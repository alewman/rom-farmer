# Mega Duck

**Source:** https://wiki.batocera.org/systems:megaduck  
**Last fetched:** 2025-12-06 16:19:15

---

This article needs some TLC. Read at your own risk.

# Mega Duck
The Mega Duck is a portable developed by Welback Holdings. It was released in 1993.

Also known as:
- Creatronic
- Videojet
- Cougar Boy
- Mega Duck Super Junior Computer
- Super QuiQue

This system scrapes metadata for the "megaduck" group and loads the `megaduck` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [MAME](#mame)
- **Folder:** `/userdata/roms/megaduck`
- **Accepted ROM formats:** `.bin`, `.zip`, `.7z`

## BIOS
No Mega Duck emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Mega Duck ROMs in `/userdata/roms/megaduck`.

## Emulators
### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `megaduck.videomode`, `megaduck.decoration`, `megaduck.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **VIDEO MODE `megaduck.video`** | BGFX for post-processing, accel/opengl for raw image.\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX GRAPHICS API `megaduck.bgfxbackend`** | Depends on video mode being set to BGFX. Vulkan is better, when supported.\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `megaduck.bgfxshaders`** | Apply a post-processing effect.\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `megaduck.switchres`** | Allows the use of switchres profiles if present.\\ => Off `0`, On `1`. |
| **VERTICAL ROTATION (TATE) `megaduck.rotation`** | Rotates screen by 90 degrees. Intended for rotating displays.\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ALT DPAD MODE `megaduck.altdpad`** | If the D-Pad is oriented incorrectly for your controller.\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |

## Controls
Here are the default Mega Duck's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For problems with MAME specifically, there are some tips on the [troubleshooting section on MAME's system page.](systems:mame#troubleshooting)

For further troubleshooting, refer to the [generic support pages](:support).