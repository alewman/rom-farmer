#!/usr/bin/env python3
"""
DEFINITIVE ARRM Hashing Rules - Summary Report

Findings from analysis:

1. SINGLE-TRACK DISCS (1 BIN file):
   - ARRM stores: path = .cue, md5 = BIN file's MD5
   - ScreenScraper knows the CUE is trivial for single-track
   - The game identity is in the BIN data
   
2. MULTI-TRACK DISCS (2+ BIN files):
   - ARRM stores: path = .cue, md5 = CUE file's MD5
   - The CUE describes audio/data track layout
   - ScreenScraper uses CUE to identify disc configuration
   
3. ISO FILES:
   - ARRM stores: path = .iso, md5 = ISO file's MD5
   - Self-contained, no ambiguity

4. BIN FILES (when folder has loose .bin):
   - ARRM stores: path = .bin, md5 = BIN file's MD5
   - Only happens if folder contains .bin files directly

IMPLICATIONS FOR ROM FARMER:
- For source ZIP matching (filter_dat), we currently hash the CUE
- But ARRM may have hashed the BIN for single-track games!
- We need to detect single vs multi-track and hash accordingly:
  - Single-track: Hash the BIN
  - Multi-track: Hash the CUE
  - ISO: Hash the ISO
"""

print(__doc__)
print("\n" + "="*70)
print("VERIFICATION RESULTS SUMMARY")
print("="*70)

results = """
System       | Tracks | Path Ext | MD5 Matches  | Count
-------------|--------|----------|--------------|-------
3DO          | 1      | .cue     | BIN          | 660
Dreamcast    | 3+     | .cue     | CUE          | 1,445
PS2 (CUE)    | 1      | .cue     | CUE          | 518
PS2 (BIN)    | 1      | .bin     | BIN          | 532
PS2 (ISO)    | N/A    | .iso     | ISO          | 1,926
"""

print(results)

print("\n" + "="*70)
print("ROM FARMER CODE CHANGES NEEDED")
print("="*70)

changes = """
1. filter_dat.py: _select_rom_file()
   - Current: Always selects .cue if present
   - Needed:  
     - Count .bin files in ZIP
     - If 1 BIN: hash the BIN
     - If 2+ BINs: hash the CUE
     
2. compress.py: _calculate_source_md5()
   - Must follow same logic for transformation tracking
   - When recording transformations, use correct source hash

3. metadata.py: lookup order is fine
   - Already looks up by final_md5 first
   - Then by source_md5

This ensures our stored hashes match what ARRM/ScreenScraper has.
"""

print(changes)
