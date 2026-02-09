# Bally Astrocade

**Source:** https://wiki.batocera.org/systems:astrocde  
**Last fetched:** 2025-12-06 16:18:39

---

This article needs some TLC. Read at your own risk.

# Bally Astrocade
The Bally Astrocade (a.k.a. Bally Home Library Computer, Bally Professional Arcade or Bally ABA-1000) is a console developed by Bally Manufacturing. It was released in April 1978 by mail order as the Bally Professional Arcade.

Bally only marketed it for a short time before deciding to exit the market. The rights were later picked up by Astrovision in 1982, who re-released it as the Astrocade and sold it until around 1984.

It was notable for its very powerful graphical capabilities, however it was also complicated to program for and lack certain programming features such as sprites.

This system scrapes metadata for the "astrocde" group and loads the `astrocde` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [MAME](#mame)
- **Folder:** `/userdata/roms/astrocde`
- **Accepted ROM formats:** `.bin`, `.zip`, `.7z`

## BIOS
No Astrocade emulator in Batocera needs a BIOS file to run.

Requires MAME BIOS file `astrocde.zip` or `.7z` in either the `roms/astrocde` or BIOS folder.

Where? Be specific.

## ROMs
Place your Bally Astrocade ROMs in `/userdata/roms/astrocde`.

## Emulators
### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `astrocde.videomode`, `astrocde.decoration`, `astrocde.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **GRAPHICS BACKEND `astrocde.video`** | Choose your graphics rendering\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX BACKEND `astrocde.bgfxbackend`** | Choose your graphics API\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `astrocde.bgfxshaders`** | Apply a particular visual effect\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `astrocde.switchres`** | CRT monitor SwitchRes support\\ => Off `0`, On `1`. |
| **TATE MODE `astrocde.rotation`** | Rotating display to vertical mode rendering\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ALT DPAD MODE `astrocde.altdpad`** | If the D-Pad does not work properly\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |
| Settings specific to `astrocde` ||
| **CUSTOM CONFIG `astrocde.pergamecfg`** | Enable per-game custom configuration via MAME menu\\ => On `1`, Off `0`. |

## Controls
Here are the default Bally Astrocade's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For problems with MAME specifically, there are some tips on the [troubleshooting section on MAME's system page.](systems:mame#troubleshooting)

For further troubleshooting, refer to the [generic support pages](:support).