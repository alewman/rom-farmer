# Arcadia 2001

**Source:** https://wiki.batocera.org/systems:arcadia  
**Last fetched:** 2025-12-06 16:18:37

---

# Arcadia 2001
The Arcadia 2001 is a console developed by Emerson. It was released in May 1982, retailing for $99 USD ($283.75 in 2021).

It featured a Signetics 2650 CPU clocked at 1.2MHz, with a Signetics 2637 UVI clocked at 3.58MHz (3.55MHz for PAL) for video output. An on-board beeper is used to produce the sounds for the game.

A total of 35 games were released for the original system during its eighteen month lifespan, with that total rising to 47 if clones are included.

The Arcadia 2001 had over thirty clones and variants, nearly more than the amount of games released for the original system! Most notably, Bandai's Arcadia released in Japan, which featured four exclusive games.

--> You may instead know this system as (click to reveal):#
- Advision Home Arcade
- Arcadia
- Cosmos
- Dynavision
- Educat
- Ekusera
- Hanimex MPT-03
- HMG-2650
- Home Arcade Centre
- Intelligent Game MPT-03
- Intercord XL 2000 System
- Intervision 2001
- ITMC MPT-03
- Leisure Vision
- Leonardo
- Home Entertainment Centre Ch-50
- Ormatu 2001
- Palladium Video-Computer-Game
- Polybrain Video Computer Game
- Poppy MPT-03 Tele Computer Spiel
- Prestige Video Computer Game MPT-03
- Robdajet MPT-03
- Rowtron 2000
- Schmid TVG-2000
- Sheen Home Video Centre 2001
- Soundic MPT-03
- Mr. Altus Das Tele-Gehirn Color
- Tele-Fever
- Tempest MPT-03
- Tobby MPT-03
- Trakton Computer Video Game
- Tryom Video Game Center
- Tunix Home Arcade
- UVI Compu-Game
- Video Master

<--

Unfortunately Arcadia 2001 emulation isn't very well developed/documented, so if issues are encountered with this system it may be difficult or outright impossible to troubleshoot for.

This system scrapes metadata for the "arcadia" group and loads the `arcadia` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [MAME](#mame)
- **Folder:** `/userdata/roms/arcadia`
- **Accepted ROM formats:** `.bin`, `.zip`, `.7z`

## BIOS
No Arcadia 2001 emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Arcadia 2001 ROMs in `/userdata/roms/arcadia`.

## Emulators
### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `arcadia.videomode`, `arcadia.decoration`, `arcadia.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **GRAPHICS BACKEND `arcadia.video`** | Choose your graphics rendering\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX BACKEND `arcadia.bgfxbackend`** | Choose your graphics API\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `arcadia.bgfxshaders`** | Apply a particular visual effect\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `arcadia.switchres`** | CRT monitor SwitchRes support\\ => Off `0`, On `1`. |
| **TATE MODE `arcadia.rotation`** | Rotating display to vertical mode rendering\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ALT DPAD MODE `arcadia.altdpad`** | If the D-Pad does not work properly\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |

| Settings specific to `arcadia` ||
| **CUSTOM CONFIG `arcadia.pergamecfg`** | Enable per-game custom configuration via MAME menu\\ => On `1`, Off `0`. |
## Controls
Here are the default Arcadia 2001's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For problems with MAME specifically, there are some tips on the [troubleshooting section on MAME's system page.](systems:mame#troubleshooting)

For further troubleshooting, refer to the [generic support pages](:support).