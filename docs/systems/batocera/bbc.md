# BBC Micro

**Source:** https://wiki.batocera.org/systems:bbc  
**Last fetched:** 2025-12-06 16:18:44

---

# BBC Micro
The BBC Micro (a.k.a. the BBC Microcomputer System/Beeb for short) is a series of computers developed by Acorn Electronics. The first model was released in 1981, and the last model was discontinued in 1994. The first model, Model A, retailed for £235 UK pounds (£946.05 in 2021; $1,248 USD). Notable titles includes [Elite](wp>Elite_(video_game)), Starship Command and [Granny's Garden](wp>Granny%27s_Garden).

Nine models use the BBC brand, with the first six being referred to generally as the "BBC Micro" and the latter models being referred to as the "BBC Master". Software was generally incompatible between the newer and later models.

The "BBC Micro" computers include the:
- Model A
- Model B
- B+64
- B+128

The "BBC Master" computers include the:
- Master 128
- Master Turbo
- Master AIV
- Master ET
- Master 512

The BBC spearheaded the computer literacy project launched by the BBC following a documentary in which Dr. Christopher Evans predicts the coming of the computer revolution and its affects on the United Kingdom.

Designed with an emphasis on education, the BBR Micro line was notable for how robust it was and the high quality of its operating system. It was adopted by most schools in the UK during its prime, making it fairly recognizable to any UK students that did their tutelage during the late 80s/early 90s. It also had moderate success in the home computer market in the UK, North America and West Germany.

The computers were compatible with many types of peripherals, most notably an optical pen, analog controls and a digital joystick.

This system scrapes metadata for the "bbc" group and loads the `bbc` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [MAME](#mame)
- **Folder:** `/userdata/roms/bbc`
- **Accepted ROM formats:** `.mfi`, `.dfi`, `.hfe`, `.mfm`, `.td0`, `.imd`, `.d77`, `.d88`, `.1dd`, `.cqm`, `.cqi`, `.dsk`, `.ima`, `.img`, `.ufi`, `.360`, `.ipf`, `.ssd`, `.bbc`, `.dsd`, `.adf`, `.ads`, `.adm`, `.adl`, `.fsd`, `.wav`, `.tap`, `.bin`, `.zip`, `.7z`

## BIOS
Requires MAME BIOS files `bbcb.zip`, `bbc_acorn8271.zip`, & `saa5050.zip` or `*.7z` in either the `roms/bbc` or BIOS folder.

In order to get sound for certain games, sample pack `bbc.zip` can be placed in the `bios/mame/samples` folder.

## ROMs
Place your BBC Micro ROMs in `/userdata/roms/bbc`.

## Emulators
### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `bbc.videomode`, `bbc.decoration`, `bbc.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **VIDEO MODE `bbc.video`** | BGFX for post-processing, accel/opengl for raw image.\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX GRAPHICS API `bbc.bgfxbackend`** | Depends on video mode being set to BGFX. Vulkan is better, when supported.\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `bbc.bgfxshaders`** | Apply a post-processing effect.\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `bbc.switchres`** | Allows the use of switchres profiles if present.\\ => Off `0`, On `1`. |
| **VERTICAL ROTATION (TATE) `bbc.rotation`** | Rotates screen by 90 degrees. Intended for rotating displays.\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ALT DPAD MODE `bbc.altdpad`** | If the D-Pad is oriented incorrectly for your controller.\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |
| **SPECIAL CONTROL LAYOUTS `bbc.altlayout`** | Controls for 5/6 button games and other unique controls\\ => Default Only `0`, Street Fighter (SNES) `1`, Street Fighter (Modern) `4`, Mortal Kombat (SNES) `2`, Killer Instinct (SNES) `3`, Genesis 6-Button (Retroarch) `5`, Neo Geo (Neo Geo Mini Pad) `6`, Neo Geo (Neo Geo CD Pad) `7`, Neo Geo (Offset Fightstick) `8`, Twin Stick with Triggers `9`, Rotated 4-Way Stick (Q*Bert) `10`. |
| Settings specific to `bbc` ||
| **MEDIA TYPE `bbc.altromtype`** | Type of ROM file to load.\\ => Cassette `cass`, ROM (Slot 1) `rom1`, ROM (Slot 2) `rom2`, ROM (Slot 3) `rom3`, ROM (Slot 4) `rom4`, Disk (Drive 1) `flop1`, Disk (Drive 2) `flop2`. |
| **UI KEYS `bbc.enableui`** | Open with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |

## Controls
The BBC Micro had a wide variety of accessories and thus methods of controller inputs.

Which ones can we emulate?

Here are the default BBC Micro's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For problems with MAME specifically, there are some tips on the [troubleshooting section on MAME's system page.](systems:mame#troubleshooting)

For further troubleshooting, refer to the [generic support pages](:support).