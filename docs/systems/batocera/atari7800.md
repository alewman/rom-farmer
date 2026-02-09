# Atari 7800

**Source:** https://wiki.batocera.org/systems:atari7800  
**Last fetched:** 2025-12-06 16:18:41

---

This article needs some TLC. Read at your own risk.

# Atari 7800
The Atari 7800 (a.k.a. ProSystem) is a home videogame console developed by Atari. It was released in 1986. It is the successor to both the [Atari 2600](systems:atari2600) and [5200](systems:atari5200).

It was capable of running Atari 2600 games, making it the first backwards compatible home console.

In an attempt to curb the flood of low-quality games that caused the NA videogame crash previously, the cartridges had to be digitally signed by Atari to function on the console.

This system scrapes metadata for the "atari7800" group and loads the `atari7800` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: prosystem](#libretro:_prosystem)
- **Folder:** `/userdata/roms/atari7800`
- **Accepted ROM formats:** `.a78`, `.bin`, `.zip`, `.7z`

## BIOS
BIOS files are optional.

| MD5 checksum | Share file path | Description |
| | `bios/7800 BIOS (U).rom` | |

## ROMs
Place your Atari 7800 ROMs in `/userdata/roms/atari7800`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `atari7800.videomode`, `atari7800.ratio`, `atari7800.smooth`, `atari7800.shaders`, `atari7800.pixel_perfect`, `atari7800.decoration`, `atari7800.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `atari7800.gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `atari7800.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `atari7800.video_threaded`** | Improves performance at the cost of latency and more video stuttering.\\ => On `true`, Off `false`. |

#### libretro: ProSystem
A [libretro port](https:*github.com/libretro/prosystem-libretro) of [ProSystem](https:*gstanton.github.io/ProSystem1_3/), an Atari 7800 emulator.

##### libretro: ProSystem configuration
## Controls
Here are the default Atari 7800's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).