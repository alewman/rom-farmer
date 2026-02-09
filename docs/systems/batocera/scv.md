# Super Cassette Vision

**Source:** https://wiki.batocera.org/systems:scv  
**Last fetched:** 2025-12-06 16:19:44

---

This article needs some TLC. Read at your own risk.

# Super Cassette Vision
The Super Cassette Vision (a.k.a. スーパーカセットビジョン, Suupaa Kasetto Bijon) is a console developed by Epoch Co. It was released in Japan on July, 1984 and France later that same year.

A version of the system targeted the young female market, the Super Lady Cassette Vision.

To say it was not successful is an understatement. Epoch would go on to drop out of the console market by 1987.

This system scrapes metadata for the "scv" group and loads the `scv` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: emuscv](#libretro:_emuscv)
- **Folder:** `/userdata/roms/scv`
- **Accepted ROM formats:** `.bin`, `.0`

## BIOS
| MD5 checksum | Share file path | Description |
| `635a978fd40db9a18ee44eff449fc126` | `bios/upd7801g.s01` | |

## ROMs
Place your Super Cassette Vision ROMs in `/userdata/roms/scv`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `scv.videomode`, `scv.ratio`, `scv.smooth`, `scv.shaders`, `scv.pixel_perfect`, `scv.decoration`, `scv.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `scv.gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `scv.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `scv.video_threaded`** | Improves performance at the cost of latency and more video stuttering.\\ => On `true`, Off `false`. |

#### libretro: emuscv
##### libretro: emuscv configuration
## Controls
Here are the default Super Cassette Vision's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).