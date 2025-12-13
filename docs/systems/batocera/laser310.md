# VTech Laser 310

**Source:** https://wiki.batocera.org/systems:laser310  
**Last fetched:** 2025-12-06 16:19:09

---

This article needs some TLC. Read at your own risk.

# VTech Laser 310
The VTech Laser 310 is a home computer developed by Video Technology. It was released in 1984. A version of this system was also released as the `Dick Smith Electronics VZ-300`. [Here's a cool article about it on oldcomputers.net.](https://www.old-computers.com/museum/computer.asp?c=157)

This system scrapes metadata for the "laser310" group and loads the `laser310` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.vz`, `.wav`, `.cas`, `.zip`, `.7z`
- **Folder:** `/userdata/roms/laser310`
- **BIOS:** `/userdata/bios/laser310.zip`

| Emulators |
| [libretro: MAME](#libretro:_mame) |
| [MAME](#mame) |

## BIOS
| MD5 checksum | Share file path | Description |
| `42c8f9e6c2133ae0e953b89ccbbdb7e2` | `bios/laser310.zip` | `vtechv20.u12`: BASIC V2.0 |
| `f7e5d9a3eb2b57bf5f4e2a4565318a8f` | `bios/laser310.zip` | `vtechv21.u12`: BASIC V2.1 (hack) |

## ROMs
Place your VTech Laser 310 ROMs in `/userdata/roms/laser310/`.

Using snapshot (.vz) files is recommended, as these are binary memory dumps with a simple header, which can be automatically bootstrapped by MAME.  Cassette formats will require keyboard interaction from the user (`CLOAD` followed by the F2 key to start the tape).

## Emulators
### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: mame
##### libretro: mame configuration
Standardized features for this core: `laser310.autosave`, `laser310.netplay`

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
| Settings specific to laser310 ||
| **SOFTWARE LIST `laser310.softList`** | Use MAME software lists to identify ROM\\ => Don't Use (Default) `none`, Dick Smith Electronics VZ-200/300 cassettes `vz_cass`, Dick Smith Electronics VZ-200/300 snapshots `vz_snap`. |
| **MEMORY SLOT `laser310.memslot`** | Choose hardware for the memory expansion slot\\ => Laser 310/VZ-300 16k Memory `laser310_16k`, Laser/VZ 64k Memory (Default) `laser_64k`. |
| **MEDIA TYPE `laser310.altromtype`** | Type of ROM file to load.\\ => Cassette `cass`, Snapshot `snap`. |
| **UI KEYS `laser310.enableui`** | Toggle with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |
| **CUSTOM CONFIG `laser310.pergamecfg`** | Enable per-game custom configuration via MAME menu.\\ => On `1`, Off `0`. |

### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `laser310.videomode`, `laser310.decoration`, `laser310.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **VIDEO MODE `laser310.video`** | BGFX for post-processing, accel/opengl for raw image.\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **VSYNC `laser310.vsync`** | Fix screen tearing, but may drop frames.\\ => Off (Default) `0`, On `1`. |
| **BGFX GRAPHICS API `laser310.bgfxbackend`** | Depends on video mode being set to BGFX. Vulkan is better, when supported.\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `laser310.bgfxshaders`** | Apply a post-processing effect.\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, CRT Geom Deluxe (RGB) `crt-geom-deluxe-rgb`, CRT Geom Deluxe (Composite) `crt-geom-deluxe-composite`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `laser310.switchres`** | Allows the use of switchres profiles if present.\\ => Off `0`, On `1`. |
| **VERTICAL ROTATION (TATE) `laser310.rotation`** | Rotates screen by 90 degrees. Intended for rotating displays.\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ARTWORK CROP `laser310.artworkcrop`** | Crop artwork to only unused space, keeping the game as large as possible.\\ => Off (Default) `0`, On `1`. |
| **CUSTOM MAME CONFIG `laser310.customcfg`** | Set system-wide controls via MAME menu\\ => On `1`, Off `0`. |
| **DATA PLUGIN `laser310.dataplugin`** | Make game history, setup instructions, and special moves viewable in the menu\\ => Enabled `1`, Disabled (Default) `0`. |
| **OFF-SCREEN RELOAD BUTTON `laser310.offscreenreload`** | Set gun button 2 to reload.\\ => On `1`, Off (Default) `0`. |
| Settings specific to `laser310` ||
| **SOFTWARE LIST `laser310.softList`** | Use MAME software lists to identify ROM\\ => Don't Use (Default) `none`, Dick Smith Electronics VZ-200/300 cassettes `vz_cass`, Dick Smith Electronics VZ-200/300 snapshots `vz_snap`. |
| **MEMORY SLOT `laser310.memslot`** | Choose hardware for the memory expansion slot\\ => Laser 310/VZ-300 16k Memory `laser310_16k`, Laser/VZ 64k Memory (Default) `laser_64k`. |
| **MEDIA TYPE `laser310.altromtype`** | Type of ROM file to load.\\ => Cassette `cass`, Snapshot `snap`. |
| **UI KEYS `laser310.enableui`** | Toggle with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |
| **CUSTOM CONFIG `laser310.pergamecfg`** | Enable per-game custom configuration via MAME menu.\\ => On `1`, Off `0`. |

## Controls
The default button mapping for the laser310's controls is as follows::

## Troubleshooting
For problems with MAME specifically, there are some tips on the [troubleshooting section on MAME's system page.](systems:mame#troubleshooting)

For further troubleshooting, refer to the [generic support pages](:support).