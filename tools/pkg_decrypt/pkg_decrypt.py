#!/usr/bin/env python3
"""
PS3/PSP PKG Decrypter and Extractor

Based on Mathieulh's PS3 PSP PKG Decrypter Extractor v.1.0.0.0
Ported to Python for Linux compatibility.

Original C# source: https://github.com/Mathieulh/PS3-PSP-PKG-Decrypter-Extractor
License: Free to use and modify (with author's blessing)
"""

import struct
import os
from pathlib import Path
from typing import Optional, Tuple
from Crypto.Cipher import AES


class PKGDecrypter:
    """Decrypt and extract PS3/PSP PKG files."""
    
    # AES keys from original source
    PSP_AES_KEY = bytes([
        0x07, 0xF2, 0xC6, 0x82, 0x90, 0xB5, 0x0D, 0x2C,
        0x33, 0x81, 0x8D, 0x70, 0x9B, 0x60, 0xE6, 0x2B
    ])
    
    PS3_AES_KEY = bytes([
        0x2E, 0x7B, 0x71, 0xD7, 0xC9, 0xC9, 0xA1, 0x4E,
        0xA3, 0x22, 0x1F, 0x18, 0x88, 0x28, 0xB8, 0xF8
    ])
    
    def __init__(self, pkg_file: Path, rap_key: Optional[str] = None):
        """Initialize PKG decrypter.
        
        Args:
            pkg_file: Path to PKG file
            rap_key: RAP key (hex string) - not needed for decryption, kept for compatibility
        """
        self.pkg_file = Path(pkg_file)
        self.rap_key = rap_key
        self.aes_key = None
        self.pkg_file_key = None
        self.encrypted_start_offset = 0
        
    def _increment_array(self, arr: bytearray, index: int):
        """Increment byte array as a big-endian counter.
        
        Args:
            arr: Byte array to increment (modified in place)
            index: Index to increment from
        """
        if index < 0:
            return
        
        arr[index] = (arr[index] + 1) & 0xFF  # Wrap to 0-255
        if arr[index] == 0:
            self._increment_array(arr, index - 1)
    
    def _xor_decrypt(self, data: bytes, key: bytes) -> bytes:
        """XOR decrypt data with key.
        
        Args:
            data: Encrypted data
            key: XOR key
            
        Returns:
            Decrypted data
        """
        return bytes(a ^ b for a, b in zip(data, key))
    
    def _aes_encrypt(self, data: bytes, key: bytes) -> bytes:
        """AES encrypt in ECB mode.
        
        Args:
            data: Data to encrypt
            key: AES key
            
        Returns:
            Encrypted data
        """
        cipher = AES.new(key, AES.MODE_ECB)
        return cipher.encrypt(data)
    
    def decrypt_pkg(self, output_path: Optional[Path] = None) -> Path:
        """Decrypt PKG file.
        
        Args:
            output_path: Output file path (default: input + .dec)
            
        Returns:
            Path to decrypted file
            
        Raises:
            ValueError: If PKG file is invalid
        """
        if output_path is None:
            output_path = self.pkg_file.with_suffix(self.pkg_file.suffix + '.dec')
        
        output_path = Path(output_path)
        
        with open(self.pkg_file, 'rb') as f:
            # Check PKG magic
            magic = f.read(4)
            if magic != b'\x7fPKG':
                raise ValueError("Not a valid PKG file (invalid magic)")
            
            # Check if retail (finalized) PKG
            finalized = struct.unpack('>B', f.read(1))[0]
            if finalized != 0x80:
                raise ValueError("Debug PKG files not supported (retail only)")
            
            # Skip 2 bytes
            f.read(2)
            
            # Get PKG type (PS3=0x01, PSP=0x02)
            pkg_type = struct.unpack('>B', f.read(1))[0]
            if pkg_type == 0x01:
                self.aes_key = self.PS3_AES_KEY
            elif pkg_type == 0x02:
                self.aes_key = self.PSP_AES_KEY
            else:
                raise ValueError(f"Invalid PKG type: {pkg_type:#x} (expected PS3=0x01 or PSP=0x02)")
            
            # Get encrypted file start offset (at 0x24)
            f.seek(0x24)
            self.encrypted_start_offset = struct.unpack('>I', f.read(4))[0]
            
            # Get encrypted file length (at 0x2C)
            f.seek(0x2C)
            encrypted_length = struct.unpack('>I', f.read(4))[0]
            
            # Get PKG file key (at 0x70)
            f.seek(0x70)
            self.pkg_file_key = bytearray(f.read(16))
            
            # Generate XOR key by encrypting file key with global AES key
            xor_key = self._aes_encrypt(bytes(self.pkg_file_key), self.aes_key)
            
            # Calculate chunks
            chunk_size = 16 * 65536  # Process in 1MB chunks
            
            # Seek to encrypted data start
            f.seek(self.encrypted_start_offset)
            
            # Decrypt and write
            with open(output_path, 'wb') as out:
                inc_key = bytearray(self.pkg_file_key)
                bytes_remaining = encrypted_length
                
                while bytes_remaining > 0:
                    # Read chunk
                    read_size = min(chunk_size, bytes_remaining)
                    encrypted_data = f.read(read_size)
                    
                    if not encrypted_data:
                        break
                    
                    # Generate consecutive XOR keys for this chunk
                    xor_key_consec = bytearray()
                    for _ in range(0, len(encrypted_data), 16):
                        xor_key_consec.extend(self._aes_encrypt(bytes(inc_key), self.aes_key))
                        self._increment_array(inc_key, 15)
                    
                    # XOR decrypt
                    decrypted_data = self._xor_decrypt(encrypted_data, xor_key_consec[:len(encrypted_data)])
                    
                    # Write decrypted data
                    out.write(decrypted_data)
                    
                    bytes_remaining -= len(encrypted_data)
        
        return output_path
    
    def extract_pkg(self, output_dir: Optional[Path] = None, verbose: bool = False) -> Path:
        """Decrypt and extract PKG file.
        
        Args:
            output_dir: Output directory (default: input + .EXT)
            verbose: Print extraction progress
            
        Returns:
            Path to extraction directory
        """
        # Decrypt PKG first
        if verbose:
            print(f"Decrypting PKG: {self.pkg_file.name}")
        
        decrypted_file = self.decrypt_pkg()
        
        if output_dir is None:
            output_dir = self.pkg_file.with_suffix(self.pkg_file.suffix + '.EXT')
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if verbose:
            print(f"Extracting to: {output_dir}")
        
        # Extract files from decrypted PKG
        with open(decrypted_file, 'rb') as f:
            # Read file table header
            first_name_offset = struct.unpack('>I', f.read(4))[0]
            file_count = first_name_offset // 32
            
            f.seek(12)
            first_file_offset = struct.unpack('>I', f.read(4))[0]
            
            # Read entire file table
            f.seek(0)
            file_table = f.read(first_file_offset)
            
            if verbose:
                print(f"Extracting {file_count} files...")
            
            # Process each file entry
            # Table format (32 bytes per entry):
            # 0-3: name offset, 4-7: name size, 8-11: NULL
            # 12-15: file offset, 16-19: NULL, 20-23: file size
            # 24: content type, 25-26: ?, 27: file type, 28-31: NULL
            
            for i in range(file_count):
                offset_in_table = i * 32
                
                # Parse entry
                name_offset = struct.unpack('>I', file_table[offset_in_table:offset_in_table+4])[0]
                name_size = struct.unpack('>I', file_table[offset_in_table+4:offset_in_table+8])[0]
                file_offset = struct.unpack('>I', file_table[offset_in_table+12:offset_in_table+16])[0]
                file_size = struct.unpack('>I', file_table[offset_in_table+20:offset_in_table+24])[0]
                content_type = file_table[offset_in_table+24]
                file_type = file_table[offset_in_table+27]
                
                # Extract filename
                name_bytes = file_table[name_offset:name_offset+name_size]
                filename = name_bytes.rstrip(b'\x00').decode('utf-8', errors='replace')
                
                # Check if directory
                is_dir = (file_type == 0x04 and file_size == 0)
                
                # Content type 0x90 = PSP (filename already decrypted)
                # Content type 0x80 or 0x00 = PS3 (filename needs decryption)
                if content_type != 0x90:
                    # PS3 - decrypt filename
                    filename_encrypted = self._decrypt_ps3_data(
                        name_size, name_offset, 
                        self.encrypted_start_offset,
                        self.PS3_AES_KEY, self.pkg_file
                    )
                    filename = filename_encrypted[:name_size].rstrip(b'\x00').decode('utf-8', errors='replace')
                
                # Create file/directory path
                file_path = output_dir / filename.replace('/', os.sep)
                
                if is_dir:
                    # Create directory
                    file_path.mkdir(parents=True, exist_ok=True)
                    if verbose:
                        print(f"  [{i+1}/{file_count}] DIR:  {filename}")
                else:
                    # Ensure parent directory exists
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Extract file
                    f.seek(file_offset)
                    file_data = f.read(file_size)
                    
                    # For PS3 files, decrypt content
                    if content_type != 0x90:
                        file_data = self._decrypt_ps3_data(
                            file_size, file_offset,
                            self.encrypted_start_offset,
                            self.PS3_AES_KEY, self.pkg_file
                        )[:file_size]
                    
                    # Write file
                    with open(file_path, 'wb') as out:
                        out.write(file_data)
                    
                    if verbose:
                        size_kb = file_size / 1024
                        print(f"  [{i+1}/{file_count}] FILE: {filename} ({size_kb:.1f} KB)")
        
        # Clean up decrypted temp file
        decrypted_file.unlink()
        
        if verbose:
            print(f"\nExtraction complete: {output_dir}")
        
        return output_dir
    
    def _decrypt_ps3_data(self, data_size: int, data_offset: int, 
                          pkg_encrypted_start: int, aes_key: bytes,
                          pkg_file: Path) -> bytes:
        """Decrypt PS3-specific data (filenames, file content).
        
        Args:
            data_size: Size of data to decrypt
            data_offset: Offset of data relative to decrypted file
            pkg_encrypted_start: Start offset of encrypted section in original PKG
            aes_key: AES key to use
            pkg_file: Original (encrypted) PKG file path
            
        Returns:
            Decrypted data
        """
        # Pad size to 16-byte boundary
        padded_size = ((data_size + 15) // 16) * 16
        
        # Calculate position in encrypted PKG
        encrypted_offset = pkg_encrypted_start + data_offset
        
        # Read encrypted data from original PKG
        with open(pkg_file, 'rb') as f:
            f.seek(encrypted_offset)
            encrypted_data = f.read(padded_size)
        
        # Generate incremented key for this offset
        inc_key = bytearray(self.pkg_file_key)
        
        # Increment key to match position
        for _ in range(0, data_offset, 16):
            self._increment_array(inc_key, 15)
        
        # Generate XOR keys for decryption
        xor_key_consec = bytearray()
        for _ in range(0, padded_size, 16):
            xor_key_consec.extend(self._aes_encrypt(bytes(inc_key), aes_key))
            self._increment_array(inc_key, 15)
        
        # XOR decrypt
        decrypted = self._xor_decrypt(encrypted_data, xor_key_consec)
        
        return decrypted


def main():
    """Command-line interface for PKG decryption."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Decrypt and extract PS3/PSP PKG files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Extract PKG file
  %(prog)s game.pkg
  
  # Extract to specific directory
  %(prog)s game.pkg -o /output/dir
  
  # Verbose output
  %(prog)s game.pkg -v
  
Based on Mathieulh's PS3 PSP PKG Decrypter Extractor
Python port for Linux by ROM Farmer project
        '''
    )
    
    parser.add_argument('pkg_file', help='PKG file to decrypt')
    parser.add_argument('-o', '--output', help='Output directory')
    parser.add_argument('-r', '--rap', help='RAP key (not needed for decryption, kept for compatibility)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--decrypt-only', action='store_true', help='Only decrypt, do not extract')
    
    args = parser.parse_args()
    
    pkg_file = Path(args.pkg_file)
    if not pkg_file.exists():
        print(f"Error: PKG file not found: {pkg_file}")
        return 1
    
    try:
        decrypter = PKGDecrypter(pkg_file, args.rap)
        
        if args.decrypt_only:
            output_file = decrypter.decrypt_pkg()
            if args.verbose:
                print(f"Decrypted: {output_file}")
        else:
            output_dir = Path(args.output) if args.output else None
            extracted_dir = decrypter.extract_pkg(output_dir, args.verbose)
            
            if not args.verbose:
                print(f"Extracted to: {extracted_dir}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
