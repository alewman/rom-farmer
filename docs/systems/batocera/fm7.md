# Fujitsu Micro 7

**Source:** https://wiki.batocera.org/systems:fm7  
**Last fetched:** 2025-12-06 16:18:57

---

This article needs some TLC. Read at your own risk.

# Fujitsu Micro 7
The Fujitsu Micro 7 (FM-7) is a computer developed by Fujitsu. It was released exclusively in Japan and Spain on November 1982, retailing for ¥126,000 Yen ($1,250 USD; $4,216.44 in 2021).

The FM-7 is a stripped down version of the prior FM-8 computer, originally referred to as the "FM-8 Jr.". It primarily competed with the NEC PC-8801 and the Sharp X1 series of computers.

Model list ([list source](https://github.com/MisterTea/MAMEHub/blob/master/Sources/Emulator/src/mess/drivers/fm7.c)):
| Model        | Release | Main CPU       | Sub CPU   | RAM                           |
| FM-8         | 1981-05 | M68A09 @ 1MHz  | M6809     | 64K (main) + 48K (VRAM)       |
| FM-7         | 1982-11 | M68B09 @ 2MHz  | M68B09    | 64K (main) + 48K (VRAM)       |
| FM-NEW7      | 1984-05 | M68B09 @ 2MHz  | M68B09    | 64K (main) + 48K (VRAM)       |
| FM-77        | 1984-05 | M68B09 @ 2MHz  | M68B09E   | 64/256K (main) + 48K (VRAM)   |
| FM-77AV      | 1985-10 | M68B09E @ 2MHz | M68B09    | 128/192K (main) + 96K (VRAM)  |
| FM-77AV20    | 1986-10 | M68B09E @ 2MHz | M68B09    | 128/192K (main) + 96K (VRAM)  |
| FM-77AV40    | 1986-10 | M68B09E @ 2MHz | M68B09    | 192/448K (main) + 144K (VRAM) |
| FM-77AV20EX  | 1987-11 | M68B09E @ 2MHz | M68B09    | 128/192K (main) + 96K (VRAM)  |
| FM-77AV40EX  | 1987-11 | M68B09E @ 2MHz | M68B09    | 192/448K (main) + 144K (VRAM) |
| FM-77AV40SX  | 1988-11 | M68B09E @ 2MHz | M68B09    | 192/448K (main) + 144K (VRAM) |

The only emulator Batocera employs for this system is MAME/MESS's FM-7 core, which is still experimental and lacking documentation. Therefore, emulation of this system can really only be recommended to advanced users.

This system scrapes metadata for the "fm7" group and loads the `fm7` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [MAME](#mame)
- **Folder:** `/userdata/roms/fm7`
- **Accepted ROM formats:** `.wav`, `.t77`, `.mfi`, `.dfi`, `.hfe`, `.mfm`, `.td0`, `.imd`, `.d77`, `.d88`, `.1dd`, `.cqm`, `.cqi`, `.dsk`, `.zip`, `.7z`

## BIOS
Requires MAME BIOS file `fm7.zip` or `*.7z` in either `roms/fm7` or BIOS folder.

Optionally `fm77av.zip` or `*.7z` for FM-77AV support.

## ROMs
Place your Fujitsu Micro 7 ROMs in `/userdata/roms/fm7`.

## Emulators
### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `fm7.videomode`, `fm7.decoration`, `fm7.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **VIDEO MODE `fm7.video`** | BGFX for post-processing, accel/opengl for raw image.\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX GRAPHICS API `fm7.bgfxbackend`** | Depends on video mode being set to BGFX. Vulkan is better, when supported.\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `fm7.bgfxshaders`** | Apply a post-processing effect.\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `fm7.switchres`** | Allows the use of switchres profiles if present.\\ => Off `0`, On `1`. |
| **VERTICAL ROTATION (TATE) `fm7.rotation`** | Rotates screen by 90 degrees. Intended for rotating displays.\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ALT DPAD MODE `fm7.altdpad`** | If the D-Pad is oriented incorrectly for your controller.\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |
| Settings specific to `fm7` ||
| **FM-7 MODEL `fm7.altmodel`** | \\ => FM-7 `fm7`, FM-77AV `fm77av`. |
| **MEDIA TYPE `fm7.altromtype`** | Type of ROM file to load.\\ => Cassette `cass`, Disk (Drive 1) `flop1`, Disk (Drive 2) `flop2`. |
| **UI KEYS `fm7.enableui`** | Open with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |

## Controls
Here are the default FM-7's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For problems with MAME specifically, there are some tips on the [troubleshooting section on MAME's system page.](systems:mame#troubleshooting)

For further troubleshooting, refer to the [generic support pages](:support).