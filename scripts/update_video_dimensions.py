#!/usr/bin/env python3
"""
Update video dimensions for existing media files in the database.

This script scans all video files in the metadata database and populates
the width/height fields using ffprobe.
"""

import json
import subprocess
from pathlib import Path

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from romfarmer.metadata.database import MediaFile, MetadataDatabase

console = Console()


def get_video_dimensions(video_path: Path) -> tuple[int | None, int | None]:
    """Get video dimensions using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_streams",
                "-select_streams",
                "v:0",
                str(video_path),
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            if "streams" in data and len(data["streams"]) > 0:
                stream = data["streams"][0]
                width = stream.get("width")
                height = stream.get("height")
                if width and height:
                    return width, height
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Error processing video: {e}")

    return None, None


def main():
    """Update video dimensions in database."""
    db_path = Path("metadata/database/romfarmer.db")

    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database not found: {db_path}")
        return

    console.print("\n[bold cyan]Updating Video Dimensions[/bold cyan]\n")

    db = MetadataDatabase(db_path)

    with db.get_session() as session:
        # Get all video files
        videos = session.query(MediaFile).filter(MediaFile.media_type == "video").all()

        console.print(f"Found {len(videos):,} video files")

        # Count how many need updating
        needs_update = sum(1 for v in videos if v.width is None or v.height is None)
        console.print(f"Videos needing dimensions: {needs_update:,}\n")

        if needs_update == 0:
            console.print("[green]✓ All videos already have dimensions![/green]")
            return

        updated = 0
        errors = 0
        skipped = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Processing videos...", total=needs_update)

            for video in videos:
                # Skip if already has dimensions
                if video.width is not None and video.height is not None:
                    skipped += 1
                    continue

                video_path = Path(video.file_path)

                if not video_path.exists():
                    errors += 1
                    progress.advance(task)
                    continue

                width, height = get_video_dimensions(video_path)

                if width and height:
                    video.width = width
                    video.height = height
                    updated += 1
                else:
                    errors += 1

                progress.advance(task)

                # Commit every 100 updates
                if updated % 100 == 0:
                    session.commit()

        # Final commit
        session.commit()

    console.print("\n[bold]Results:[/bold]")
    console.print(f"  Updated: {updated:,}")
    console.print(f"  Skipped (already had dimensions): {skipped:,}")
    console.print(f"  Errors: {errors:,}")

    if updated > 0:
        console.print(f"\n[green]✓ Successfully updated {updated:,} video dimensions![/green]")

    # Show resolution distribution
    console.print("\n[bold]Resolution Distribution:[/bold]")
    with db.get_session() as session:
        from sqlalchemy import func

        results = (
            session.query(
                MediaFile.width, MediaFile.height, func.count(MediaFile.id).label("count")
            )
            .filter(
                MediaFile.media_type == "video",
                MediaFile.width.isnot(None),
                MediaFile.height.isnot(None),
            )
            .group_by(MediaFile.width, MediaFile.height)
            .order_by(func.count(MediaFile.id).desc())
            .limit(10)
            .all()
        )

        console.print("\n[cyan]Top 10 Resolutions:[/cyan]")
        for width, height, count in results:
            console.print(f"  {width}x{height}: {count:,} videos")


if __name__ == "__main__":
    main()
