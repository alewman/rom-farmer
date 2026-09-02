#!/usr/bin/env python3
"""
Migration: Add EmulationStation metadata fields to scraped_games table.

Adds columns for:
- hidden: Games marked hidden in ES (exclude from builds)
- favorite: Games marked as favorites
- kidgame: Games marked as kid-friendly
- playcount: Number of times played
- lastplayed: Last played timestamp

Run this after updating to the latest ROM Farmer version.
"""

import sqlite3
from pathlib import Path


def migrate_database(db_path: Path):
    """Add new metadata columns to scraped_games table."""

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return False

    print(f"📦 Migrating database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='scraped_games'
    """)

    if not cursor.fetchone():
        print("⚠️  scraped_games table not found (probably fresh database)")
        conn.close()
        return True

    # Get existing columns
    cursor.execute("PRAGMA table_info(scraped_games)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    # Define new columns to add
    new_columns = {
        "hidden": "BOOLEAN DEFAULT 0",
        "favorite": "BOOLEAN DEFAULT 0",
        "kidgame": "BOOLEAN DEFAULT 0",
        "playcount": "INTEGER DEFAULT 0",
        "lastplayed": "DATETIME",
    }

    added = []
    skipped = []

    for col_name, col_def in new_columns.items():
        if col_name in existing_columns:
            skipped.append(col_name)
            continue

        try:
            cursor.execute(f"ALTER TABLE scraped_games ADD COLUMN {col_name} {col_def}")
            added.append(col_name)
            print(f"  ✓ Added column: {col_name}")
        except sqlite3.OperationalError as e:
            print(f"  ✗ Failed to add {col_name}: {e}")

    conn.commit()
    conn.close()

    # Summary
    if added:
        print(f"\n✅ Migration complete: Added {len(added)} columns")
    if skipped:
        print(f"⏭️  Skipped {len(skipped)} existing columns: {', '.join(skipped)}")

    return True


def main():
    """Run migration on default database."""

    # Find database
    possible_paths = [
        Path.cwd() / "metadata" / "database" / "romfarmer.db",
        Path(__file__).parent.parent / "metadata" / "database" / "romfarmer.db",
    ]

    db_path = None
    for path in possible_paths:
        if path.exists():
            db_path = path
            break

    if not db_path:
        print("❌ Could not find romfarmer.db")
        print("   Looked in:")
        for path in possible_paths:
            print(f"     - {path}")
        return 1

    success = migrate_database(db_path)
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
