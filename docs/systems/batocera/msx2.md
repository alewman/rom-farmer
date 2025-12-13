# MSX2

**Source:** https://wiki.batocera.org/systems:msx2  
**Last fetched:** 2025-12-06 16:19:18

---

This article needs some TLC. Read at your own risk.

# MSX2
The MSX2 is a computer developed by Microsoft. It was released in 1985. Notable titles include [Metal Gear](wp>Metal_Gear_(video_game)).

Despite this being a product of Microsoft, it's likely you've never heard of this computer. It was primarily popular in the Asian, South American and European regions, but virtually unknown in North America.

Manufacturing was split up among a wide range of companies, including Pioneer, Panasonic, Sharp, Sony, Sanyo, Philips and LG Goldstar. Therefore, there were many different alternative names for the system, including:
- Panasonic FS-A1
- Panasonic FS-A1mkII
- Toshiba FS-TM1

This system scrapes metadata for the "msx" group and loads the `msx2` set from the currently selected theme, if available.

Grouped with the "msx" group of systems.

### Quick reference
- **Accepted ROM formats:** `.dsk`, `.mx2`, `.rom`, `.zip`, `.7z`, `.cas`, `.m3u`
- **Folder:** `/userdata/roms/msx2`

| Emulators |
| [libretro: bluemsx](#libretro:_bluemsx) |
| [libretro: fmsx](#libretro:_fmsx) |
| [openmsx](#openmsx) |
| [CLK](#CLK) |

## BIOS
| MD5 checksum | Share file path | Description |
| `ec3a01c91f24fbddcbcab0ad301bc9ef` | `bios/MSX2.ROM` for BlueMSX and OpenMSX, and `bios/MSX/msx2.rom` for CLK | |
| `2183c2aff17cf4297bdb496de78c2e8a` | `bios/MSX2EXT.ROM` for BlueMSX and OpenMSX, and `bios/MSX/msx2ext.rom` for CLK| |

Download the BlueMSX standalone at http://bluemsx.msxblue.com/rel_download/blueMSXv282full.zip

Then extract the "Databases" and "Machines" folders and add them to the `bios` folder.

For fMSX these files are required instead:

```

CARTS.SHA
CYRILLIC.FNT
DISK.ROM
FMPAC.ROM
FMPAC16.ROM
ITALIC.FNT
KANJI.ROM
MSX.ROM
MSX2.ROM
MSX2EXT.ROM
MSX2P.ROM
MSX2PEXT.ROM
MSXDOS2.ROM
PAINTER.ROM
RS232.ROM

```

## ROMs
Place your MSX2 ROMs in `/userdata/roms/msx2`.

### Multi-disk games
Some MSX2 games require multiple disks to play. This can be handled by RetroArch using a [M3U playlist](:cd_image_formats#multi-disc_games). For example:

```

test game disk 1.dsk
test game disk 2.dsk
test game disk 3.dsk

```

Batocera will automatically hide the extra disk files and only show the M3U playlist as the playable game in EmulationStation.

## Emulators
### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: blueMSX
[blueMSX](http:*bluemsx.msxblue.com/download.html) is a cycle-accurate, [open-source](https:*sourceforge.net/projects/bluemsx/) MSX/SVI/ColecoVision/SG-1000 emulator with high compatibility. This is the [libretro port](https://github.com/libretro/blueMSX-libretro) of it.

##### libretro: blueMSX configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **REDUCE SPRITE FLICKERING `global.bluemsx_nospritelimits`** | Enhancement. Remove the four sprites per line limit.\\ => Off `False`, On `True`. |

All other settings must be adjusted with RetroArch's **Quick Menu** (`[HOTKEY]` + ).

#### libretro: fMSX
##### libretro: fMSX configuration
Standardized features for this core: `msx2.rewind`, `msx2.autosave`, `msx2.netplay`, `msx2.cheevos`

### openmsx
#### openmsx configuration
Standardized features available to all cores of this emulator: `msx2.videomode`, `msx2.padtokeyboard`, `msx2.videomode`, `msx2.bezel`, `msx2.bezel_stretch`, `msx2.hud`, `msx2.hud_corner`, `msx2.bezel.tattoo`, `msx2.bezel.tattoo_corner`, `msx2.bezel.tattoo_file`, `msx2.bezel.resize_tattoo`

### CLK
[CLK aka Clock Signal](https://github.com/TomHarte/CLK) is a multi-system emulator that is focused on low-latency emulation, that can be used for MSX2. CLK has been added to Batocera 42.

## Controls
Here are the default MSX2's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).