# PC Engine SuperGrafx

**Source:** https://wiki.batocera.org/systems:supergrafx  
**Last fetched:** 2025-12-06 16:19:51

---

# PC Engine SuperGrafx
The PC Engine SuperGrafx (a.k.a. PCエンジンスーパーグラフィックス, Pī Shī Enjin SūpāGurafikkusu, PC Engine 2 or simply "SuperGrafx") is a fourth-generation videogame console developed by NEC. It was released in Japan on December 1989 and France on May 1990.

Technically the successor to the [PC Engine](systems:pcengine), and the first console by NEC to be "true" 16-bit instead of partially using 16-bit components. It was primarily marketed as an upgrade to the existing PC Engine instead of a replacement, compatible with all the already existing PC Engine HuCards in addition to its own. It was also compatible with the CD-ROM² add-on, although no CD-based games were produced that took advantage of the SuperGrafx's superior hardware.

The hardware itself was rushed to the market, releasing several months before its intended release date of 1990.

This system scrapes metadata for the "supergrafx" group and loads the `supergrafx` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: Mednafen_SuperGrafx](#libretro:_mednafen_supergrafx)
- **Folder:** `/userdata/roms/supergrafx`
- **Accepted ROM formats:** `.pce`, `.sgx`, `.cue`, `.ccd`, `.chd`, `.zip`, `.7z`

## BIOS

Shares BIOS requirements with the [PC Engine CD-ROM²/TurboGrafx-CD](systems:pcenginecd).

This BIOS file is required.

| MD5 checksum | Share file path | Description |
| `38179df8f4ac870017db21ebcbf53114` | `bios/syscard3.pce` | Super CD-ROM2 System V3.xx |

These BIOS files can also work, however they are known to have compatibility issues with certain games:

| MD5 checksum | Share file path | Description |
| | `bios/syscard2.pce` | CD-ROM System V2.xx |
| | `bios/syscard1.pce` | CD-ROM System V1.xx |
| | `bios/gexpress.pce` | Game Express CD Card |

## ROMs
Place your Supergrafx ROMs in `/userdata/roms/supergrafx`.

To load [CD-ROM content](:cd_image_formats), a CUE sheet is *required*. CUE sheets can be [recovered](:cd_image_formats#cue_sbi_gdi_sheet_recovery) if lost.

The preferred format for disc compression is [CHD](:disk_image_compression#chd). CHDs, by their nature, include the CUE sheet information.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `supergrafx.videomode`, `supergrafx.ratio`, `supergrafx.smooth`, `supergrafx.shaders`, `supergrafx.pixel_perfect`, `supergrafx.decoration`, `supergrafx.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `supergrafx.gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `supergrafx.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `supergrafx.video_threaded`** | Improves performance at the cost of latency and more video stuttering.\\ => On `true`, Off `false`. |

#### libretro: Mednafen_SuperGrafx
A [libretro port](https:*github.com/libretro/beetle-supergrafx-libretro) of [Mednafen](https:*mednafen.github.io/)'s PCE-Fast core.

##### libretro: Mednafen_SuperGrafx configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **REDUCE SPRITE FLICKERING `global.sgx_nospritelimit`** | Enhancement. Remove the sixteen sprites per line limit.\\ => Off `disabled`, On `enabled`. |

The remaining settings can be adjusted from RetroArch's **Quick Menu** (`[HOTKEY]` +  in-game) -> **Options**.

## Controls
Here are the default SuperGrafx's controls shown on a [Batocera Retropad](:configure_a_controller):

| RetroPad | User 1 - 5 input descriptors | PCE Joypad 2-button | PCE Joypad 6-button |
|  | I | I | I |
|  | II | II | II |
|  | III | II Turbo On/Off | III |
|  | IV | I Turbo On/Off | IV |
| `[SELECT]` | Select | Select | Select |
| `[START]` | Run | Run | Run |
| D-Pad Up | D-Pad Up | D-Pad Up | D-Pad Up |
| D-Pad Down | D-Pad Down | D-Pad Down | D-Pad Down |
| D-Pad Left | D-Pad Left | D-Pad Left | D-Pad Left |
| D-Pad Right | D-Pad Right | D-Pad Right | D-Pad Right |
| `[L1]` | V | | V |
| `[R1]` | VI | | VI |
| `[R2]` | Mode Switch | Mode Switch | Mode Switch |
| `[L3]` | | Alternate II Turbo On/Off | |
| `[R3]` | | Alternate I Turbo On/Off | |

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).