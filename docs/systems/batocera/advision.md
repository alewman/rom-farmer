# Adventure Vision

**Source:** https://wiki.batocera.org/systems:advision  
**Last fetched:** 2025-12-06 16:18:31

---

This article needs some TLC. Read at your own risk.

# Adventure Vision
The Adventure Vision is a second-generation console developed by Entex Industries. It was released in 1982.

The monitor, game controls, and computer hardware are all contained within a single portable unit. Despite being technically portable, most people opted to use its built-in AC adapter (it ate through batteries and was unwieldy to actually move about).

It built-in monitor utilized a single vertical line of 40 red LEDs and a rapidly spinning mechanical motor to create its images. A similar technique would later be used by Nintendo with the 1995 [Virtual Boy](systems:virtualboy).

It features a stellar library of 4 games, all arcade ports. It was discontinued a year later.

This system scrapes metadata for the "advision" group and loads the `advision` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [MAME](#mame)
- **Folder:** `/userdata/roms/advision`
- **Accepted ROM formats:** `.bin`, `.zip`, `.7z`

## BIOS
Requires MAME BIOS file `advision.zip` or `.7z` in either advision or BIOS folder.

## ROMs
Place your Adventure Vision ROMs in `/userdata/roms/advision`.

## Emulators
### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `advision.videomode`, `advision.decoration`, `advision.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **GRAPHICS BACKEND `advision.video`** | Choose your graphics rendering\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX BACKEND `advision.bgfxbackend`** | Choose your graphics API\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `advision.bgfxshaders`** | Apply a particular visual effect\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `advision.switchres`** | CRT monitor SwitchRes support\\ => Off `0`, On `1`. |
| **TATE MODE `advision.rotation`** | Rotating display to vertical mode rendering\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ALT DPAD MODE `advision.altdpad`** | If the D-Pad does not work properly\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |

## Controls
When seated on a table, the console is surprisingly ergonomic. It features buttons on both sides of the control panel to facilitate both right and left-handed users.

Here are the default Adventure Vision's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For problems with MAME specifically, there are some tips on the [troubleshooting section on MAME's system page.](systems:mame#troubleshooting)

For further troubleshooting, refer to the [generic support pages](:support).