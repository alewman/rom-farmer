# Atari XE Game System

**Source:** https://wiki.batocera.org/systems:xegs  
**Last fetched:** 2025-12-06 16:20:07

---

This article needs some TLC. Read at your own risk.

# Atari XE Game System
The Atari XE Game System is a computer developed by Atari. It was released in 1987.

This system scrapes metadata for the "xegs" group(s) and loads the `xegs` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.atr`, `.dsk`, `.xfd`, `.bin`, `.rom`, `.car`, `.zip`, `.7z`
- **Folder:** `/userdata/roms/xegs`

| Emulators |
| [libretro: mess](#libretro:_mess) |
| [MAME](#mame) |

## BIOS
| MD5 checksum | Share file path | Description |
| `42cbd989802c17d0ac3731d33270d835` | `bios/xegs.zip` | |

## ROMs
Place your Atari XE Game System ROMs in `/userdata/roms/xegs`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `xegs.videomode`, `xegs.videomode`, `xegs.ratio`, `xegs.shaderset`, `xegs.smooth`, `xegs.integerscale`, `xegs.bezel`, `xegs.bezel_stretch`, `xegs.hud`, `xegs.bezel.tattoo`, `xegs.bezel.tattoo_corner`, `xegs.bezel.tattoo_file`, `xegs.bezel.resize_tattoo`, `xegs.ai_service_enabled`, `xegs.ai_target_lang`, `xegs.ai_service_url`, `xegs.ai_service_pause`, `xegs.integerscale`, `xegs.runahead`, `xegs.secondinstance`, `xegs.video_frame_delay_auto`, `xegs.vrr_runloop_enable`, `xegs.video_threaded`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `xegs.gfxbackend`** | Choose which graphics API library to use. Vulkan may not work for every core.\\ => OpenGL `gl`, GLCore `glcore`, Vulkan `vulkan`. |
| **AUDIO LATENCY `xegs.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **ALLOW ROTATION `xegs.video_allow_rotate`** | Allow cores to set rotation.\\ => On `true`, Off `false`. |
| **CONTROLLER TO LIGHTGUN `xegs.lightgun_map`** | Map controller inputs to lightgun inputs\\ => On `true`, Off `false`. |

#### libretro: mess
##### libretro: mess configuration
Standardized features for this core: `xegs.autosave`, `xegs.netplay`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **OVERCLOCK (UNSTABLE) `global.mame_cpu_overclock`** | Enhancement. Reduces system slowdown. Causes issues in some games.\\ => default `default`, 30 `30`, 35 `35`, 40 `40`, 45 `45`, 50 `50`, 55 `55`, 60 `60`, 65 `65`, 70 `70`, 75 `75`, 80 `80`, 85 `85`, 90 `90`, 95 `95`, 100 `100`, 105 `105`, 110 `110`, 115 `115`, 120 `120`, 125 `125`, 130 `130`, 135 `135`, 140 `140`, 145 `145`, 150 `150`. |
| **RENDERING RESOLUTION `global.mame_altres`** | Enhancement. Increase the rendering resolution. Makes 3D objects clearer.\\ => 640x480 `640x480`, 800x600 `800x600`, 960x720 `960x720`, 1024x768 `1024x768`, 1280x720 `1280x720`, 1600x800 `1600x800`, 1920x1080 `1920x1080`, 2560x1440 `2560x1440`, 3840x2160 `3840x2160`. |
| **SHARE MAME ARTWORK `global.sharemameart`** | Use the same art paths as standalone MAME - not recommended if using decorations or shaders.\\ => On (Default) `1`, Off `0`. |
| **CROP ARTWORK `global.artworkcrop`** | Crop MAME artwork to maximize the game screen and only fill unused space.\\ => On (Default) `1`, Off `0`. |
| **CUSTOM MAME CONFIG `global.customcfg`** | Set system-wide controls via MAME menu\\ => On `1`, Off `0`. |
| **ALT DPAD MODE `global.altdpad`** | If the D-Pad is oriented incorrectly for your controller.\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |
| Settings specific to xegs ||
| **SOFTWARE LIST `xegs.softList`** | Use MAME software lists to identify ROM\\ => Don't Use (Default) `none`, Atari XE Game System cartridges `xegs`, Atari 400 / 800 floppy disks `a800_flop`. |
| **MEDIA TYPE `xegs.altromtype`** | Type of ROM file to load.\\ => Cartridge `cart`, Disk (Drive 1) `flop1`, Disk (Drive 2) `flop2`, Disk (Drive 3) `flop3`, Disk (Drive 4) `flop4`. |
| **UI KEYS `xegs.enableui`** | Toggle with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |
| **CUSTOM GAME CONFIG `xegs.pergamecfg`** | Enable per-game custom configuration via MAME menu.\\ => On `1`, Off `0`. |

### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `xegs.videomode`, `xegs.padtokeyboard`, `xegs.videomode`, `xegs.bezel`, `xegs.bezel_stretch`, `xegs.hud`, `xegs.bezel.tattoo`, `xegs.bezel.tattoo_corner`, `xegs.bezel.tattoo_file`, `xegs.bezel.resize_tattoo`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **VIDEO MODE `xegs.video`** | BGFX for post-processing, accel/opengl for raw image.\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX GRAPHICS API `xegs.bgfxbackend`** | Depends on video mode being set to BGFX. Vulkan is better, when supported.\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `xegs.bgfxshaders`** | Apply a post-processing effect.\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, CRT Geom Deluxe (RGB) `crt-geom-deluxe-rgb`, CRT Geom Deluxe (Composite) `crt-geom-deluxe-composite`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `xegs.switchres`** | Allows the use of switchres profiles if present.\\ => Off `0`, On `1`. |
| **VERTICAL ROTATION (TATE) `xegs.rotation`** | Rotates screen by 90 degrees. Intended for rotating displays.\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ARTWORK CROP `xegs.artworkcrop`** | Crop artwork to only unused space, keeping the game as large as possible.\\ => Off (Default) `0`, On `1`. |
| **ALT DPAD MODE `xegs.altdpad`** | If the D-Pad is oriented incorrectly for your controller.\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |
| **CUSTOM MAME CONFIG `xegs.customcfg`** | Set system-wide controls via MAME menu\\ => On `1`, Off `0`. |
| Settings specific to `xegs` ||
| **SOFTWARE LIST `xegs.softList`** | Use MAME software lists to identify ROM\\ => Don't Use (Default) `none`, Atari XE Game System cartridges `xegs`, Atari 400 / 800 floppy disks `a800_flop`. |
| **MEDIA TYPE `xegs.altromtype`** | Type of ROM file to load.\\ => Cartridge `cart`, Disk (Drive 1) `flop1`, Disk (Drive 2) `flop2`, Disk (Drive 3) `flop3`, Disk (Drive 4) `flop4`. |
| **UI KEYS `xegs.enableui`** | Toggle with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |
| **CUSTOM GAME CONFIG `xegs.pergamecfg`** | Enable per-game custom configuration via MAME menu.\\ => On `1`, Off `0`. |

## Controls
Here are the default Atari XE Game System's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).