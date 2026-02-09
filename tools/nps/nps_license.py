#!/usr/bin/env python3
"""
NoPayStation License File Generator
Converts zRIF strings to work.bin files for Vita3K emulator

According to Vita3K source code, work.bin is simply the zRIF string saved as-is.
Vita3K handles the decryption internally using its own zrif2rif library.
"""

from pathlib import Path
from typing import Optional


class LicenseGenerator:
    """Generates work.bin files from zRIF strings"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def zrif_to_work_bin(self, zrif: str) -> str:
        """
        Convert zRIF string to work.bin content
        
        For Vita3K, work.bin is just the zRIF string stored as plain text.
        Vita3K's internal zrif2rif library handles the actual decryption.
        
        Args:
            zrif: Base64-encoded zRIF string
            
        Returns:
            The zRIF string (unchanged)
        """
        # work.bin for Vita3K is literally just the zRIF string
        return zrif.strip()
    
    def create_work_bin(self, zrif_file: Path, output_dir: Optional[Path] = None) -> Path:
        """
        Create work.bin from a .zrif file
        
        Args:
            zrif_file: Path to .zrif file
            output_dir: Optional output directory (defaults to zrif_file's directory)
            
        Returns:
            Path to created work.bin file
        """
        if not zrif_file.exists():
            raise FileNotFoundError(f"zRIF file not found: {zrif_file}")
        
        # Read zRIF content
        with open(zrif_file, 'r') as f:
            zrif_content = f.read().strip()
        
        if self.verbose:
            print(f"Processing: {zrif_file.name}")
            print(f"  zRIF: {zrif_content[:20]}...")
        
        # Convert to work.bin format (just the zRIF string)
        work_bin_content = self.zrif_to_work_bin(zrif_content)
        
        # Determine output path
        if output_dir is None:
            output_dir = zrif_file.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        work_bin_path = output_dir / 'work.bin'
        
        # Write work.bin
        with open(work_bin_path, 'w') as f:
            f.write(work_bin_content)
        
        if self.verbose:
            print(f"  Created: {work_bin_path} ({len(work_bin_content)} chars)")
        
        return work_bin_path
    
    def batch_create_work_bins(self, root_dir: Path, dry_run: bool = False) -> dict:
        """
        Create work.bin files for all games in a directory tree
        
        Args:
            root_dir: Root directory containing game folders
            dry_run: If True, don't create files, just report what would be done
            
        Returns:
            Statistics dict with counts
        """
        root_dir = Path(root_dir)
        
        stats = {
            'total_games': 0,
            'created': 0,
            'already_exists': 0,
            'failed': 0,
            'errors': []
        }
        
        # Find all game directories (contain base/ folder with .zrif file)
        for game_dir in sorted(root_dir.glob('*-*')):
            if not game_dir.is_dir():
                continue
            
            stats['total_games'] += 1
            
            # Look for base game zRIF
            base_dir = game_dir / 'base'
            if not base_dir.exists():
                continue
            
            zrif_files = list(base_dir.glob('*.zrif'))
            if not zrif_files:
                continue
            
            zrif_file = zrif_files[0]  # Use first zRIF found
            work_bin_path = base_dir / 'work.bin'
            
            # Check if already exists
            if work_bin_path.exists():
                stats['already_exists'] += 1
                if self.verbose:
                    print(f"[SKIP] {game_dir.name} - work.bin already exists")
                continue
            
            if dry_run:
                print(f"[DRY-RUN] Would create: {work_bin_path}")
                stats['created'] += 1
                continue
            
            # Create work.bin
            try:
                self.create_work_bin(zrif_file, output_dir=base_dir)
                stats['created'] += 1
                print(f"[OK] {game_dir.name}")
            except Exception as e:
                stats['failed'] += 1
                error_msg = f"{game_dir.name}: {str(e)}"
                stats['errors'].append(error_msg)
                print(f"[FAIL] {error_msg}")
        
        return stats


def main():
    """CLI interface for license generation"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate work.bin license files from zRIF strings'
    )
    parser.add_argument(
        'input',
        help='Path to .zrif file or directory containing games'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output directory (defaults to same as input)'
    )
    parser.add_argument(
        '-b', '--batch',
        action='store_true',
        help='Process all games in directory tree'
    )
    parser.add_argument(
        '-d', '--dry-run',
        action='store_true',
        help='Show what would be done without creating files'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    generator = LicenseGenerator(verbose=args.verbose)
    input_path = Path(args.input)
    
    if args.batch:
        # Batch mode - process directory tree
        print(f"Scanning: {input_path}")
        print("="*60)
        
        stats = generator.batch_create_work_bins(
            input_path, 
            dry_run=args.dry_run
        )
        
        print("\n" + "="*60)
        print("BATCH PROCESSING COMPLETE")
        print("="*60)
        print(f"Total games scanned: {stats['total_games']}")
        print(f"work.bin files created: {stats['created']}")
        print(f"Already existed: {stats['already_exists']}")
        print(f"Failed: {stats['failed']}")
        
        if stats['errors']:
            print("\nErrors:")
            for error in stats['errors']:
                print(f"  - {error}")
    else:
        # Single file mode
        output_dir = Path(args.output) if args.output else None
        
        if args.dry_run:
            print(f"[DRY-RUN] Would create work.bin from: {input_path}")
        else:
            work_bin_path = generator.create_work_bin(input_path, output_dir)
            print(f"Created: {work_bin_path}")


if __name__ == '__main__':
    main()
