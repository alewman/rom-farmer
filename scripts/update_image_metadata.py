#!/usr/bin/env python3
"""
Update image metadata (color mode, transparency) for existing images.

This script scans all image files in the metadata database and populates
the image-specific metadata fields.
"""

from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from romfarmer.metadata.database import MetadataDatabase, MediaFile

console = Console()


def get_image_metadata(image_path: Path) -> dict:
    """Get comprehensive image metadata."""
    try:
        from PIL import Image

        with Image.open(image_path) as img:
            has_transparency = img.mode in ('RGBA', 'LA', 'PA', 'P')
            # For P mode, check if there's actually transparency in the palette
            if img.mode == 'P' and 'transparency' not in img.info:
                has_transparency = False
            
            return {
                'mode': img.mode,
                'has_transparency': has_transparency,
            }
    except Exception as e:
        return {
            'mode': None,
            'has_transparency': None,
        }


def main():
    """Update image metadata in database."""
    db_path = Path("metadata/database/romfarmer.db")
    
    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database not found: {db_path}")
        return
    
    console.print("\n[bold cyan]Updating Image Metadata[/bold cyan]\n")
    
    db = MetadataDatabase(db_path)
    
    # Image media types
    image_types = ['image', 'boxart', 'screenshot', 'cartridge', 'wheel', 'marquee', 'mix']
    
    with db.get_session() as session:
        # Get all image files
        images = session.query(MediaFile).filter(
            MediaFile.media_type.in_(image_types)
        ).all()
        
        console.print(f"Found {len(images):,} image files")
        
        # Count how many need updating
        needs_update = sum(
            1 for img in images 
            if img.image_mode is None
        )
        console.print(f"Images needing metadata: {needs_update:,}\n")
        
        if needs_update == 0:
            console.print("[green]✓ All images already have metadata![/green]")
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
            task = progress.add_task("Processing images...", total=needs_update)
            
            for image in images:
                # Skip if already has metadata
                if image.image_mode is not None and image.has_transparency is not None:
                    skipped += 1
                    continue
                
                image_path = Path(image.file_path)
                
                if not image_path.exists():
                    errors += 1
                    progress.advance(task)
                    continue
                
                metadata = get_image_metadata(image_path)
                
                if metadata['mode']:
                    image.image_mode = metadata['mode']
                    image.has_transparency = metadata['has_transparency']
                    updated += 1
                else:
                    errors += 1
                
                progress.advance(task)
                
                # Commit every 1000 updates
                if updated % 1000 == 0:
                    session.commit()
        
        # Final commit
        session.commit()
    
    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"  Updated: {updated:,}")
    console.print(f"  Skipped (already had metadata): {skipped:,}")
    console.print(f"  Errors: {errors:,}")
    
    if updated > 0:
        console.print(f"\n[green]✓ Successfully updated {updated:,} images with metadata![/green]")
    
    # Show mode distribution
    console.print("\n[bold]Color Mode Distribution:[/bold]")
    with db.get_session() as session:
        from sqlalchemy import func
        
        results = session.query(
            MediaFile.image_mode,
            func.count(MediaFile.id).label('count')
        ).filter(
            MediaFile.media_type.in_(image_types),
            MediaFile.image_mode.isnot(None)
        ).group_by(
            MediaFile.image_mode
        ).order_by(
            func.count(MediaFile.id).desc()
        ).all()
        
        console.print("\n[cyan]Image Modes:[/cyan]")
        for mode, count in results:
            console.print(f"  {mode}: {count:,} images")
    
    # Show transparency statistics
    console.print("\n[bold]Transparency Statistics:[/bold]")
    with db.get_session() as session:
        from sqlalchemy import func
        
        total = session.query(func.count(MediaFile.id)).filter(
            MediaFile.media_type.in_(image_types),
            MediaFile.has_transparency.isnot(None)
        ).scalar()
        
        with_transparency = session.query(func.count(MediaFile.id)).filter(
            MediaFile.media_type.in_(image_types),
            MediaFile.has_transparency == True
        ).scalar()
        
        pct = (with_transparency / total * 100) if total > 0 else 0
        
        console.print(f"\n[cyan]Transparency:[/cyan]")
        console.print(f"  With transparency: {with_transparency:,} ({pct:.1f}%)")
        console.print(f"  Without transparency: {total - with_transparency:,} ({100-pct:.1f}%)")


if __name__ == "__main__":
    main()
