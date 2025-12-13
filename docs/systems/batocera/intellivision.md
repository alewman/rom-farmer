# Mattel Intellivision

**Source:** https://wiki.batocera.org/systems:intellivision  
**Last fetched:** 2025-12-06 16:19:07

---

This article needs some TLC. Read at your own risk.

# Mattel Intellivision
The Mattel Intellivision is a console developed by Mattel. It was released in 1979.

This system scrapes metadata for the "intellivision" group and loads the `intellivision` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: freeintv](#libretro:_freeintv)
- **Folder:** `/userdata/roms/intellivision`
- **Accepted ROM formats:** `.int`, `.bin`, `.rom`, `.zip`, `.7z`

## BIOS
| MD5 checksum | Share file path | Description |
| `62e761035cb657903761800f4437b8af` | `bios/exec.bin` | |
| `0cd5946c6473e42e8e4c2137785e427f` | `bios/grom.bin` | |

## ROMs
Place your Mattel Intellivision ROMs in `/userdata/roms/intellivision`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `intellivision.videomode`, `intellivision.ratio`, `intellivision.smooth`, `intellivision.shaders`, `intellivision.pixel_perfect`, `intellivision.decoration`, `intellivision.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `intellivision.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `intellivision.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `intellivision.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: freeintv
##### libretro: freeintv configuration
## Controls
Intellivision had a complex controller with
- 4 side-located action buttons (two for left handed players, two for right handed players). Top two side buttons are electronically the same, giving three distinct buttons.
- a 12-button numeric keypad with plastic overlays that slide into place as an extra layer on the keypad to show game-specific key functions

It's therefore recommended to use a bezel from [thebezelproject](https:*github.com/thebezelproject/BezelProject) to display those layouts, and to also display the game controller tattoo (available in `V39+`). More information on [decorations](https:*wiki.batocera.org/decoration).

The controller was often considered as a very bad one.

Here are the default Mattel Intellivision's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).