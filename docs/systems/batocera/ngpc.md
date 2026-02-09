# SNK Neo Geo Pocket Color

**Source:** https://wiki.batocera.org/systems:ngpc  
**Last fetched:** 2025-12-06 16:19:27

---

# SNK Neo Geo Pocket Color
The Neo Geo Pocket Color (also known as NGPC), is a 16-bit colour handheld video game console manufactured by SNK. It is a successor to SNK's monochrome Neo Geo Pocket handheld which debuted in 1998 in Japan. The Neo Geo Pocket Color was released on March 16, 1999 in Japan, August 6, 1999 in North America, and some time in 1999 in Europe. In 2000, following SNK's purchase by American Pachinko (mechanical game originating in Japan) manufacturer Aruze, the Neo Geo Pocket Color was dropped from both the North American and European markets. It did, however, last until 2001 in Japan, with a total of 2 million units sold. 

This system scrapes metadata for the "ngpc" group and loads the `ngpc` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: Mednafen_ngp](#libretro:_mednafen_ngp)
- **Folder:** `/userdata/roms/ngpc`
- **Accepted ROM formats:** `.ngc`, `.zip`, `.7z`

## BIOS
No Neo-Geo Pocket Color emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Neo-Geo Pocket Color ROMs in `/userdata/roms/ngpc`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `ngpc.videomode`, `ngpc.ratio`, `ngpc.smooth`, `ngpc.shaders`, `ngpc.pixel_perfect`, `ngpc.decoration`, `ngpc.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `ngpc.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `ngpc.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `ngpc.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: Mednafen_ngp
Batocera uses the standalone port [Beetle NeoPop](https://github.com/libretro/beetle-ngp-libretro) based on Mednafen. Mednafen's Neo Geo Pocket emulation is based on NeoPop.

##### libretro: Mednafen_ngp configuration
## Controls
Here are the default Neo-Geo Pocket Color's controls shown on a [Batocera Retropad](:configure_a_controller):

The default button mapping to the Neo Geo Pocket Color is as following: 

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).