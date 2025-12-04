#!/usr/bin/env python3
"""
Add image metadata columns to media_files table.

This migration adds:
- image_mode (VARCHAR 16) - Color mode (RGB, RGBA, L, etc.)
- has_transparency (BOOLEAN) - True if image has alpha channel
"""

import sqlite3
from pathlib import Path
from rich.console import Console

console = Console()

def main():
    db_path = Path("metadata/database/romfarmer.db")
    
    if not db_path.exists():
        console.print(f"[red]Error:[/red] Database not found: {db_path}")
        return
    
    console.print("\n[bold cyan]Adding Image Metadata Columns[/bold cyan]\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(media_files);")
    columns = {row[1] for row in cursor.fetchall()}
    
    new_columns = {
        'image_mode': 'VARCHAR(16)',
        'has_transparency': 'BOOLEAN',
    }
    
    added = []
    skipped = []
    
    for col_name, col_type in new_columns.items():
        if col_name in columns:
            skipped.append(col_name)
            console.print(f"[yellow]⊘[/yellow] Column '{col_name}' already exists")
        else:
            cursor.execute(f"ALTER TABLE media_files ADD COLUMN {col_name} {col_type};")
            added.append(col_name)
            console.print(f"[green]✓[/green] Added column '{col_name}' ({col_type})")
    
    conn.commit()
    conn.close()
    
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Added: {len(added)}")
    console.print(f"  Skipped (already exist): {len(skipped)}")
    
    if added:
        console.print(f"\n[green]✓ Migration completed successfully![/green]")
    else:
        console.print(f"\n[yellow]All columns already exist - no changes made[/yellow]")

if __name__ == "__main__":
    main()
