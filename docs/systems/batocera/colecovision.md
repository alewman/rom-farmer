# ColecoVision

**Source:** https://wiki.batocera.org/systems:colecovision  
**Last fetched:** 2025-12-06 16:18:49

---

This article needs some TLC. Read at your own risk.

# ColecoVision
The ColecoVision is a second-generation video-game console produced by Coleco Industries. It retailed for $174.99 and had a Zilog Z80 CPU at 3.58 MHz with 8KB of RAM. Due to poor sales of the console (maybe related to the video-game crash in North America) Coleco Industries filed for bankruptcy soon after. It was notable for providing a close-to-arcade experiences for some games. Masayuki Uemura, head of [Famicom](systems:nes) development, stated that the ColecoVision set the bar that influenced how he approached the creation of the Famicom.

Coleco released the Expansion Module #1 that allowed the ColecoVision to play Atari 2600 games. [Atari did not like this,](https://www.nytimes.com/1983/03/12/business/company-news-atari-coleco-pact.html) settling out of court with Coleco to be licensed under Atari's patents.

The Expansion Module #3 would be released that would convert the ColecoVision into the [Coleco Adam home computer](wp>Coleco_Adam).

This system scrapes metadata for the `colecovision` group(s) and loads the `colecovision` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch) or [CLK](#CLK)
- **Core:** [libretro: bluemsx](#libretro:_bluemsx)
- **Folder:** `/userdata/roms/colecovision`
- **Accepted ROM formats:** `.bin`, `.col`, `.rom`, `.zip`, `.7z`

CLK has been added with Batocera 42.

## BIOS
Retroarch ColecoVision emulator in Batocera needs no BIOS file to run.

CLK requires the following BIOS file:
| MD5 checksum | Share file path | Description |
| `2c66f5911e5b42b8ebe113403548eee7` | `bios/ColecoVision/coleco.rom` | Only required for CLK |

## ROMs
Place your ColecoVision ROMs in `/userdata/roms/colecovision`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all cores of this emulator: `colecovision.videomode`, `colecovision.ratio`, `colecovision.smooth`, `colecovision.shaders`, `colecovision.pixel_perfect`, `colecovision.decoration`, `colecovision.game_translation`

| ES setting name `batocera.conf key` | Description => ES option `key value` |
| Settings that apply to all cores of this emulator |
| **GRAPHICS BACKEND `colecovision.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `colecovision.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |

#### libretro: Bluemsx
##### libretro: Bluemsx configuration
| ES setting name `batocera.conf key` | Description => ES option `key value` |
| Settings that apply to all systems this core supports |
| **REDUCE SPRITE FLICKERING `colecovision.bluemsx_nospritelimits`** | Remove the 4 sprite per line limit\\ => Off `False`, On `True`. |

### CLK
[CLK aka Clock Signal](https://github.com/TomHarte/CLK) is a multi-system emulator that is focused on low-latency emulation, that can be used for ColecoVision. CLK has been added to Batocera 42.

## Controls
The original controller has 2 side buttons (Side Button Left and Side Button Right) and a keyboard with 10 numeric values and 2 symbols. Only a fraction of these controls can be mapped to a standard controller, so 9 and 0 are missing in the default layout. 

The default button mapping for the ColecoVision's controls is as follows:

## Troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).