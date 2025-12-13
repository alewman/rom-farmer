# Tomy Tutor

**Source:** https://wiki.batocera.org/systems:tutor  
**Last fetched:** 2025-12-06 16:19:55

---

This article needs some TLC. Read at your own risk.

# Tomy Tutor
The Tomy Tutor (a.k.a. Pyūta, ぴゅう太, Grandstand Tutor) is a computer developed by Tomy. It was released in Japan in 1983, and in the UK and North America the next year.

The system itself is similar to the Texas Instruments TI-99/4A. The system had moderate success in Japan, advertising itself as a children's learning computer (despite its more sophisticated 16-bit CPU compared to competitors at the time) and being sold primarily to elementary and junior high school students. However, when the cheaper and more accessible [console that shall not be named](systems:nes) was released later that year, sales dropped dramatically. In the UK and US, the Tutor struggled to compete against the [ZX Spectrum](systems:zxspectrum) and the [Commodore 64](systems:c64).

This system scrapes metadata for the "tutor" group and loads the `tutor` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [MAME](#mame)
- **Folder:** `/userdata/roms/tutor`
- **Accepted ROM formats:** `.bin`, `.wav`, `.zip`, `.7z`

## BIOS
Requires MAME BIOS file `tutor.zip` or `*.7z` in either `roms/tutor` or the BIOS folder.

## ROMs
Place your Tomy Tutor ROMs in `/userdata/roms/tutor`.

The Tutor used both cartridges and cassettes for its media.

## Emulators
### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `tutor.videomode`, `tutor.decoration`, `tutor.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **VIDEO MODE `tutor.video`** | BGFX for post-processing, accel/opengl for raw image.\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX GRAPHICS API `tutor.bgfxbackend`** | Depends on video mode being set to BGFX. Vulkan is better, when supported.\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `tutor.bgfxshaders`** | Apply a post-processing effect.\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `tutor.switchres`** | Allows the use of switchres profiles if present.\\ => Off `0`, On `1`. |
| **VERTICAL ROTATION (TATE) `tutor.rotation`** | Rotates screen by 90 degrees. Intended for rotating displays.\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ALT DPAD MODE `tutor.altdpad`** | If the D-Pad is oriented incorrectly for your controller.\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |
| **SPECIAL CONTROL LAYOUTS `tutor.altlayout`** | Controls for 5/6 button games and other unique controls\\ => Default Only `0`, Street Fighter (SNES) `1`, Street Fighter (Modern) `4`, Mortal Kombat (SNES) `2`, Killer Instinct (SNES) `3`, Genesis 6-Button (Retroarch) `5`, Neo Geo (Neo Geo Mini Pad) `6`, Neo Geo (Neo Geo CD Pad) `7`, Neo Geo (Offset Fightstick) `8`, Twin Stick with Triggers `9`, Rotated 4-Way Stick (Q*Bert) `10`. |
| Settings specific to `tutor` ||
| **MEDIA TYPE `tutor.altromtype`** | Type of ROM file to load.\\ => Cassette `cass`, Cartridge `cart`. |
| **UI KEYS `tutor.enableui`** | Open with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |

## Starting a game
To get through the loading menu, `[R1]` will move down and  will select.

## Controls
Here are the default Tomy Tutor's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For problems with MAME specifically, there are some tips on the [troubleshooting section on MAME's system page.](systems:mame#troubleshooting)

For further troubleshooting, refer to the [generic support pages](:support).