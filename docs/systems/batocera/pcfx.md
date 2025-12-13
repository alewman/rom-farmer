# PC-FX

**Source:** https://wiki.batocera.org/systems:pcfx  
**Last fetched:** 2025-12-06 16:19:32

---

This article needs some TLC. Read at your own risk.

# PC-FX
The PC-FX is a fifth-generation videogame console developed by NEC. It was released exclusively in Japan on December 1994.

It adopted a desktop PC form-factor, most likely to facilitate future upgradeable hardware.

Despite being a fifth-generation console, it did not support 3D polygon graphics (probably serving as further fuel to convince Sony/Nintendo that their consoles' games should be nearly exclusively 3D, despite what the devs wanted to make). NEC's reasoning for this was that 3D processors of the time did not have high enough fidelity in their graphics compared to pre-rendered polygon graphics.

This, combined with the prohibitively high price and lack of developer support, is probably what lead to the low sales of the PC-FX. The PC-FX would mark NEC's last foray in the videogame console market.

This system scrapes metadata for the "pcfx" group and loads the `pcfx` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: pcfx](#libretro:_pcfx)
- **Folder:** `/userdata/roms/pcfx`
- **Accepted ROM formats:** `.cue`, `.ccd`, `.toc`, `.chd`, `.zip`, `.7z`

## BIOS
| MD5 checksum | Share file path | Description |
| `08e36edbea28a017f79f8d4f7ff9b6d7` | `bios/pcfx.rom` | |

## ROMs
Place your PC-FX ROMs in `/userdata/roms/pcfx`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `pcfx.videomode`, `pcfx.ratio`, `pcfx.smooth`, `pcfx.shaders`, `pcfx.pixel_perfect`, `pcfx.decoration`, `pcfx.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `pcfx.gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `pcfx.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `pcfx.video_threaded`** | Improves performance at the cost of latency and more video stuttering.\\ => On `true`, Off `false`. |

#### libretro: pcfx
##### libretro: pcfx configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **REDUCE SPRITE FLICKERING `global.pcfx_nospritelimit`** | Enhancement. Remove the sixteen sprites per line limit.\\ => Off `disabled`, On `enabled`. |

## Controls
6-button controller, much like the Genesis/Mega Drive.

Here are the default PC-FX's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).