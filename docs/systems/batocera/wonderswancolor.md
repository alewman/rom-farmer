# Bandai WonderSwan Color

**Source:** https://wiki.batocera.org/systems:wswanc  
**Last fetched:** 2025-12-06 16:12:28

---

# Bandai WonderSwan Color
The WonderSwan Color is a handheld game console designed by Bandai released in 2000, and was only available in Japan. While the original WonderSwan had only a black and white screen, the color version features 64k of RAM and a larger color LCD screen.

Prior to WonderSwan's release, Nintendo had a practical monopoly in the Japanese handheld market. After the release of the WonderSwan Color, Bandai took approximately 8% of the market share in Japan, partly due to its low price. 

This system scrapes metadata for the "wonderswancolor" group and loads the `wonderswancolor` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: Mednafen_wswan](#libretro:_mednafen_wswan)
- **Folder:** `/userdata/roms/wswanc`
- **Accepted ROM formats:** `.wsc`, `.zip`, `.7z`

## BIOS
No WonderSwan Color emulator in Batocera needs a BIOS file to run.

## ROMs
Place your WonderSwan Color ROMs in `/userdata/roms/wswanc`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `wswanc.videomode`, `wswanc.ratio`, `wswanc.smooth`, `wswanc.shaders`, `wswanc.pixel_perfect`, `wswanc.decoration`, `wswanc.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `wswanc.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `wswanc.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `wswanc.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: Mednafen_wswan
Batocera uses the standalone port [Beetle Cygne](https:*github.com/libretro/beetle-wswan-libretro) based on Mednafen. Mednafen's WonderSwan emulation is based on [Cygne](http:*cygne.emuunlim.com/), modified with bug fixes and to add sound emulation. 

##### libretro: Mednafen_wswan configuration
## Controls
Here are the default WonderSwan Color's controls shown on a [Batocera Retropad](:configure_a_controller):

The default button mapping to the WonderSwan Color is 1-to-1 with the [Nintendo Game Boy](systems:gb). You can rotate the screen with the `[SELECT]` button.

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).