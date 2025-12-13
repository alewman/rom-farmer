# CreatiVision

**Source:** https://wiki.batocera.org/systems:crvision  
**Last fetched:** 2025-12-06 16:18:50

---

This article needs some TLC. Read at your own risk.

# CreatiVision
The CreatiVision is a hybrid computer/videogame console developed by VTech. It was first released in 1982.

The CreatiVision had many different names and was published by different brands across the globe. You may have known it as:
- VTech CreatiVision
- VTech Laser 2001 Home Computer
- Educat 2002
- Dick Smith Wizzard
- FunVision Comp Video Games System
- Hanimex Rameses
- VZ 2000
- Zanussi CreatiVision
- Bente CreatiVision
- Cheryco CreatiVision
- Salora Laser 2001
- Telefunken CreatiVision

This system scrapes metadata for the "crvision" group and loads the `crvision` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [MAME](#mame)
- **Folder:** `/userdata/roms/crvision`
- **Accepted ROM formats:** `.bin`, `.rom`, `.zip`, `.7z`

## BIOS
Requires MAME BIOS file `crvision.zip` or `.7z` in either `crvision` or the BIOS folder.

## ROMs
Place your CreatiVision ROMs in `/userdata/roms/crvision`.

## Emulators
### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `crvision.videomode`, `crvision.decoration`, `crvision.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **GRAPHICS BACKEND `crvision.video`** | Choose your graphics rendering\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX BACKEND `crvision.bgfxbackend`** | Choose your graphics API\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `crvision.bgfxshaders`** | Apply a particular visual effect\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `crvision.switchres`** | CRT monitor SwitchRes support\\ => Off `0`, On `1`. |
| **TATE MODE `crvision.rotation`** | Rotating display to vertical mode rendering\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ALT DPAD MODE `crvision.altdpad`** | If the D-Pad does not work properly\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |
| Settings specific to `crvision` ||
| **MEDIA TYPE `crvision.altromtype`** | Type of ROM file (Cartridge default)\\ => Cartridge `cart`, Cassette `cass`. |
| **CUSTOM CONFIG `crvision.pergamecfg`** | Enable per-game custom configuration via MAME menu\\ => On `1`, Off `0`. |

## Controls

The controls for the CreatiVision are one of the most unique both in design and conceptualization. Instead of using a single controller layout and having games adapt to it, the game would come with a decorative overlay that you would slot into the rails of the controller, covering the membrane buttons. The layout would be unique to that game.

Generally, most games opted to use the top-most and bottom-most buttons for their primary functions, but some others used the sides as well. Batocera assumes a default control scheme that makes most games *playable*, but you are encouraged to remap them as needed on a per-game basis. Most games' overlays can be found at [creatiVemu's software database](http://www.madrigaldesign.it/creativemu/software.php).

Here are the default CreatiVision's controls shown on a [Batocera Retropad](:configure_a_controller):

Remember, this was also a computer, so it uses a non-standard computer keyboard layout underneath. When both controllers are docked in the horizontal position in the console, it resembles the QWERTY keyboard layout. That's why the button labels internally used might be a bit confusing when using it in its game mode.

## Troubleshooting
### Further troubleshooting
For problems with MAME specifically, there are some tips on the [troubleshooting section on MAME's system page.](systems:mame#troubleshooting)

For further troubleshooting, refer to the [generic support pages](:support).