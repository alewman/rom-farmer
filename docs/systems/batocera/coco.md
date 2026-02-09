# TRS-80 Color Computer

**Source:** https://wiki.batocera.org/systems:coco  
**Last fetched:** 2025-12-06 16:18:48

---

This article needs some TLC. Read at your own risk.

# TRS-80 Color Computer
The TRS-80 Color Computer is a computer developed by Tandy Radio Shack. It was released in 1980.

You may also know it as the:
- Tandy Color Computer
- CoCo
- CoCo 2

The TRS-80, without the "Color Computer" part, is a completely different system.

This system scrapes metadata for the "coco" group and loads the `coco` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [MAME](#mame)
- **Folder:** `/userdata/roms/coco`
- **Accepted ROM formats:** `.wav`, `.cas`, `.ccc`, `.rom`, `.zip`, `.7z`

## BIOS
Requires MAME BIOS file coco.zip or .7z in either coco or BIOS folder.

## ROMs
Place your TRS-80 Color Computer ROMs in `/userdata/roms/coco`.

## Emulators
### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `coco.videomode`, `coco.decoration`, `coco.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **VIDEO MODE `coco.video`** | BGFX for post-processing, accel/opengl for raw image.\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX GRAPHICS API `coco.bgfxbackend`** | Depends on video mode being set to BGFX. Vulkan is better, when supported.\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `coco.bgfxshaders`** | Apply a post-processing effect.\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `coco.switchres`** | Allows the use of switchres profiles if present.\\ => Off `0`, On `1`. |
| **VERTICAL ROTATION (TATE) `coco.rotation`** | Rotates screen by 90 degrees. Intended for rotating displays.\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ALT DPAD MODE `coco.altdpad`** | If the D-Pad is oriented incorrectly for your controller.\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |
| **SPECIAL CONTROL LAYOUTS `coco.altlayout`** | Controls for 5/6 button games and other unique controls\\ => Default Only `0`, Street Fighter (SNES) `1`, Street Fighter (Modern) `4`, Mortal Kombat (SNES) `2`, Killer Instinct (SNES) `3`, Genesis 6-Button (Retroarch) `5`, Neo Geo (Neo Geo Mini Pad) `6`, Neo Geo (Neo Geo CD Pad) `7`, Neo Geo (Offset Fightstick) `8`, Twin Stick with Triggers `9`, Rotated 4-Way Stick (Q*Bert) `10`. |
| Settings specific to `coco` ||
| **MEDIA TYPE `coco.altromtype`** | Type of ROM file to load.\\ => Cassette `cass`, Cartridge `cart`. |
| **UI KEYS `coco.enableui`** | Open with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |

## Controls
Here are the default TRS-80 Color Computer's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For problems with MAME specifically, there are some tips on the [troubleshooting section on MAME's system page.](systems:mame#troubleshooting)

For further troubleshooting, refer to the [generic support pages](:support).