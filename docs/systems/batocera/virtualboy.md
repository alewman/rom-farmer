# Virtual Boy

**Source:** https://wiki.batocera.org/systems:virtualboy  
**Last fetched:** 2025-12-06 16:19:58

---

# Virtual Boy
The Virtual Boy is a portable but not handheld console developed by Nintendo. It was released in 1995, retailing for $179.95 USD ($314.21 in 2020).

The Virtual Boy was renown for its gimmick: stereoscopic 3D achieved by parallax effect. A beam of light would be bounced against a constantly rotating mirror, and depending on where the light was aimed would project the illusion of an image due to persistence of vision.

Due to a lack of polish, little software support, high asking price (compared to a [Game Boy](systems:gb)), health concerns, lack of portability (requiring a table to use) and abandonment by Nintendo a year after its launch, the Virtual Boy was a commercial failure. However, the idea of 3D stereoscopic images would leave [its impression on Nintendo](systems:3ds) for many years to come...

This system scrapes metadata for the "virtualboy" group and loads the `virtualboy` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: vb](#libretro:_vb)
- **Folder:** `/userdata/roms/virtualboy`
- **Accepted ROM formats:** `.vb`, `.zip`, `.7z`

## BIOS
No Virtual Boy emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Virtual Boy ROMs in `/userdata/roms/virtualboy`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `virtualboy.videomode`, `virtualboy.ratio`, `virtualboy.smooth`, `virtualboy.shaders`, `virtualboy.pixel_perfect`, `virtualboy.decoration`, `virtualboy.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `virtualboy.gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `virtualboy.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `virtualboy.video_threaded`** | Improves performance at the cost of latency and more video stuttering.\\ => On `true`, Off `false`. |

#### libretro: vb
##### libretro: vb configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **COLOR PALETTE (2D) `global.2d_color_mode`** | \\ => original `black & red`, black/white `black & white`, black/blue `black & blue`, black/cyan `black & cyan`, black/electric cyan `black & electric cyan`, black/green `black & green`, black/magenta `black & magenta`, black/yellow `black & yellow`. |
| **ANAGLYPH PRESET (3D) `global.3d_color_mode`** | Use your physical anaglypth 3D glasses!\\ => Off `disabled`, red/blue `red & blue`, red/cyan `red & cyan`, red/electric cyan `red & electric cyan`, green/magenta `green & magenta`, yellow/blue `yellow & blue`. |

## Controls

The Virtual Boy's controller is unique, even among Nintendo's [other consoles](systems:n64) around the same time frame. Because of that, its controls aren't faithfully replicatable on modern controllers.

Here are the default Virtual Boy's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).