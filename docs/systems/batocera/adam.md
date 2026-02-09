# Coleco ADAM

**Source:** https://wiki.batocera.org/systems:adam  
**Last fetched:** 2025-12-06 16:18:31

---

This article needs some TLC. Read at your own risk.

# Coleco ADAM
The Coleco ADAM is home computer developed by Coleco. It was released in October 1983, retailing for $725 USD ($1,883.84 in 2021). [Here's a cool article about it on oldcomputers.net.](http://oldcomputers.net/adam.html)

The ADAM wasn't particularly successful, due to its early production problems, and was discontinued just over a year later in January 1985.

A weaker version of it was also featured as an expansion module to the [ColecoVision](systems:colecovision) that converts the videogame console into a full-blown home computer.

This system scrapes metadata for the "adam" group and loads the `adam` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [MAME](#mame)
- **Folder:** `/userdata/roms/adam`
- **Accepted ROM formats:** `.wav`, `.ddp`, `.mfi`, `.dfi`, `.hfe`, `.mfm`, `.td0`, `.imd`, `.d77`, `.d88`, `.1dd`, `.cqm`, `.cqi`, `.dsk`, `.rom`, `.col`, `.bin`, `.zip`, `.7z`

## BIOS
Requires the following MAME BIOS files as ZIP or 7Z in the `roms/adam` or BIOS folder:
`adam`, `adam_ddp`, `adam_fdc`, `adam_kb`, & `adam_prn`

## ROMs
Place your Coleco ADAM ROMs in `/userdata/roms/adam`.

## Emulators
### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `adam.videomode`, `adam.decoration`, `adam.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **VIDEO MODE `adam.video`** | BGFX for post-processing, accel/opengl for raw image.\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX GRAPHICS API `adam.bgfxbackend`** | Depends on video mode being set to BGFX. Vulkan is better, when supported.\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `adam.bgfxshaders`** | Apply a post-processing effect.\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `adam.switchres`** | Allows the use of switchres profiles if present.\\ => Off `0`, On `1`. |
| **VERTICAL ROTATION (TATE) `adam.rotation`** | Rotates screen by 90 degrees. Intended for rotating displays.\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ALT DPAD MODE `adam.altdpad`** | If the D-Pad is oriented incorrectly for your controller.\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |
| **SPECIAL CONTROL LAYOUTS `adam.altlayout`** | Controls for 5/6 button games and other unique controls\\ => Default Only `0`, Street Fighter (SNES) `1`, Street Fighter (Modern) `4`, Mortal Kombat (SNES) `2`, Killer Instinct (SNES) `3`, Genesis 6-Button (Retroarch) `5`, Neo Geo (Neo Geo Mini Pad) `6`, Neo Geo (Neo Geo CD Pad) `7`, Neo Geo (Offset Fightstick) `8`, Twin Stick with Triggers `9`, Rotated 4-Way Stick (Q*Bert) `10`. |
| Settings specific to `adam` ||
| **MEDIA TYPE `adam.altromtype`** | Type of ROM file to load.\\ => Cassette 1 `cass1`, Cassette 2 `cass2`, Disk (Drive 1) `flop1`, Disk (Drive 2) `flop2`, Cartridge (Slot 1) `cart1`, Cartridge (Slot 2) `cart2`, Cartridge (Slot 3) `cart3`, Cartridge (Slot 4) `cart4`. |
| **UI KEYS `adam.enableui`** | Open with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |

## Controls
Here are the default Coleco ADAM's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For problems with MAME specifically, there are some tips on the [troubleshooting section on MAME's system page.](systems:mame#troubleshooting)

For further troubleshooting, refer to the [generic support pages](:support).