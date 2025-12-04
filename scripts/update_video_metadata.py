#!/usr/bin/env python3
"""
Update video metadata (codec, bitrate, FPS, duration) for existing videos.

This script scans all video files in the metadata database and populates
the video-specific metadata fields.
"""

import subprocess
import json
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from romfarmer.metadata.database import MetadataDatabase, MediaFile

console = Console()


def get_video_metadata(video_path: Path) -> dict:
    """Get comprehensive video metadata using ffprobe."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', 
             '-show_streams', '-select_streams', 'v:0', str(video_path)],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'streams' in data and len(data['streams']) > 0:
                stream = data['streams'][0]
                return {
                    'codec': stream.get('codec_name'),
                    'bitrate': int(stream['bit_rate']) if stream.get('bit_rate') else None,
                    'fps': stream.get('r_frame_rate'),
                    'duration': float(stream['duration']) if stream.get('duration') else None,
                }
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Error processing video: {e}")
    
    return {
        'codec': None,
        'bitrate': None,
        'fps': None,
        'duration': None,
    }


def main():
    """Update video metadata in database."""
    db_path = Path("metadata/database/romfarmer.db")
    
    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database not found: {db_path}")
        return
    
    console.print("\n[bold cyan]Updating Video Metadata[/bold cyan]\n")
    
    db = MetadataDatabase(db_path)
    
    with db.get_session() as session:
        # Get all video files
        videos = session.query(MediaFile).filter(
            MediaFile.media_type == 'video'
        ).all()
        
        console.print(f"Found {len(videos):,} video files")
        
        # Count how many need updating
        needs_update = sum(
            1 for v in videos 
            if v.video_codec is None or v.video_bitrate is None
        )
        console.print(f"Videos needing metadata: {needs_update:,}\n")
        
        if needs_update == 0:
            console.print("[green]✓ All videos already have metadata![/green]")
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
                # Skip if already has full metadata
                if (video.video_codec is not None and 
                    video.video_bitrate is not None and 
                    video.video_fps is not None and 
                    video.video_duration is not None):
                    skipped += 1
                    continue
                
                video_path = Path(video.file_path)
                
                if not video_path.exists():
                    errors += 1
                    progress.advance(task)
                    continue
                
                metadata = get_video_metadata(video_path)
                
                if metadata['codec']:
                    video.video_codec = metadata['codec']
                    video.video_bitrate = metadata['bitrate']
                    video.video_fps = metadata['fps']
                    video.video_duration = metadata['duration']
                    updated += 1
                else:
                    errors += 1
                
                progress.advance(task)
                
                # Commit every 100 updates
                if updated % 100 == 0:
                    session.commit()
        
        # Final commit
        session.commit()
    
    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  Updated: {updated:,}")
    console.print(f"  Skipped (already had metadata): {skipped:,}")
    console.print(f"  Errors: {errors:,}")
    
    if updated > 0:
        console.print(f"\n[green]✓ Successfully updated {updated:,} videos with metadata![/green]")
    
    # Show codec distribution
    console.print("\n[bold]Codec Distribution:[/bold]")
    with db.get_session() as session:
        from sqlalchemy import func
        
        results = session.query(
            MediaFile.video_codec,
            func.count(MediaFile.id).label('count')
        ).filter(
            MediaFile.media_type == 'video',
            MediaFile.video_codec.isnot(None)
        ).group_by(
            MediaFile.video_codec
        ).order_by(
            func.count(MediaFile.id).desc()
        ).all()
        
        console.print("\n[cyan]Video Codecs:[/cyan]")
        for codec, count in results:
            console.print(f"  {codec}: {count:,} videos")
    
    # Show bitrate statistics
    console.print("\n[bold]Bitrate Statistics:[/bold]")
    with db.get_session() as session:
        from sqlalchemy import func
        
        stats = session.query(
            func.min(MediaFile.video_bitrate).label('min'),
            func.max(MediaFile.video_bitrate).label('max'),
            func.avg(MediaFile.video_bitrate).label('avg')
        ).filter(
            MediaFile.media_type == 'video',
            MediaFile.video_bitrate.isnot(None)
        ).first()
        
        if stats:
            console.print(f"\n[cyan]Bitrate Range:[/cyan]")
            console.print(f"  Min: {stats.min / 1_000_000:.2f} Mbps")
            console.print(f"  Max: {stats.max / 1_000_000:.2f} Mbps")
            console.print(f"  Avg: {stats.avg / 1_000_000:.2f} Mbps")


if __name__ == "__main__":
    main()
