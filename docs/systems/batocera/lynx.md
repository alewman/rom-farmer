# Atari Lynx

**Source:** https://wiki.batocera.org/systems:lynx  
**Last fetched:** 2025-12-06 16:19:11

---

# Atari Lynx
The Atari Lynx was a fourth-generation handheld game console released by [Atari](wp>Atari) on September 1, 1989 and it retailed for $179.99 USD.

It has a WDC 65SC02 CPU. Notably, it was the world's first handheld system that used a color LCD screen, as well as having fairly advanced graphics for the time. It featured buttons on the top and bottom of the right side of the unit, allowing games to be played in either sideways landscape mode, or upright portrait mode.

Epyx started development of the handheld in 1986, completing it in 1987. Epyx demonstrated the console under the name "Handy" at the Winter Consumer Electronics Show in 1989. Facing financial difficulties, Epyx sought out a partner to take charge of unit production and distribution while they took care of software development. Nintendo and Sega declined, but Atari agreed, releasing the "Atari Lynx" in September 1989. At the end of the year, Epyx would file for complete bankruptcy and Atari would completely acquire them, essentially owning the entire handheld project. This ironically lead to Atari having to purchase [Amigas](systems:amiga500) from their competitor Commodore in order to develop Lynx software.

The console itself was considered successful and met its projected sales. Despite this, it would be discontinued in 1995, with Atari falling out of the console market with its failure of the [Jaguar](systems:jaguar).

This system scrapes metadata for the "atarilynx" group and loads the `atarilynx` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Cores available:** [Mednafen:_Lynx](#libretro:_mednafen_lynx), [libretro: handy](#libretro:_handy)
- **Folder:** `/userdata/roms/lynx`
- **Accepted ROM formats:** `.bll`, `.lnx`, `.lyx`, `.o`, `.zip`, `.7z`

## BIOS
| MD5 checksum | Share file path | Description |
| `fcd403db69f54290b51035d82f835e7b` | `bios/lynxboot.img` | Lynx Boot Image |

## ROMs
Place your Atari Lynx ROMs in `/userdata/roms/lynx`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `lynx.videomode`, `lynx.ratio`, `lynx.smooth`, `lynx.shaders`, `lynx.pixel_perfect`, `lynx.decoration`, `lynx.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `lynx.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `lynx.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `lynx.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: Mednafen_Lynx
Beetle Lynx is an Atari Lynx video game system emulator that can be used as a libretro core. Specifically it's a port of Mednafen Lynx which is a fork of Handy.

#### libretro: handy
##### libretro: handy configuration
## Controls
Here are the default Atari Lynx's controls shown on a [Batocera Retropad](:configure_a_controller):

The default button mapping to the Lynx is as following:

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).