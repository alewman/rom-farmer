================================================================================
  {GAME_TITLE} - HYBRID BUILD
  Built: {BUILD_DATE}
================================================================================

This is a complete, self-contained PS3 game package that works on both:
  ✓ Real PS3 hardware (Jailbroken/CFW)
  ✓ RPCS3 emulator

================================================================================
  WHAT'S INCLUDED
================================================================================

📀 BASE GAME:
   - Full game disc image in .ps3 folder format
   - Version: {APP_VER}

🔄 UPDATES:
   - Official Sony PSN updates baked into the game
   - Game executable and files are already updated
   - No separate update installation needed

📦 DLC (DOWNLOADABLE CONTENT):
   - {DLC_COUNT} DLC packages included
   - Major campaign DLC extracted to disc (for real PS3)
   - ALL DLC PKG files in _PKG/ folder (for RPCS3 + real PS3)

================================================================================
  FOLDER STRUCTURE
================================================================================

{GAME_FOLDER}/
├── PS3_DISC.SFB           ← Disc metadata
├── PS3_GAME/              ← Main game files (updated to v{APP_VER})
│   ├── PARAM.SFO          ← Game parameters
│   ├── ICON0.PNG          ← Game icon
│   ├── PS3LOGO.DAT        ← Boot logo
│   └── USRDIR/            ← Game data
│       ├── EBOOT.BIN      ← Game executable (updated)
│       └── DLC/           ← Major campaign DLC (for real PS3)
│           ├── ORCHID/    ← Captain Scarlett
│           ├── IRIS/      ← Mr. Torgue
│           ├── SAGE/      ← Sir Hammerlock
│           └── ASTER/     ← Tiny Tina
├── PS3_UPDATE/            ← May be present (update metadata)
├── _PKG/                  ← PKG files for manual installation
│   ├── *.pkg              ← {PKG_COUNT} DLC PKG files (see list below)
│   └── RAPS/              ← License activation files
│       └── *.rap          ← {RAP_COUNT} RAP files (one per DLC)
└── README.txt             ← This file

================================================================================
  HOW TO USE - REAL PS3 (JAILBROKEN/CFW)
================================================================================

METHOD 1: Play from Disc (Recommended for Major Campaigns)
-----------------------------------------------------------
1. Copy entire folder to: /dev_hdd0/GAMES/ or USB drive
2. Launch game from XMB (Multiman/Webman)
3. Major campaign DLC will load automatically from disc
   ✓ Captain Scarlett, Mr. Torgue, Sir Hammerlock, Tiny Tina
4. Other DLC (characters, skins) require PKG installation (see Method 2)

METHOD 2: Install Additional DLC from PKG Files
------------------------------------------------
For character packs, skins, and other DLC not on disc:

1. Copy PKG files from _PKG/ folder to: /dev_hdd0/packages/
   
2. Copy RAP files from _PKG/RAPS/ to: /dev_hdd0/exdata/
   (RAP files activate/license the DLC)

3. Install PKG files:
   - Open Package Manager on PS3 (in XMB under Game)
   - Select PKG file
   - Press X to install

4. Launch game - DLC should now be available

NOTES:
- You can install ALL PKG files if you prefer HDD installation over disc
- RAP files MUST be in /dev_hdd0/exdata/ or DLC won't activate
- Some CFW may auto-detect RAP files from packages folder

================================================================================
  HOW TO USE - RPCS3 EMULATOR
================================================================================

STEP 1: Install the Base Game
------------------------------
1. In RPCS3: File → Boot Game
2. Select this folder (the .ps3 folder)
3. Game will boot with v{APP_VER} update already applied

STEP 2: Install DLC (Required - Disc DLC Not Recognized by RPCS3)
------------------------------------------------------------------
RPCS3 does not load DLC from disc structure. You must manually install PKGs.

1. Open RPCS3 menu: File → Install Packages/Raps

2. Install RAP files first:
   - Navigate to _PKG/RAPS/ folder
   - Select ALL .rap files
   - Click Open (installs licenses)

3. Install PKG files:
   - Navigate to _PKG/ folder
   - Select desired .pkg files (or all of them)
   - Click Open (installs DLC)
   - This may take several minutes depending on size

4. Launch game - DLC should now be available in-game

NOTES:
- You can install DLC selectively (see PKG list below)
- RAP files are small license files that activate DLC
- PKG files contain the actual DLC content
- Install order doesn't matter, but RAPs before PKGs is recommended

================================================================================
  DLC PKG FILES INCLUDED
================================================================================

The _PKG/ folder contains {PKG_COUNT} DLC packages with user-friendly names:

{PKG_LIST}

All PKG filenames are descriptive - you can see what each DLC is before
installing it. No cryptic codes or IDs!

================================================================================
  TECHNICAL DETAILS
================================================================================

Title ID:       {TITLE_ID}
Region:         {REGION}
Game Version:   {APP_VER}
Build Type:     HYBRID (Real PS3 + RPCS3 compatible)
Total Size:     {TOTAL_SIZE}

Build Strategy:
- Base game: {BASE_SIZE}
- Updates: Baked into PS3_GAME/ (not separate)
- Disc DLC: {DISC_DLC_SIZE} (major campaigns extracted to USRDIR/DLC/)
- PKG files: {PKG_SIZE} (all DLC for manual installation)
- RAP files: {RAP_SIZE} (license activation)

Why "HYBRID"?
-------------
This build works on BOTH real PS3 and RPCS3:
- Real PS3: Loads major campaign DLC from disc automatically
- RPCS3: Requires PKG installation (disc DLC not recognized)
- Both: Can install additional DLC from _PKG/ folder as needed

================================================================================
  TROUBLESHOOTING
================================================================================

Q: DLC doesn't show up on real PS3
A: 1) Check that RAP files are in /dev_hdd0/exdata/
   2) Reinstall PKG if needed
   3) Try rebooting PS3

Q: DLC doesn't show up in RPCS3
A: 1) Make sure you installed RAP files first
   2) Verify PKG installation completed (check RPCS3 log)
   3) Restart RPCS3

Q: "Corrupted data" error when installing PKG
A: 1) Re-copy PKG file (may be damaged)
   2) Check available HDD space
   3) Try different PKG file

Q: Game crashes after installing DLC
A: 1) Verify game update is v{APP_VER}
   2) Check if DLC requires newer game version
   3) Try installing DLC one at a time to isolate issue

Q: How do I know which DLC I want to install?
A: Check the PKG filenames - they're descriptive!
   Example: "Borderlands 2 - Mechromancer Pack.pkg"
   Install campaigns first, then characters, then cosmetics

================================================================================
  CREDITS
================================================================================

Built with: rom-farmer-python
PKG Source: NoPayStation database
Updates:    Official Sony PSN servers
Build Type: HYBRID (Disc + PKG)

This package is for archival and compatibility purposes.
Please support the developers by purchasing games legally.

================================================================================
