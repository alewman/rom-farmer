# PDP-1

**Source:** https://wiki.batocera.org/systems:pdp1  
**Last fetched:** 2025-12-06 16:19:33

---

This article needs some TLC. Read at your own risk.

# PDP-1
The PDP-1 is a computer developed by Digital Equipment Corporation. It was released in 1961.

This system scrapes metadata for the "pdp1" group(s) and loads the `pdp1` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.zip`, `.7z`, `.tap`, `.rim`, `.drm`
- **Folder:** `/userdata/roms/pdp1`

| Emulators |
| [libretro: mame](#libretro:_mame) |
| [MAME](#mame) |

## BIOS
No PDP-1 emulator in Batocera needs a BIOS file to run.

## ROMs
Place your PDP-1 ROMs in `/userdata/roms/pdp1`.

Use Control-Enter or Start to start after loading. Loading may take some time,
if the green lights are blinking, it is loading.

Spacewar is two player only, if you only have one controller connected, it will control both ships.

## Emulators
### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: mame
##### libretro: mame configuration
Standardized features for this core: `pdp1.autosave`, `pdp1.netplay`, `pdp1.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **OVERCLOCK (UNSTABLE) `global.mame_cpu_overclock`** | Enhancement. Reduces system slowdown. Causes issues in some games.\\ => default `default`, 30 `30`, 35 `35`, 40 `40`, 45 `45`, 50 `50`, 55 `55`, 60 `60`, 65 `65`, 70 `70`, 75 `75`, 80 `80`, 85 `85`, 90 `90`, 95 `95`, 100 `100`, 105 `105`, 110 `110`, 115 `115`, 120 `120`, 125 `125`, 130 `130`, 135 `135`, 140 `140`, 145 `145`, 150 `150`. |
| **RENDERING RESOLUTION `global.mame_altres`** | Enhancement. Increase the rendering resolution. Makes 3D objects clearer.\\ => 640x480 `640x480`, 800x600 `800x600`, 960x720 `960x720`, 1024x768 `1024x768`, 1280x720 `1280x720`, 1600x800 `1600x800`, 1920x1080 `1920x1080`, 2560x1440 `2560x1440`, 3840x2160 `3840x2160`. |
| **SPECIAL CONTROL LAYOUTS `global.altlayout`** | Controls for 5/6 button games and other unique controls\\ => Default Only `default`, SNES Style `snes`, Genesis/Megadrive Style `megadrive`, Modern Fightstick Style `fightstick`, Neo Geo Mini Pad `neomini`, Neo Geo CD Pad `neocd`, Twin Stick with Triggers `twinstick`, Rotated 4-Way Stick (Q*Bert) `qbert`. |
| **HIGH SCORE PLUGIN `global.hiscoreplugin`** | Enable or disable high score saving\\ => Enabled (Default) `1`, Disabled `0`. |
| **COIN SOUND PLUGIN `global.coindropplugin`** | Play a coin drop sound effect when an insert coin button is pressed\\ => Enabled `1`, Disabled (Default) `0`. |
| **SHARE MAME ARTWORK `global.sharemameart`** | Use the same art paths as standalone MAME - not recommended if using decorations or shaders.\\ => On (Default) `1`, Off `0`. |
| **CROP ARTWORK `global.artworkcrop`** | Crop MAME artwork to maximize the game screen and only fill unused space.\\ => On (Default) `1`, Off `0`. |
| **CUSTOM CONFIG `global.customcfg`** | Use a custom MAME config, do not overwrite config on launch.\\ => On `1`, Off (Default) `0`. |
| **OFF-SCREEN RELOAD BUTTON `global.offscreenreload`** | Set gun button 2 to reload.\\ => On `1`, Off (Default) `0`. |
| Settings specific to pdp1 ||
| **SOFTWARE LIST `pdp1.softList`** | Use MAME software lists to identify ROM\\ => Don't Use (Default) `none`, PDP-1 Paper Tape Reader Images `pdp1_ptp`. |
| **UI KEYS `pdp1.enableui`** | Toggle with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |
| **CUSTOM GAME CONFIG `pdp1.pergamecfg`** | Enable per-game custom configuration via MAME menu.\\ => On `1`, Off `0`. |

### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `pdp1.videomode`, `pdp1.padtokeyboard`, `pdp1.powermode`, `pdp1.tdp`, `pdp1.videomode`, `pdp1.bezel`, `pdp1.bezel_stretch`, `pdp1.hud`, `pdp1.hud_corner`, `pdp1.bezel.tattoo`, `pdp1.bezel.tattoo_corner`, `pdp1.bezel.tattoo_file`, `pdp1.bezel.resize_tattoo`, `pdp1.use_guns`, `pdp1.use_wheels`, `pdp1.wheel_rotation`, `pdp1.wheel_deadzone`, `pdp1.wheel_midzone`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **VIDEO MODE `pdp1.video`** | BGFX for post-processing, accel/opengl for raw image.\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **VSYNC `pdp1.vsync`** | Fix screen tearing, but may drop frames.\\ => Off (Default) `0`, On `1`. |
| **BGFX GRAPHICS API `pdp1.bgfxbackend`** | Depends on video mode being set to BGFX.\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `pdp1.bgfxshaders`** | Apply a post-processing effect.\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, CRT Geom Deluxe (RGB) `crt-geom-deluxe-rgb`, CRT Geom Deluxe (Composite) `crt-geom-deluxe-composite`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `pdp1.switchres`** | Allows the use of switchres profiles if present.\\ => Off `0`, On `1`. |
| **MULTISCREENS `pdp1.multiscreens`** | Play this game on several screens (if available)\\ => Off `0`, On `1`. |
| **VERTICAL ROTATION (TATE) `pdp1.rotation`** | Rotates screen by 90 degrees. Intended for rotating displays.\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ARTWORK CROP `pdp1.artworkcrop`** | Crop artwork to only unused space, keeping the game as large as possible.\\ => Off (Default) `0`, On `1`. |
| **CUSTOM MAME CONFIG `pdp1.customcfg`** | Set system-wide controls via MAME menu\\ => On `1`, Off `0`. |
| **DATA PLUGIN `pdp1.dataplugin`** | Make game history, setup instructions, and special moves viewable in the menu\\ => Enabled `1`, Disabled (Default) `0`. |
| **OFF-SCREEN RELOAD BUTTON `pdp1.offscreenreload`** | Set gun button 2 to reload.\\ => On `1`, Off (Default) `0`. |
| **CROSSHAIR `pdp1.mame_crosshair`** | None\\ => Disabled (Default) `disabled`, Enabled `enabled`, When moving `onmove`. |
| Settings specific to `pdp1` ||
| **SOFTWARE LIST `pdp1.softList`** | Use MAME software lists to identify ROM\\ => Don't Use (Default) `none`, PDP-1 Paper Tape Reader Images `pdp1_ptp`. |
| **UI KEYS `pdp1.enableui`** | Toggle with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |
| **CUSTOM GAME CONFIG `pdp1.pergamecfg`** | Enable per-game custom configuration via MAME menu.\\ => On `1`, Off `0`. |

## Controls
Here are the default PDP-1's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).