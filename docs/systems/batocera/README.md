# Batocera System Documentation

This directory contains cached copies of **168 Batocera wiki system pages** for reference.

## Source

All documentation is sourced from the official Batocera Wiki:
- https://wiki.batocera.org/systems
- Uses raw DokuWiki export endpoint for accurate content

## License

Per the Batocera Wiki: Content is licensed under [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/deed.en)

## Purpose

These pages serve as the source of truth for:
- **ROM formats**: What file extensions each system accepts
- **BIOS requirements**: Required BIOS files and their MD5 hashes  
- **Folder paths**: Where ROMs should be placed in Batocera
- **Emulators**: Which emulators/cores are available
- **Special requirements**: XISO conversion, CHD compression, etc.

## Updating

To refresh documentation, run:
```bash
# Fetch ROM Farmer platforms only (41 systems)
python3 scripts/fetch_batocera_docs.py

# Fetch ALL Batocera systems (160+ systems)
python3 scripts/fetch_batocera_docs.py --all

# Fetch single system
python3 scripts/fetch_batocera_docs.py --system saturn
```

---

## ROM Farmer Supported Platforms (41)

### Cartridge Systems (No-Intro)

| System | File | Myrient |
|--------|------|---------|
| Atari 2600 | [atari2600.md](atari2600.md) | ✅ |
| Atari 5200 | [atari5200.md](atari5200.md) | ✅ |
| Atari 7800 | [atari7800.md](atari7800.md) | ✅ |
| Atari Jaguar | [atarijaguar.md](atarijaguar.md) | ✅ |
| Atari Lynx | [atarilynx.md](atarilynx.md) | ✅ |
| ColecoVision | [colecovision.md](colecovision.md) | ✅ |
| Game Boy | [gb.md](gb.md) | ✅ |
| Game Boy Advance | [gba.md](gba.md) | ✅ |
| Game Boy Color | [gbc.md](gbc.md) | ✅ |
| Game Gear | [gamegear.md](gamegear.md) | ✅ |
| Intellivision | [intellivision.md](intellivision.md) | ✅ |
| Master System | [mastersystem.md](mastersystem.md) | ✅ |
| Mega Drive / Genesis | [megadrive.md](megadrive.md) | ✅ |
| N64 | [n64.md](n64.md) | ✅ |
| NDS | [nds.md](nds.md) | ✅ |
| NES | [nes.md](nes.md) | ✅ |
| Neo Geo Pocket | [ngp.md](ngp.md) | ✅ |
| Neo Geo Pocket Color | [ngpc.md](ngpc.md) | ✅ |
| Nintendo 3DS | [3ds.md](3ds.md) | ✅ |
| PC Engine / TurboGrafx-16 | [pcengine.md](pcengine.md) | ✅ |
| Sega 32X | [sega32x.md](sega32x.md) | ✅ |
| SG-1000 | [sg1000.md](sg1000.md) | ✅ |
| SNES | [snes.md](snes.md) | ✅ |
| Vectrex | [vectrex.md](vectrex.md) | ✅ |
| Virtual Boy | [virtualboy.md](virtualboy.md) | ✅ |
| WonderSwan | [wonderswan.md](wonderswan.md) | ✅ |
| WonderSwan Color | [wonderswancolor.md](wonderswancolor.md) | ✅ |

### Disc-Based Systems (Redump)

| System | File | Format | Myrient |
|--------|------|--------|---------|
| 3DO | [3do.md](3do.md) | CHD | ✅ |
| Dreamcast | [dreamcast.md](dreamcast.md) | CHD/GDI | ✅ |
| GameCube | [gamecube.md](gamecube.md) | RVZ/NKit | ✅ |
| Mega CD | [megacd.md](megacd.md) | CHD | ✅ |
| PC Engine CD | [pcenginecd.md](pcenginecd.md) | CHD | ✅ |
| PlayStation | [psx.md](psx.md) | CHD | ✅ |
| PlayStation 2 | [ps2.md](ps2.md) | CHD | ✅ |
| PlayStation 3 | [ps3.md](ps3.md) | Decrypted ISO | ✅ |
| PlayStation Portable | [psp.md](psp.md) | CHD/CSO | ✅ |
| Saturn | [saturn.md](saturn.md) | CHD | ✅ |
| Wii | [wii.md](wii.md) | RVZ/NKit | ✅ |
| Wii U | [wiiu.md](wiiu.md) | WUX | ✅ |
| Xbox | [xbox.md](xbox.md) | **XISO** | ✅ |
| Xbox 360 | [xbox360.md](xbox360.md) | ISO | ✅ |

---

## Additional Systems (Easy to Add)

These systems have simple ROM formats and Myrient availability:

### Cartridge - Easy Additions

| System | File | Notes | Myrient |
|--------|------|-------|---------|
| Fairchild Channel F | [channelf.md](channelf.md) | First microprocessor console (1976) | ✅ |
| Odyssey 2 / Videopac | [odyssey2.md](odyssey2.md) | Magnavox 1978 | ✅ |
| Bally Astrocade | [astrocde.md](astrocde.md) | 1978 | ✅ |
| Arcadia 2001 | [arcadia.md](arcadia.md) | Emerson 1982 | ✅ |
| Super Cassette Vision | [scv.md](scv.md) | Epoch 1984 | ✅ |
| Casio PV-1000 | [pv1000.md](pv1000.md) | Japan only 1983 | ✅ |
| PC Engine SuperGrafx | [supergrafx.md](supergrafx.md) | Enhanced PCE | ✅ |
| Famicom Disk System | [fds.md](fds.md) | NES add-on | ✅ |
| Satellaview | [satellaview.md](satellaview.md) | SNES satellite | ✅ |
| Sufami Turbo | [sufami.md](sufami.md) | SNES add-on | ✅ |
| N64DD | [n64dd.md](n64dd.md) | N64 disk drive | ✅ |
| Pokemon Mini | [pokemini.md](pokemini.md) | Tiny handheld | ✅ |
| Watara Supervision | [supervision.md](supervision.md) | GB competitor | ✅ |
| Mega Duck | [megaduck.md](megaduck.md) | GB clone | ✅ |
| Gamate | [gamate.md](gamate.md) | GB competitor | ✅ |
| Game.com | [gamecom.md](gamecom.md) | Tiger 1997 | ✅ |

### Disc-Based - Easy Additions

| System | File | Format | Myrient |
|--------|------|--------|---------|
| Neo Geo CD | [neogeocd.md](neogeocd.md) | CHD | ✅ Redump |
| PC-FX | [pcfx.md](pcfx.md) | CHD | ✅ Redump |
| Jaguar CD | [jaguarcd.md](jaguarcd.md) | CHD | ✅ Redump |
| Amiga CD32 | [amigacd32.md](amigacd32.md) | CHD | ✅ Redump |
| CD-i | [cdi.md](cdi.md) | CHD | ✅ Redump |
| PS Vita | [psvita.md](psvita.md) | VPK/NoNpDrm | ✅ |

### Arcade

| System | File | Notes |
|--------|------|-------|
| Neo Geo (AES/MVS) | [neogeo.md](neogeo.md) | FBNeo romset |
| Atomiswave | [atomiswave.md](atomiswave.md) | Sammy arcade |
| NAOMI | [naomi.md](naomi.md) | Sega arcade |
| Triforce | [triforce.md](triforce.md) | Nintendo/Sega/Namco |

### Computers

| System | File | Notes | Myrient |
|--------|------|-------|---------|
| Commodore 64 | [c64.md](c64.md) | Most popular 8-bit | ✅ |
| Amiga 500 | [amiga500.md](amiga500.md) | OCS/ECS | ✅ |
| Amiga 1200 | [amiga1200.md](amiga1200.md) | AGA | ✅ |
| Atari ST | [atarist.md](atarist.md) | 16-bit | ✅ |
| ZX Spectrum | [zxspectrum.md](zxspectrum.md) | UK 8-bit | ✅ |
| MSX/MSX2 | [msx1.md](msx1.md) / [msx2.md](msx2.md) | Microsoft standard | ✅ |
| DOS | [dos.md](dos.md) | DOSBox | ✅ |
| PC-98 | [pc98.md](pc98.md) | Japan PC | ✅ |
| X68000 | [x68000.md](x68000.md) | Sharp 16-bit | ✅ Redump |
| FM Towns | [fmtowns.md](fmtowns.md) | Fujitsu | ✅ Redump |

---

## All Systems Index (168 total)

<details>
<summary>Click to expand full list</summary>

### A-C
- [3do.md](3do.md) - 3DO Interactive Multiplayer
- [3ds.md](3ds.md) - Nintendo 3DS
- [adam.md](adam.md) - Coleco Adam
- [advision.md](advision.md) - Entex Adventure Vision
- [amiga1200.md](amiga1200.md) - Amiga 1200 (AGA)
- [amiga500.md](amiga500.md) - Amiga 500 (OCS/ECS)
- [amigacd32.md](amigacd32.md) - Amiga CD32
- [amigacdtv.md](amigacdtv.md) - Commodore CDTV
- [amstradcpc.md](amstradcpc.md) - Amstrad CPC
- [apfm1000.md](apfm1000.md) - APF MP-1000
- [apple2.md](apple2.md) - Apple II
- [apple2gs.md](apple2gs.md) - Apple IIGS
- [arcadia.md](arcadia.md) - Arcadia 2001
- [archimedes.md](archimedes.md) - Acorn Archimedes
- [arduboy.md](arduboy.md) - Arduboy
- [astrocde.md](astrocde.md) - Bally Astrocade
- [atari2600.md](atari2600.md) - Atari 2600
- [atari5200.md](atari5200.md) - Atari 5200
- [atari7800.md](atari7800.md) - Atari 7800
- [atari800.md](atari800.md) - Atari 800
- [atarijaguar.md](atarijaguar.md) - Atari Jaguar
- [atarilynx.md](atarilynx.md) - Atari Lynx
- [atarist.md](atarist.md) - Atari ST
- [atom.md](atom.md) - Acorn Atom
- [atomiswave.md](atomiswave.md) - Sammy Atomiswave
- [bbc.md](bbc.md) - BBC Micro
- [c128.md](c128.md) - Commodore 128
- [c20.md](c20.md) - Commodore VIC-20
- [c64.md](c64.md) - Commodore 64
- [camplynx.md](camplynx.md) - Camputers Lynx
- [cdi.md](cdi.md) - Philips CD-i
- [channelf.md](channelf.md) - Fairchild Channel F
- [coco.md](coco.md) - TRS-80 Color Computer
- [colecovision.md](colecovision.md) - ColecoVision
- [commanderx16.md](commanderx16.md) - Commander X16
- [cplus4.md](cplus4.md) - Commodore Plus/4
- [crvision.md](crvision.md) - VTech CreatiVision

### D-G
- [daphne.md](daphne.md) - Daphne Laserdisc
- [dice.md](dice.md) - DICE
- [dos.md](dos.md) - MS-DOS
- [dreamcast.md](dreamcast.md) - Sega Dreamcast
- [easyrpg.md](easyrpg.md) - EasyRPG
- [electron.md](electron.md) - Acorn Electron
- [fbneo.md](fbneo.md) - FinalBurn Neo
- [fds.md](fds.md) - Famicom Disk System
- [flash.md](flash.md) - Adobe Flash
- [fm7.md](fm7.md) - Fujitsu FM-7
- [fmtowns.md](fmtowns.md) - FM Towns
- [gamate.md](gamate.md) - Bit Corp Gamate
- [gameandwatch.md](gameandwatch.md) - Game & Watch
- [gamecom.md](gamecom.md) - Tiger Game.com
- [gamecube.md](gamecube.md) - Nintendo GameCube
- [gamegear.md](gamegear.md) - Sega Game Gear
- [gamepock.md](gamepock.md) - Epoch Game Pocket
- [gb.md](gb.md) - Game Boy
- [gb2players.md](gb2players.md) - Game Boy 2 Players
- [gba.md](gba.md) - Game Boy Advance
- [gbc.md](gbc.md) - Game Boy Color
- [gbc2players.md](gbc2players.md) - Game Boy Color 2 Players
- [gc.md](gc.md) - GameCube (alternate)
- [gmaster.md](gmaster.md) - Hartung Game Master
- [gp32.md](gp32.md) - GamePark GP32
- [gx4000.md](gx4000.md) - Amstrad GX4000

### H-N
- [ikemen.md](ikemen.md) - Ikemen Go
- [intellivision.md](intellivision.md) - Mattel Intellivision
- [jaguarcd.md](jaguarcd.md) - Atari Jaguar CD
- [laser310.md](laser310.md) - Laser 310
- [lindbergh.md](lindbergh.md) - Sega Lindbergh
- [lowresnx.md](lowresnx.md) - LowRes NX
- [lynx.md](lynx.md) - Atari Lynx (alternate)
- [macintosh.md](macintosh.md) - Apple Macintosh
- [mame.md](mame.md) - MAME
- [mastersystem.md](mastersystem.md) - Sega Master System
- [megacd.md](megacd.md) - Sega/Mega CD
- [megadrive.md](megadrive.md) - Sega Genesis/Mega Drive
- [megaduck.md](megaduck.md) - Mega Duck
- [model2.md](model2.md) - Sega Model 2
- [model3.md](model3.md) - Sega Model 3
- [msx1.md](msx1.md) - MSX
- [msx2.md](msx2.md) - MSX2
- [msx2plus.md](msx2plus.md) - MSX2+
- [msxturbor.md](msxturbor.md) - MSX turboR
- [mugen.md](mugen.md) - M.U.G.E.N
- [multivision.md](multivision.md) - Othello Multivision
- [n64.md](n64.md) - Nintendo 64
- [n64dd.md](n64dd.md) - Nintendo 64DD
- [naomi.md](naomi.md) - Sega NAOMI
- [naomi2.md](naomi2.md) - Sega NAOMI 2
- [namco2x6.md](namco2x6.md) - Namco System 246
- [nds.md](nds.md) - Nintendo DS
- [neogeo.md](neogeo.md) - Neo Geo AES/MVS
- [neogeocd.md](neogeocd.md) - Neo Geo CD
- [nes.md](nes.md) - Nintendo Entertainment System
- [ngp.md](ngp.md) - Neo Geo Pocket
- [ngpc.md](ngpc.md) - Neo Geo Pocket Color

### O-S
- [odyssey2.md](odyssey2.md) - Magnavox Odyssey 2
- [openbor.md](openbor.md) - OpenBOR
- [oricatmos.md](oricatmos.md) - Oric Atmos
- [pc88.md](pc88.md) - NEC PC-88
- [pc98.md](pc98.md) - NEC PC-98
- [pcecd.md](pcecd.md) - PC Engine CD
- [pcengine.md](pcengine.md) - PC Engine
- [pcenginecd.md](pcenginecd.md) - PC Engine CD (alternate)
- [pcfx.md](pcfx.md) - NEC PC-FX
- [pdp1.md](pdp1.md) - PDP-1
- [pet.md](pet.md) - Commodore PET
- [pico.md](pico.md) - Sega Pico
- [pico8.md](pico8.md) - PICO-8
- [pokemini.md](pokemini.md) - Pokemon Mini
- [ps2.md](ps2.md) - PlayStation 2
- [ps3.md](ps3.md) - PlayStation 3
- [ps4.md](ps4.md) - PlayStation 4
- [psp.md](psp.md) - PlayStation Portable
- [psvita.md](psvita.md) - PlayStation Vita
- [psx.md](psx.md) - PlayStation
- [pv1000.md](pv1000.md) - Casio PV-1000
- [pyxel.md](pyxel.md) - Pyxel
- [samcoupe.md](samcoupe.md) - SAM Coupé
- [satellaview.md](satellaview.md) - Satellaview
- [saturn.md](saturn.md) - Sega Saturn
- [scummvm.md](scummvm.md) - ScummVM
- [scv.md](scv.md) - Super Cassette Vision
- [sega32x.md](sega32x.md) - Sega 32X
- [segacd.md](segacd.md) - Sega CD
- [sg1000.md](sg1000.md) - Sega SG-1000
- [sgb.md](sgb.md) - Super Game Boy
- [singe.md](singe.md) - SINGE
- [snes.md](snes.md) - Super Nintendo
- [snes-msu1.md](snes-msu1.md) - SNES MSU-1
- [socrates.md](socrates.md) - VTech Socrates
- [solarus.md](solarus.md) - Solarus
- [spectravideo.md](spectravideo.md) - Spectravideo
- [sufami.md](sufami.md) - SuFami Turbo
- [supergrafx.md](supergrafx.md) - PC Engine SuperGrafx
- [supervision.md](supervision.md) - Watara Supervision
- [supracan.md](supracan.md) - Super A'Can

### T-Z
- [thomson.md](thomson.md) - Thomson
- [ti99.md](ti99.md) - TI-99/4A
- [tic80.md](tic80.md) - TIC-80
- [triforce.md](triforce.md) - Triforce
- [tutor.md](tutor.md) - Tomy Tutor
- [uzebox.md](uzebox.md) - Uzebox
- [vc4000.md](vc4000.md) - VC 4000
- [vectrex.md](vectrex.md) - Vectrex
- [videopacplus.md](videopacplus.md) - Videopac+
- [vircon32.md](vircon32.md) - Vircon32
- [virtualboy.md](virtualboy.md) - Virtual Boy
- [vis.md](vis.md) - Tandy VIS
- [voxatron.md](voxatron.md) - Voxatron
- [vsmile.md](vsmile.md) - V.Smile
- [wasm4.md](wasm4.md) - WASM-4
- [wii.md](wii.md) - Nintendo Wii
- [wiiu.md](wiiu.md) - Nintendo Wii U
- [wonderswan.md](wonderswan.md) - WonderSwan
- [wonderswancolor.md](wonderswancolor.md) - WonderSwan Color
- [wswan.md](wswan.md) - WonderSwan (alternate)
- [wswanc.md](wswanc.md) - WonderSwan Color (alternate)
- [x1.md](x1.md) - Sharp X1
- [x68000.md](x68000.md) - Sharp X68000
- [xbox.md](xbox.md) - Microsoft Xbox
- [xbox360.md](xbox360.md) - Microsoft Xbox 360
- [xegs.md](xegs.md) - Atari XEGS
- [zx81.md](zx81.md) - Sinclair ZX81
- [zxspectrum.md](zxspectrum.md) - ZX Spectrum

</details>

---

## Key References by Topic

### CHD Compression
Most disc-based systems support MAME's CHD format:
- See [Disk Image Compression](https://wiki.batocera.org/disk_image_compression)

### XISO Conversion (Xbox)
Xbox requires XISO format (extracted game partition):
- Tool: `extract-xiso -r game.iso`
- See [xbox.md](xbox.md) for full instructions

### Multi-Disc Games
Use m3u playlists for multi-disc games:
- PlayStation, PlayStation 2, Saturn, Dreamcast

---
Last updated: 2025-12-06
