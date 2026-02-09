#!/usr/bin/env python3
"""
zRIF to RIF converter
Converts base64-encoded zRIF strings to binary .rif license files

Based on the zRIF format used by NoPayStation and Vita3K
"""

import base64
import zlib
from pathlib import Path


def zrif_to_rif(zrif_string: str) -> bytes:
    """
    Convert a zRIF string to RIF binary data
    
    The zRIF format is:
    - Base64 encoded
    - DEFLATE compressed RIF data
    
    Args:
        zrif_string: The base64-encoded zRIF string
        
    Returns:
        152 bytes of RIF data
    """
    # Step 1: Decode base64
    try:
        compressed_data = base64.b64decode(zrif_string.strip())
    except Exception as e:
        raise ValueError(f"Invalid base64 zRIF string: {e}")
    
    # Step 2: Decompress using DEFLATE (raw deflate, no zlib header)
    try:
        rif_data = zlib.decompress(compressed_data, -zlib.MAX_WBITS)
    except Exception as e:
        raise ValueError(f"Failed to decompress zRIF: {e}")
    
    # Step 3: Verify size
    if len(rif_data) != 152:
        raise ValueError(f"Invalid RIF size: {len(rif_data)} bytes (expected 152)")
    
    return rif_data


def create_rif_from_zrif_file(zrif_file: Path, output_file: Path = None) -> Path:
    """
    Create a .rif file from a .zrif file
    
    Args:
        zrif_file: Path to .zrif file containing the zRIF string
        output_file: Optional output path (defaults to same location as .rif)
        
    Returns:
        Path to created .rif file
    """
    # Read zRIF string
    with open(zrif_file, 'r') as f:
        zrif_string = f.read().strip()
    
    # Convert to RIF
    rif_data = zrif_to_rif(zrif_string)
    
    # Determine output path
    if output_file is None:
        output_file = zrif_file.with_suffix('.rif')
    
    # Write RIF file
    with open(output_file, 'wb') as f:
        f.write(rif_data)
    
    return output_file


def batch_convert(root_dir: Path, verbose: bool = False) -> dict:
    """
    Convert all .zrif files to .rif files in a directory tree
    
    Args:
        root_dir: Root directory to search
        verbose: Print progress messages
        
    Returns:
        Statistics dict
    """
    stats = {
        'total_found': 0,
        'converted': 0,
        'already_exists': 0,
        'failed': 0,
        'errors': []
    }
    
    # Find all .zrif files
    for zrif_file in root_dir.rglob('*.zrif'):
        stats['total_found'] += 1
        rif_file = zrif_file.with_suffix('.rif')
        
        # Skip if .rif already exists
        if rif_file.exists():
            stats['already_exists'] += 1
            if verbose:
                print(f"[SKIP] {rif_file.relative_to(root_dir)} - already exists")
            continue
        
        # Convert
        try:
            create_rif_from_zrif_file(zrif_file, rif_file)
            stats['converted'] += 1
            if verbose:
                print(f"[OK] {rif_file.relative_to(root_dir)}")
        except Exception as e:
            stats['failed'] += 1
            error_msg = f"{zrif_file.relative_to(root_dir)}: {str(e)}"
            stats['errors'].append(error_msg)
            if verbose:
                print(f"[FAIL] {error_msg}")
    
    return stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert zRIF files to binary RIF license files'
    )
    parser.add_argument(
        'input',
        type=Path,
        help='Path to .zrif file or directory containing .zrif files'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output .rif file (single file mode only)'
    )
    parser.add_argument(
        '-b', '--batch',
        action='store_true',
        help='Process all .zrif files in directory tree'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    if args.batch:
        print(f"Scanning: {args.input}")
        print("=" * 60)
        
        stats = batch_convert(args.input, verbose=args.verbose)
        
        print("\n" + "=" * 60)
        print("BATCH CONVERSION COMPLETE")
        print("=" * 60)
        print(f"Total .zrif files found: {stats['total_found']}")
        print(f"Converted to .rif: {stats['converted']}")
        print(f"Already existed: {stats['already_exists']}")
        print(f"Failed: {stats['failed']}")
        
        if stats['errors']:
            print("\nErrors:")
            for error in stats['errors']:
                print(f"  - {error}")
    else:
        # Single file mode
        rif_file = create_rif_from_zrif_file(args.input, args.output)
        print(f"Created: {rif_file}")
        print(f"Size: {rif_file.stat().st_size} bytes")


if __name__ == '__main__':
    main()
