# CD-i

**Source:** https://wiki.batocera.org/systems:cdi  
**Last fetched:** 2025-12-06 16:18:47

---

This article needs some TLC. Read at your own risk.

# CD-i
The Compact Disc Interactive (CD-i) is an interactive multimedia console and format standard developed in a joint effort by Philips, Sony and Magnavox. It was released in 1990.

Because it was more a standard than just a console, it was possible for multiple manufacturers to make their own version of "CD-i" player, such as integrating a player into a television set itself, expansion modules for certain computers, or just reboxings with different brandings.

Unlike the traditional CD-ROM players of the time, CD-i required a dedicated Motorola 68000-based CPU to run its own operating system called Compact Disc - Real Time Operating System (CD-RTOS).

Although many types of media were produced for the CD-i, it is most well known for its less-than-scrupulous video games. Such as the infamous ["we can't call these games The Legend of X" incident](https://en.wikipedia.org/wiki/Link:_The_Faces_of_Evil_and_Zelda:_The_Wand_of_Gamelon).

[Here's an interesting blog centered around the CD-i, "The World of CD-i".](https://www.theworldofcdi.com/)

This system scrapes metadata for the "cdi" group(s) and loads the `cdi` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [MAME](#mame)
- **Folder:** `/userdata/roms/cdi`
- **Accepted ROM formats:** `.chd`, `.cue`, `.toc`, `.nrg`, `.gdi`, `.iso`, `.cdr`

## BIOS
Requires MAME BIOS file `cdimono1.zip` or `.7z` in either the `roms/cdi` or BIOS folder.

MD5: 3d20cf7550f1b723158b42a1fd5bac62

## ROMs
Place your CD-i ROMs in `/userdata/roms/cdi`.

## Emulators
### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `cdi.videomode`, `cdi.decoration`, `cdi.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **VIDEO MODE `cdi.video`** | BGFX for post-processing, accel/opengl for raw image.\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX GRAPHICS API `cdi.bgfxbackend`** | Depends on video mode being set to BGFX. Vulkan is better, when supported.\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `cdi.bgfxshaders`** | Apply a post-processing effect.\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `cdi.switchres`** | Allows the use of switchres profiles if present.\\ => Off `0`, On `1`. |
| **VERTICAL ROTATION (TATE) `cdi.rotation`** | Rotates screen by 90 degrees. Intended for rotating displays.\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ALT DPAD MODE `cdi.altdpad`** | If the D-Pad is oriented incorrectly for your controller.\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |

## Controls
Here are the default CD-i's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For problems with MAME specifically, there are some tips on the [troubleshooting section on MAME's system page.](systems:mame#troubleshooting)

For further troubleshooting, refer to the [generic support pages](:support).