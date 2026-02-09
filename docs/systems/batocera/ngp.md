# SNK Neo Geo Pocket

**Source:** https://wiki.batocera.org/systems:ngp  
**Last fetched:** 2025-12-06 16:19:26

---

# SNK Neo Geo Pocket
The Neo Geo Pocket is a monochrome handheld game console released by SNK. It was the company's first handheld system and is part of the Neo Geo family. It debuted in Japan in late 1998 but never saw an American release, being exclusive to Japan, Asia and Europe.   

This system scrapes metadata for the "ngp" group and loads the `ngp` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: Mednafen_ngp](#libretro:_mednafen_ngp)
- **Folder:** `/userdata/roms/ngp`
- **Accepted ROM formats:** `.ngp`, `.zip`, `.7z`

## BIOS
No Neo-Geo Pocket emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Neo-Geo Pocket ROMs in `/userdata/roms/ngp`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `ngp.videomode`, `ngp.ratio`, `ngp.smooth`, `ngp.shaders`, `ngp.pixel_perfect`, `ngp.decoration`, `ngp.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `ngp.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `ngp.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `ngp.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: Mednafen_ngp
Batocera uses the standalone port [Beetle NeoPop](https://github.com/libretro/beetle-ngp-libretro) based on Mednafen. Mednafen's Neo Geo Pocket emulation is based on NeoPop.

##### libretro: Mednafen_ngp configuration
## Controls
Here are the default Neo-Geo Pocket's controls shown on a [Batocera Retropad](:configure_a_controller):

The default button mapping to the Neo Geo Pocket is as following: 

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).