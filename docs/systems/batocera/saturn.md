# Sega Saturn

**Source:** https://wiki.batocera.org/systems:saturn  
**Last fetched:** 2025-12-06 16:19:42

---

# Sega Saturn
The Sega Saturn is fifth generation home console developed by Sega. It was released in 1994, retailing for $399.99 USD ($740 in 2021).

The Saturn's hardware borrows many components from the [Sega Titan Video](https://segaretro.org/Sega_Titan_Video) arcade system. But instead of reading from a cartridge, it uses CD-ROMs.

The Saturn is considered one of the more complicated consoles to both program for by developers and to properly emulate. In fact, it's better to consider this a sixth generation console for performance reasons. In an ironic twist of events, [the Saturn's successor](systems:dreamcast) is much easier to emulate than the Saturn itself.

This system scrapes metadata for the "saturn" group and loads the `saturn` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Cores available:** [libretro: beetle-saturn](#libretro:_beetle-saturn), [libretro: kronos](#libretro:_kronos), [libretro: yabasanshiro](#libretro:_yabasanshiro)
- **Folder:** `/userdata/roms/saturn`
- **Accepted ROM formats:** `.cue`, `.ccd`, `.m3u`, `.chd`, `.iso`, `.zip`

## BIOS
| MD5 checksum | Share file path | Description |
| `85ec9ca47d8f6807718151cbcca8b964` | `bios/sega_101.bin` | |
| `3240872c70984b6cbfda1586cab68dbe` | `bios/mpr-17933.bin` | |
| `255113ba943c92a54facd25a10fd780c` | `bios/mpr-18811-mx.ic1` | |
| `1cd19988d1d72a3e7caa0b73234c96b4` | `bios/mpr-19367-mx.ic1` | |
| `af5828fdff51384f99b3c4926be27762` | `bios/saturn_bios.bin` | |

## ROMs
Place your Sega Saturn ROMs in `/userdata/roms/saturn`.

### Multi-disc games
[libretro: yabasanshiro](#libretro:_yabasanshiro) does not support swapping the disc using RetroArch's disc control menu, so the save file must be renamed to disc 2's game name and the disc's ROM must be loaded manually in Batocera in order to "swap discs". There is no way to use playlists to achieve this functionality.

For example, if you have a game like `Panzer Dragoon (disc 1).chd` and you've reached the end of the disc and need to swap, go into the `saves/saturn/` folder and rename `Panzer Dragoon (disc 1).sav` to `Panzer Dragoon (disc 2).sav`. Then, load the `Panzer Dragoon (disc 2).chd` game in Batocera and continue from where you left off.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `saturn.videomode`, `saturn.ratio`, `saturn.smooth`, `saturn.shaders`, `saturn.pixel_perfect`, `saturn.decoration`, `saturn.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `saturn.gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `saturn.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `saturn.video_threaded`** | Improves performance at the cost of latency and more video stuttering.\\ => On `true`, Off `false`. |

#### libretro: beetle-saturn
The [libretro port](https:*github.com/libretro/beetle-saturn-libretro) of the original [Mednafen](https:*mednafen.github.io/) Saturn core. A highly accurate but demanding emulator.

beetle-saturn does not support opening `.zip` files.

##### libretro: beetle-saturn configuration
#### libretro: kronos
##### libretro: kronos configuration
#### libretro: yabasanshiro
[Yaba Sanshiro](http:*www.uoyabause.org/) is an [open-source](https:*github.com/devmiyax/yabause) Sega Saturn emulator. Initially forked from [Yabause](https://github.com/Yabause/yabause).

This is the libretro port of it.

##### libretro: yabasanshiro configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **RENDERING RESOLUTION `global.resolution_mode`** | Enhancement. Increase the rendering resolution. Makes 3D objects clearer. Do note that some games would run at their own unique but similar resolutions. Therefore, the listed resolutions may not be 100% accurate.\\ => original `original`, 2x `2x`, 4x `4x`, 720p `720p`, 1080p `1080p`, 4k `4k`. |
| **MULTITAP `global.multitap_yabasanshiro`** | Allows up to 7 or 12 controllers in supported games.\\ => Off `disabled`, Port1 `port1`, Port2 `port2`, Port1+2 `port12`. |

## Controls
The default control scheme is broken in **v38 and before**. Go to **Quick Menu** -> **Controls** -> **Port 1 Controls**:

and change it to this:

Here are the default Sega Saturn's controls shown on a [Batocera Retropad](:configure_a_controller) **since v39**:

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).