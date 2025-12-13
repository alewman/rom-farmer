# Nintendo Game & Watch

**Source:** https://wiki.batocera.org/systems:gameandwatch  
**Last fetched:** 2025-12-06 16:18:58

---

# Nintendo Game & Watch
The Game & Watch is a series of self-contained handheld LCD games by [Nintendo](wp>Nintendo), in which the first one was released all the way back on April 28, 1980. They are often seen as the precursor to the Game Boy/Color, although new Game & Watch games were still being released as late as 1991.

This system scrapes metadata for the "gameandwatch" group and loads the `gameandwatch` set from the currently selected theme, if available.

Grouped with the "lcdgames" group of systems.

### Quick reference

`.mgb` may also be supported, needs confirmation

- **Accepted ROM formats:** `.mgw`, `.zip`, `.7z`
- **Folder:** `/userdata/roms/gameandwatch`

| Emulators | Accepted ROM formats |
| [libretro: gw](#libretro:_gw) | `.mgw`, `.zip`, `.7z` |
| [MAME](#mame) | `.zip`, `.7z` |

## BIOS
No Game & Watch emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Game and Watch ROMs in `/userdata/roms/gameandwatch`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `gameandwatch.videomode`, `gameandwatch.ratio`, `gameandwatch.smooth`, `gameandwatch.shaders`, `gameandwatch.pixel_perfect`, `gameandwatch.decoration`, `gameandwatch.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `gameandwatch.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `gameandwatch.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `gameandwatch.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: gw
[gw-libretro](https://github.com/libretro/gw-libretro) is a simulator and not an emulator. This means that the games that can be played with it aren't actually the original games, but recreations of the games combined with the original artwork and an image of the handheld.

##### libretro: gw configuration
There are no specific configuration settings for this emulator.

### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `gameandwatch.videomode`, `gameandwatch.decoration`, `gameandwatch.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **GRAPHICS BACKEND `gameandwatch.video`** | Choose your graphics rendering\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX BACKEND `gameandwatch.bgfxbackend`** | Choose your graphics API\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `gameandwatch.bgfxshaders`** | Apply a particular visual effect\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `gameandwatch.switchres`** | CRT monitor SwitchRes support\\ => Off `0`, On `1`. |
| **TATE MODE `gameandwatch.rotation`** | Rotating display to vertical mode rendering\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ALT DPAD MODE `gameandwatch.altdpad`** | If the D-Pad does not work properly\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |

## Controls
The inputs are game specific. Press `START` to get an overlay like the following example: