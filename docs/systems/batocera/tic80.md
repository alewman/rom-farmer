# TIC-80

**Source:** https://wiki.batocera.org/systems:tic80  
**Last fetched:** 2025-12-06 16:19:54

---

# TIC-80
Very similar and inspired by [Pico-8](systems:pico8), TIC-80 is a fantasy console for playing tiny games inspired by the 8-bit consoles era. It has never been physically released, but runs as a [software on computers like Windows / Mac / Linux and web browsers](https:*tic80.com/). The main difference between Pico-8 and TIC-80, besides the fantasy hardware constraints, is that TIC-80 is fully free and opensource, with [its code available on Github](https:*github.com/nesbox/TIC-80). They also have a Pro version for faster development, if you like this project, [please support them](https://nesbox.itch.io/tic80), it's well worth it.

### Fantasy hardware constraints
- Display: 240x136 16 colors
- Cartridge: .tic file, max 64kB
- Sound: 4 channel chiptunes
- Code: Lua, Moonscript, Javascript, Wren or Fennel
- Sprites: 256 8x8 foreground sprites, and 256 8x8 background tiles

This system scrapes metadata for the "tic80" group and loads the `tic80` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: tic80](#libretro:_tic80)
- **Folder:** `/userdata/roms/tic80`
- **Accepted ROM formats:** `.tic`

## BIOS
No BIOS is required for TIC-80

## ROMs
Place your TIC-80 ROMs in `/userdata/roms/tic80`.

### "Cartridges" and games format
TIC-80 games are distributed as text files (mostly) with the code, sprites and sounds embedded in them. You can download hundreds of .tic games, music and programs from the [TIC-80 official website](https://tic80.com/play). 

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `tic80.videomode`, `tic80.ratio`, `tic80.smooth`, `tic80.shaders`, `tic80.pixel_perfect`, `tic80.decoration`, `tic80.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `tic80.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `tic80.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `tic80.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: tic80
##### libretro: tic80 configuration
## Controls
Here are the default TIC-80's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).