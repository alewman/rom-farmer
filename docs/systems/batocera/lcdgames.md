# LCD Games

**Source:** https://wiki.batocera.org/systems:lcdgames  
**Last fetched:** 2025-12-06 16:19:09

---

# LCD Games
You remember those little coin-battery operated self-contained handheld games you got from a McDonald's Happy Meal back in the 90s? Yeah this is that.

One of the more infamous LCD handheld manufacturers was Tiger Electronics, who created a myriad of licensed handheld games between 1985 to the mid-2000s based on popular games/franchises of the time.

MAME/MESS, the emulator used for these things, supports some LCD handhelds made all the way back in 1979.

This system scrapes metadata for the "lcdgames" group and loads the `lcdgames` set from the currently selected theme, if available.

Grouped with the "lcdgames" group of systems.

### Quick reference
- **Accepted ROM formats:** `.mgw`, `.zip`, `.7z`
- **Folder:** `/userdata/roms/lcdgames`

| Emulators | Accepted ROM formats |
| libretro: mame | `.mgw`, `.zip`, `.7z` |
| [MAME](#mame) | `.zip`, `.7z` |

## BIOS
No LCD Games emulator in Batocera needs a BIOS file to run.

## ROMs
Place your LCD Games ROMs in `/userdata/roms/lcdgames`.

Nintendo Game & Watch games can be used in the `lcdgames` ROM folder, but they will most probably run better within the [Game & Watch system](systems:gameandwatch). Both `lcdgames` and `gameandwatch` folders can be grouped in EmulationStation under "LCD Games".

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `lcdgames.videomode`, `lcdgames.ratio`, `lcdgames.smooth`, `lcdgames.shaders`, `lcdgames.pixel_perfect`, `lcdgames.decoration`, `lcdgames.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `lcdgames.gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `lcdgames.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `lcdgames.video_threaded`** | Improves performance at the cost of latency and more video stuttering.\\ => On `true`, Off `false`. |

### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `lcdgames.videomode`, `lcdgames.decoration`, `lcdgames.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **VIDEO MODE `lcdgames.video`** | BGFX for post-processing, accel/opengl for raw image.\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX GRAPHICS API `lcdgames.bgfxbackend`** | Depends on video mode being set to BGFX. Vulkan is better, when supported.\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `lcdgames.bgfxshaders`** | Apply a post-processing effect.\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `lcdgames.switchres`** | Allows the use of switchres profiles if present.\\ => Off `0`, On `1`. |
| **VERTICAL ROTATION (TATE) `lcdgames.rotation`** | Rotates screen by 90 degrees. Intended for rotating displays.\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ALT DPAD MODE `lcdgames.altdpad`** | If the D-Pad is oriented incorrectly for your controller.\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |

## Controls
The controls for every LCD game was usually unique to that game in particular, although most did at least feature a "movement" related set of buttons on the left side and a few "action" buttons on the right. MAME will simply enumerate these as needed.

Here are the default LCD game controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).