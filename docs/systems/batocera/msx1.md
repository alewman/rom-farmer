# MSX1

**Source:** https://wiki.batocera.org/systems:msx1  
**Last fetched:** 2025-12-06 16:19:17

---

This article needs some TLC. Read at your own risk.

# MSX1
The MSX1 is a computer developed by Microsoft. It was released in 1983.

This system scrapes metadata for the "msx" group(s) and loads the `msx1` set from the currently selected theme, if available.

Grouped with the "msx" group of systems.

### Quick reference
- **Accepted ROM formats:** `.dsk`, `.mx1`, `.rom`, `.zip`, `.7z`, `.cas`, `.m3u`
- **Folder:** `/userdata/roms/msx1`

| Emulators |
| [libretro: bluemsx](#libretro:_bluemsx) |
| [libretro: fmsx](#libretro:_fmsx) |
| [openmsx](#openmsx) |
| [CLK](#CLK) |

## BIOS
- BlueMSX (DEFAULT): Download the BlueMSX standalone version, available at [http://bluemsx.msxblue.com/rel_download/blueMSXv282full.zip](http://bluemsx.msxblue.com/rel_download/blueMSXv282full.zip), then extract the "Databases" and "Machines" folders and add them to the `/userdata/bios` folder.

- FMSX: Requires the following files (available with fmsx distribution), in the `/userdata/bios` folder:

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

CLK requires the following BIOS files:

| MD5 checksum | Share file path | Description |
| `364a1a579fe5cb8dba54519bcfcdac0d` | `bios/MSX/msx.rom` | Generic MSX BIOS |
| `6f69cc8b5ed761b03afd78000dfb0e19` | `bios/MSX/fmpac.rom` | FM-PAC ROM |

Except the case, these two files should be identical to the ones you get for FMSX.

## ROMs
Place your MSX1 ROMs in `/userdata/roms/msx1`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `msx1.videomode`, `msx1.videomode`, `msx1.ratio`, `msx1.shaderset`, `msx1.smooth`, `msx1.integerscale`, `msx1.bezel`, `msx1.bezel_stretch`, `msx1.hud`, `msx1.bezel.tattoo`, `msx1.bezel.tattoo_corner`, `msx1.bezel.tattoo_file`, `msx1.bezel.resize_tattoo`, `msx1.ai_service_enabled`, `msx1.ai_target_lang`, `msx1.ai_service_url`, `msx1.ai_service_pause`, `msx1.runahead`, `msx1.secondinstance`, `msx1.video_frame_delay_auto`, `msx1.vrr_runloop_enable`, `msx1.video_threaded`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `msx1.gfxbackend`** | Choose which graphics API library to use. Vulkan may not work for every core.\\ => OpenGL `gl`, GLCore `glcore`, Vulkan `vulkan`. |
| **AUDIO LATENCY `msx1.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **ALLOW ROTATION `msx1.video_allow_rotate`** | Allow cores to set rotation.\\ => On `true`, Off `false`. |
| **CONTROLLER TO LIGHT GUN `msx1.lightgun_map`** | Map controller inputs to light gun inputs.\\ => On `true`, Off `false`. |

#### libretro: bluemsx
##### libretro: bluemsx configuration
[blueMSX](http:*bluemsx.msxblue.com/download.html) is a cycle-accurate, [open-source](https:*sourceforge.net/projects/bluemsx/) MSX/SVI/ColecoVision/SG-1000 emulator with high compatibility. This is the [libretro port](https://github.com/libretro/blueMSX-libretro) of it.

Standardized features for this core: `msx1.rewind`, `msx1.autosave`, `msx1.padtokeyboard`, `msx1.cheevos`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **REDUCE SPRITE FLICKERING `global.bluemsx_nospritelimits`** | Enhancement. Remove the four sprites per line limit.\\ => Off `False`, On `True`. |

#### libretro: fmsx
##### libretro: fmsx configuration
Standardized features for this core: `msx1.rewind`, `msx1.autosave`, `msx1.netplay`, `msx1.cheevos`

### openmsx
#### openmsx configuration
Standardized features available to all cores of this emulator: `msx1.videomode`, `msx1.padtokeyboard`, `msx1.videomode`, `msx1.bezel`, `msx1.bezel_stretch`, `msx1.hud`, `msx1.bezel.tattoo`, `msx1.bezel.tattoo_corner`, `msx1.bezel.tattoo_file`, `msx1.bezel.resize_tattoo`

### CLK
[CLK aka Clock Signal](https://github.com/TomHarte/CLK) is a multi-system emulator that is focused on low-latency emulation, that can be used for MSX1. CLK has been added to Batocera 42.

## Controls
Here are the default MSX1's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).