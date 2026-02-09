# Sega 32x

**Source:** https://wiki.batocera.org/systems:sega32x  
**Last fetched:** 2025-12-06 16:19:44

---

This article needs some TLC. Read at your own risk.

# Sega 32x
The Sega 32x is an add-on for the [Sega Megadrive/Genesis](systems:megadrive) console. It released in 1994, retailing for $159.99 USD.

This system scrapes metadata for the "sega32x" group and loads the `sega32x` set from the currently selected theme, if available.

Grouped with the "megadrive" group of systems. If you do not desire this behavior, you can unset it from **MAIN MENU** -> **GAME COLLECTION SETTINGS** -> **GROUPED SYSTEMS**.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: PicoDrive](#libretro:_picodrive)
- **Folder:** `/userdata/roms/sega32x`
- **Accepted ROM formats:** `.32x`, `.smd`, `.bin`, `.md`, `.zip`, `.7z`

## BIOS
No Sega 32x emulator in Batocera needs a BIOS file to run 32x games.

## ROMs
Place your Sega 32x ROMs in `/userdata/roms/sega32x`.

By default, your 32x ROMs will appear in the Megadrive system. If you do not desire this behavior, you can unset it from **MAIN MENU** -> **GAME COLLECTION SETTINGS** -> **GROUPED SYSTEMS**.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `sega32x.videomode`, `sega32x.ratio`, `sega32x.smooth`, `sega32x.shaders`, `sega32x.pixel_perfect`, `sega32x.decoration`, `sega32x.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `sega32x.gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `sega32x.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `sega32x.video_threaded`** | Improves performance at the cost of latency and more video stuttering.\\ => On `true`, Off `false`. |

#### libretro: PicoDrive
A lighter emulator which although not as accurate as other emulators, can be run on much weaker hardware. This should be the default for devices such as the Raspberry Pi Zero and other sub-1GHz CPUs. Currently the only cross-architecture option for 32X and Pico games.

##### libretro: PicoDrive configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **REDUCE SPRITE FLICKERING `global.picodrive_sprlim`** | Enhancement. Remove the eighty sprites per line limit.\\ => Off `disabled`, On `enabled`. |
| **CROP OVERSCAN `global.picodrive_cropoverscan`** | Zooms in to hide black borders.\\ => Off `disabled`, On `enabled`. |
| **CONTROLLER 1 TYPE `global.picodrive_controller1`** | Select what controller is plugged into port 1.\\ => Joypad 3 Button `3 button pad`, Joypad 6 Button `6 button pad`. |
| **CONTROLLER 2 TYPE `global.picodrive_controller2`** | Same as above but for port 2.\\ => Joypad 3 Button `3 button pad`, Joypad 6 Button `6 button pad`. |

## Controls
Here are the default Sega 32x's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).