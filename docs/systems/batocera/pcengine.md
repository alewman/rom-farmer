# PC Engine/TurboGrafx-16

**Source:** https://wiki.batocera.org/systems:pcengine  
**Last fetched:** 2025-12-06 16:19:32

---

# PC Engine/TurboGrafx-16
The PC Engine is a fourth-generation console developed by NEC. It was released in Japan on October 1987.

The console was redesigned for its North American release, and is known as the TurboGrafx-16 (the 16 representing how it uses 16-bit components (despite the fact that it only has an 8-bit CPU)) there.

Its later European/UK release in 1989 would use the original Japanese design and name. Unfortunately, due to its later release in the region it would end up competing against the other fourth-generation consoles despite its third-generation hardware. The [PC Engine SuperGrafx](systems:supergrafx) would be released shortly after to address this.

The PC Engine/TurboGrafx-16 would later get a CD-ROM attachment. For emulation of those games, use the [system specific to PC Engine CD](systems:pcenginecd).

This system scrapes metadata for the "pcengine" group and loads the `pcengine` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Cores available:** [libretro: pce](#libretro:_pce), [libretro: pce_fast](#libretro:_pce_fast)
- **Folder:** `/userdata/roms/pcengine`
- **Accepted ROM formats:** `.pce`, `.bin`, `.zip`, `.7z`

## BIOS
This BIOS file is required.

| MD5 checksum | Share file path | Description |
| `38179df8f4ac870017db21ebcbf53114` | `bios/syscard3.pce` | Super CD-ROM2 System V3.xx |

These BIOS files can also work, however they are known to have compatibility issues with certain games:

| MD5 checksum | Share file path | Description |
| | `bios/syscard2.pce` | CD-ROM System V2.xx |
| | `bios/syscard1.pce` | CD-ROM System V1.xx |
| | `bios/gexpress.pce` | Game Express CD Card |

## ROMs
Place your PC Engine ROMs in `/userdata/roms/pcengine`.

For PC Engine CD-ROMs, instead place them in `/userdata/roms/pcenginecd`.

Certain ROMs may not work if compressed in a `.zip` or `.7z` file.
## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `pcengine.videomode`, `pcengine.ratio`, `pcengine.smooth`, `pcengine.shaders`, `pcengine.pixel_perfect`, `pcengine.decoration`, `pcengine.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `pcengine.gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `pcengine.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `pcengine.video_threaded`** | Improves performance at the cost of latency and more video stuttering.\\ => On `true`, Off `false`. |

#### libretro: pce
##### libretro: pce configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **REDUCE SPRITE FLICKERING `global.pce_nospritelimit`** | Enhancement. Remove the sixteen sprites per line limit.\\ => Off `disabled`, On `enabled`. |
| **CONTROLLER 1 TYPE `global.controller1_pce`** | \\ => PCE Joypad `1`, PCE Mouse `2`. |

#### libretro: pce_fast
##### libretro: pce_fast configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **REDUCE SPRITE FLICKERING `global.pce_nospritelimit`** | Enhancement. Remove the sixteen sprites per line limit.\\ => Off `disabled`, On `enabled`. |
| **CONTROLLER 1 TYPE `global.controller1_pce`** | \\ => PCE Joypad `1`, PCE Mouse `2`. |

## Controls
Here are the default PC Engine's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).