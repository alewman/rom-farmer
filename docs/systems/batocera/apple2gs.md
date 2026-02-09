# Apple IIGS

**Source:** https://wiki.batocera.org/systems:apple2gs  
**Last fetched:** 2025-12-06 16:18:37

---

# Apple IIGS
About halfway through the life of the Apple ][ family line, Apple released the Apple IIGS which was a significant change in hardware to the previous Apple 8-bit computers, using a 16-bit 65C816 microprocessor, 256KB or 1MB of RAM (expandable up to 1MB) and the highest resolution display (up to 640x200) and state-of-the-art sound capabilities with the Ensoniq ES5503 DOC 8-bit wavetable synthesis sound chip. Among all the other computers in the line, the Apple IIGS remained the most performant of the bunch, and for this reason it is usually the "default" system that Apple ][ emulators will use for running its software.

However, the Apple IIGS was only around 95% backwards compatible with software designed for the original Apple ][ computers.

This system scrapes metadata for the "apple2gs" group and loads the `apple2gs` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.nib`, `.do`, `.po`, `.dsk`, `.mfi`, `.dfi`, `.rti`, `.edd`, `.woz`, `.wav`, `.zip`, `.7z`
- **Folder:** `/userdata/roms/apple2gs`

| Emulators | Accepted ROM formats |
| [libretro: mame](#libretro:_mame) | `.nib`, `.do`, `.po`, `.dsk`, `.mfi`, `.dfi`, `.rti`, `.edd`, `.woz`, `.wav`, `.zip`, `.7z` |
| [MAME](#mame) | `.nib`, `.do`, `.po`, `.dsk`, `.mfi`, `.dfi`, `.rti`, `.edd`, `.woz`, `.wav`, `.zip`, `.7z` |
| [GSplus](#gsplus) | `.nib`, `.do`, `.po`, `.dsk` |

## BIOS
| MD5 checksum | Share file path | Description |
| `4431aea380185e3f509285540d7cb418` | `bios/apple2e.zip` | |
| `e6d453d8738e6df4f73df8c8051df3e8` | `bios/apple2e.zip` | |
| `72924019cf1719765e4fde35e59c1c7d` | `bios/apple2e.zip` | |
| `0b150f4bfa090770a866cc5d214703f4` | `bios/apple2e.zip` | |
| `2020aa1413ff77fe29353f3ee72dc295` | `bios/a2diskiing.zip` | |
| `95b91e4a2fe7d6f13d353ba1827d37f9` | `bios/votrax.zip` | |
| `5f1be0c1cdff26f5956eef9643911886` | `bios/d2fdc.zip` | |

## ROMs
Place your Apple IIGS ROMs in `/userdata/roms/apple2gs`.

## Emulators
### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: mame
##### libretro: mame configuration
Standardized features for this core: `apple2.autosave`, `apple2.netplay`
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **OVERCLOCK (UNSTABLE) `global.mame_cpu_overclock`** | Enhancement. Reduces system slowdown. Causes issues in some games.\\ => default `default`, 30 `30`, 35 `35`, 40 `40`, 45 `45`, 50 `50`, 55 `55`, 60 `60`, 65 `65`, 70 `70`, 75 `75`, 80 `80`, 85 `85`, 90 `90`, 95 `95`, 100 `100`, 105 `105`, 110 `110`, 115 `115`, 120 `120`, 125 `125`, 130 `130`, 135 `135`, 140 `140`, 145 `145`, 150 `150`. |
| **RENDERING RESOLUTION `global.mame_altres`** | Enhancement. Increase the rendering resolution. Makes 3D objects clearer.\\ => 640x480 `640x480`, 800x600 `800x600`, 960x720 `960x720`, 1024x768 `1024x768`, 1280x720 `1280x720`, 1600x800 `1600x800`, 1920x1080 `1920x1080`, 2560x1440 `2560x1440`, 3840x2160 `3840x2160`. |
| **SPECIAL CONTROL LAYOUTS `global.altlayout`** | Controls for 5/6 button games and other unique controls\\ => Default Only `default`, SNES Style `snes`, Genesis/Megadrive Style `megadrive`, Modern Fightstick Style `fightstick`, Neo Geo Mini Pad `neomini`, Neo Geo CD Pad `neocd`, Twin Stick with Triggers `twinstick`, Rotated 4-Way Stick (Q*Bert) `qbert`. |
| **HIGH SCORE PLUGIN `global.hiscoreplugin`** | Emable or disable high score saving\\ => Enabled (Default) `1`, Disabled `0`. |
| **COIN SOUND PLUGIN `global.coindropplugin`** | Play a coin drop sound effect when an insert coin button is pressed\\ => Enabled `1`, Disabled (Default) `0`. |
| **SHARE MAME ARTWORK `global.sharemameart`** | Use the same art paths as standalone MAME - not recommended if using decorations or shaders.\\ => On (Default) `1`, Off `0`. |
| **CROP ARTWORK `global.artworkcrop`** | Crop MAME artwork to maximize the game screen and only fill unused space.\\ => On (Default) `1`, Off `0`. |
| **CUSTOM MAME CONFIG `global.customcfg`** | Set system-wide controls via MAME menu\\ => On `1`, Off `0`. |
| **OFF-SCREEN RELOAD BUTTON `global.offscreenreload`** | Set gun button 2 to reload.\\ => On `1`, Off (Default) `0`. |
| Settings specific to apple2 ||
| **SOFTWARE LIST `apple2.softList`** | Use MAME software lists to identify ROM\\ => Don't Use (Default) `none`, Apple II cleanly cracked disks `apple2_flop_clcracked`, Apple II miscellaneous disks `apple2_flop_misc`, Apple II original disks `apple2_flop_orig`. |
| **MEDIA TYPE `apple2.altromtype`** | Type of ROM file to load.\\ => Cassette `cass`, Disk (Drive 1) `flop1`, Disk (Drive 2) `flop2`. |
| **UI KEYS `apple2.enableui`** | Toggle with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |
| **CUSTOM GAME CONFIG `apple2.pergamecfg`** | Enable per-game custom configuration via MAME menu.\\ => On `1`, Off `0`. |

### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `apple2.videomode`, `apple2.padtokeyboard`, `apple2.videomode`, `apple2.bezel`, `apple2.bezel_stretch`, `apple2.hud`, `apple2.hud_corner`, `apple2.bezel.tattoo`, `apple2.bezel.tattoo_corner`, `apple2.bezel.tattoo_file`, `apple2.bezel.resize_tattoo`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **VIDEO MODE `apple2.video`** | BGFX for post-processing, accel/opengl for raw image.\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **VSYNC `apple2.vsync`** | Fix screen tearing, but may drop frames.\\ => Off (Default) `0`, On `1`. |
| **BGFX GRAPHICS API `apple2.bgfxbackend`** | Depends on video mode being set to BGFX. Vulkan is better, when supported.\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `apple2.bgfxshaders`** | Apply a post-processing effect.\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, CRT Geom Deluxe (RGB) `crt-geom-deluxe-rgb`, CRT Geom Deluxe (Composite) `crt-geom-deluxe-composite`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `apple2.switchres`** | Allows the use of switchres profiles if present.\\ => Off `0`, On `1`. |
| **VERTICAL ROTATION (TATE) `apple2.rotation`** | Rotates screen by 90 degrees. Intended for rotating displays.\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ARTWORK CROP `apple2.artworkcrop`** | Crop artwork to only unused space, keeping the game as large as possible.\\ => Off (Default) `0`, On `1`. |
| **CUSTOM MAME CONFIG `apple2.customcfg`** | Set system-wide controls via MAME menu\\ => On `1`, Off `0`. |
| **DATA PLUGIN `apple2.dataplugin`** | Make game history, setup instructions, and special moves viewable in the menu\\ => Enabled `1`, Disabled (Default) `0`. |
| **OFF-SCREEN RELOAD BUTTON `apple2.offscreenreload`** | Set gun button 2 to reload.\\ => On `1`, Off (Default) `0`. |
| Settings specific to `apple2` ||
| **SOFTWARE LIST `apple2.softList`** | Use MAME software lists to identify ROM\\ => Don't Use (Default) `none`, Apple II cleanly cracked disks `apple2_flop_clcracked`, Apple II miscellaneous disks `apple2_flop_misc`, Apple II original disks `apple2_flop_orig`. |
| **MEDIA TYPE `apple2.altromtype`** | Type of ROM file to load.\\ => Cassette `cass`, Disk (Drive 1) `flop1`, Disk (Drive 2) `flop2`. |
| **UI KEYS `apple2.enableui`** | Toggle with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |
| **CUSTOM GAME CONFIG `apple2.pergamecfg`** | Enable per-game custom configuration via MAME menu.\\ => On `1`, Off `0`. |

### GSplus
[GSplus](https://apple2.gs/plus/) is an open source, cross-platform Apple ][/IIGS emulator, based on the KEGS and GSPort emulators.

>The goals of this project are to make an easier to install and easier to use emulator, and to modernize the overall codebase and emulation platform.
>
>While much work has been done, adding new drivers and features over the past year, it is still in alpha phase. Feel free to download the package for your platform and play around, but beware there are many bugs still.

#### GSplus configuration
Standardized features available to all cores of this emulator: `apple2.videomode`, `apple2.padtokeyboard`, `apple2.decoration`

## Controls
Here are the default Apple IIGS's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).