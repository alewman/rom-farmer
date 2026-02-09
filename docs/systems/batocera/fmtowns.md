# Fujitsu FM-TOWNS

**Source:** https://wiki.batocera.org/systems:fmtowns  
**Last fetched:** 2025-12-06 16:18:57

---

This article needs some TLC. Read at your own risk.

# Fujitsu FM-TOWNS
The Fujitsu FM-TOWNS is a series of computers developed by Fujitsu between 1989 and 1997. It was exclusively released in Japan.

FM stands for "Fujistu Micro", while the "Towns" was derived from the system's codename "Townes" (referring to Charles Townes, one of the winners of the 1964 Nobel Prize in Physics) used during development. The "e" was dropped to emphasis its pronounciation like "towns" rather than "tow-nes".

The system was known for being technologically superior to its competitors at the time, the [NEC PC-98](systems:pc98) and even some 4th generation videogame consoles, however it struggled to gain the same foothold as the PC-98 did. The ports of arcade games released for the FM-7 were usually the definitive version to have at the time, outside of playing the game on the original arcade hardware itself, making them highly sought after.

In 1993, the [FM Towns Marty](wp>FM_Towns_Marty) was released, which is a game console compatible with the existing FM Towns games.

Eventually, DOS/V support would be added to the computer system, allowing for the booting of other operating systems such as Microsoft's Windows. Over time, Fujitsu would shift its development focus from software coded specifically for the FM Towns and instead making more universally compatible DOS code.

Emulation of this system is still somewhat experimental and only recommended to advanced users, those who might already be familiar with assigned drive letters manually and working the FM Town's Japanese interface.

This system scrapes metadata for the "fmtowns" group and loads the `fmtowns` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.bin`, `.m3u`, `.cue`, `.d88`, `.d77`, `.xdf`, `.iso`, `.chd`, `.toc`, `.nrg`, `.gdi`, `.cdr`, `.mfi`, `.dfi`, `.hfe`, `.mfm`, `.td0`, `.imd`, `.1dd`, `.cqm`, `.cqi`, `.dsk`, `.zip`, `.7z`
- **Folder:** `/userdata/roms/fmtowns`

| Emulators | Accepted ROM formats |
| [libretro: mame](#libretro:_mame) | `.bin`, `.cue`, `.d88`, `.d77`, `.iso`, `.chd`, `.toc`, `.nrg`, `.gdi`, `.cdr`, `.mfi`, `.dfi`, `.hfe`, `.mfm`, `.td0`, `.imd`, `.1dd`, `.cqm`, `.cqi`, `.dsk`, `.zip`, `.7z` |
| [MAME](#mame) | `.bin`, `.cue`, `.d88`, `.d77`, `.iso`, `.chd`, `.toc`, `.nrg`, `.gdi`, `.cdr`, `.mfi`, `.dfi`, `.hfe`, `.mfm`, `.td0`, `.imd`, `.1dd`, `.cqm`, `.cqi`, `.dsk`, `.zip`, `.7z` |
| [tsugaru](#tsugaru) | `.bin`, `.cue`, `.d88`, `.d77`, `.iso` |

## BIOS
| MD5 checksum | Share file path | Description |
| `8fa4e553f28cfc0c30a0a1e589799942` | `bios/fmtowns/FMT_DIC.ROM` | |
| `0585b19930d4a7f4c71bcc8a33746588` | `bios/fmtowns/FMT_DOS.ROM` | |
| `ac0c7021e9bf48ca84b51ab651169a88` | `bios/fmtowns/FMT_F20.ROM` | |
| `b91300e55b70227ce98b59c5f02fa8dd` | `bios/fmtowns/FMT_FNT.ROM` | |
| `86fb6f7280689259f0ca839dd3dd6cde` | `bios/fmtowns/FMT_SYS.ROM` | |
| `6618519b2c104cf9b7e71a48381b44a9` | `bios/fmtmarty.zip` | |
| `75a5c7afb4bc8221bab8cf24db417950` | `bios/fmtmarty.zip` | |
| `34847786d7de94b5d1133c956ab1d75d` | `bios/fmtowns.zip` | |
| `0585b19930d4a7f4c71bcc8a33746588` | `bios/fmtowns.zip` | |
| `eb44f2093f51eb7159f03e170b13af76` | `bios/fmtowns.zip` | |
| `feaf8c5675151e00cfe3ad27673bff29` | `bios/fmtowns.zip` | |
| `8fa4e553f28cfc0c30a0a1e589799942` | `bios/fmtownsux.zip` | |
| `03c8fac9a5f5f5f35fb5de5a5d0d018f` | `bios/fmtownsux.zip` | |
| `b91300e55b70227ce98b59c5f02fa8dd` | `bios/fmtownsux.zip` | |
| `90b5e01d42aaa93e8f4503a5e94e120b` | `bios/fmtownsux.zip` | |
| `1a15f6c1b58ec7e5f850118610a787a7` | `bios/fmtownsux.zip` | |

In case you don't have BIOS files, a free (albeit less compatible) set can be found at [their website](http://ysflight.in.coocan.jp/FM/towns/FreeTOWNS/e.html) as well.

## ROMs
Place your Fujitsu FM-TOWNS ROMs in `/userdata/roms/fmtowns`.

## Emulators
### Tsugaru
[Tsugaru](http://ysflight.in.coocan.jp/FM/towns/Tsugaru/e.html) is a relatively new FM Towns emulation project (started in January of 2020) with a high level of compatibility. System requires are particularly demanding and certain components (notably sound chips) are still experimental.

Check out the compatibility list at the bottom of their [website](http://ysflight.in.coocan.jp/FM/towns/Tsugaru/e.html).

#### Tsugaru configuration
Standardized features available to all cores of this emulator: `fmtowns.videomode`, `fmtowns.padtokeyboard`, `fmtowns.videomode`, `fmtowns.bezel`, `fmtowns.bezel_stretch`, `fmtowns.hud`, `fmtowns.hud_corner`, `fmtowns.bezel.tattoo`, `fmtowns.bezel.tattoo_corner`, `fmtowns.bezel.tattoo_file`, `fmtowns.bezel.resize_tattoo`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **CD-ROM SPEED `fmtowns.cdrom_speed`** | \\ => AUTO (DEFAULT) `auto`, 1X `1`, 2X `2`, 4X `4`, 8X `8`. |
| **FORCE 386DX CPU `fmtowns.386dx`** | Required by some games.\\ => NO (DEFAULT) `0`, YES `1`. |

### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: mame
##### libretro: mame configuration
Standardized features for this core: `fmtowns.autosave`, `fmtowns.netplay`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **OVERCLOCK (UNSTABLE) `global.mame_cpu_overclock`** | Enhancement. Reduces system slowdown. Causes issues in some games.\\ => default `default`, 30 `30`, 35 `35`, 40 `40`, 45 `45`, 50 `50`, 55 `55`, 60 `60`, 65 `65`, 70 `70`, 75 `75`, 80 `80`, 85 `85`, 90 `90`, 95 `95`, 100 `100`, 105 `105`, 110 `110`, 115 `115`, 120 `120`, 125 `125`, 130 `130`, 135 `135`, 140 `140`, 145 `145`, 150 `150`. |
| **RENDERING RESOLUTION `global.mame_altres`** | Enhancement. Increase the rendering resolution. Makes 3D objects clearer.\\ => 640x480 `640x480`, 800x600 `800x600`, 960x720 `960x720`, 1024x768 `1024x768`, 1280x720 `1280x720`, 1600x800 `1600x800`, 1920x1080 `1920x1080`, 2560x1440 `2560x1440`, 3840x2160 `3840x2160`. |
| **SPECIAL CONTROL LAYOUTS `global.altlayout`** | Controls for 5/6 button games and other unique controls\\ => Default Only `default`, SNES Style `snes`, Genesis/Megadrive Style `megadrive`, Modern Fightstick Style `fightstick`, Neo Geo Mini Pad `neomini`, Neo Geo CD Pad `neocd`, Twin Stick with Triggers `twinstick`, Rotated 4-Way Stick (Q*Bert) `qbert`. |
| **HIGH SCORE PLUGIN `global.hiscoreplugin`** | Emable or disable high score saving\\ => Enabled (Default) `1`, Disabled `0`. |
| **COIN SOUND PLUGIN `global.coindropplugin`** | Play a coin drop sound effect when an insert coin button is pressed\\ => Enabled `1`, Disabled (Default) `0`. |
| **SHARE MAME ARTWORK `global.sharemameart`** | Use the same art paths as standalone MAME - not recommended if using decorations or shaders.\\ => On (Default) `1`, Off `0`. |
| **CROP ARTWORK `global.artworkcrop`** | Crop MAME artwork to maximize the game screen and only fill unused space.\\ => On (Default) `1`, Off `0`. |
| **CUSTOM MAME CONFIG `global.customcfg`** | Set system-wide controls via MAME menu\\ => On `1`, Off `0`. |
| **OFF-SCREEN RELOAD BUTTON `global.offscreenreload`** | Set gun button 2 to reload.\\ => On `1`, Off (Default) `0`. |
| Settings specific to fmtowns ||
| **FM TOWNS MODEL `fmtowns.altmodel`** | Select model to emulate\\ => FM Towns Marty (Default) `fmtmarty`, FM Towns (Model 1/2) `fmtowns`, FM Towns II UX `fmtownsux`. |
| **ADD USER DISK `fmtowns.addblankdisk`** | Insert a disk into the floppy drive, a blank will be used if one doesn't exist\\ => Off (Default) `0`, On `1`. |
| **SOFTWARE LIST `fmtowns.softList`** | Use MAME software lists to identify ROM\\ => Don't Use (Default) `none`, Fujitsu FM Towns CD-ROMs `fmtowns_cd`, Fujitsu FM Towns cracked floppy disk images `fmtowns_flop_cracked`, Fujitsu FM Towns miscellaneous floppy disk images `fmtowns_flop_misc`, Fujitsu FM Towns original floppy disk images `fmtowns_flop_orig`. |
| **MEDIA TYPE `fmtowns.altromtype`** | Type of ROM file to load.\\ => Floppy Disk (Drive 1) `flop1`, Floppy Disk (Drive 2 - Model 1/2 & II UX) `flop2`, CD-ROM `cdrm`, Hard Drive (II UX) `hard1`. |
| **UI KEYS `fmtowns.enableui`** | Toggle with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |
| **CUSTOM CONFIG `fmtowns.pergamecfg`** | Enable per-game custom configuration via MAME menu.\\ => On `1`, Off `0`. |

### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `fmtowns.videomode`, `fmtowns.padtokeyboard`, `fmtowns.videomode`, `fmtowns.bezel`, `fmtowns.bezel_stretch`, `fmtowns.hud`, `fmtowns.hud_corner`, `fmtowns.bezel.tattoo`, `fmtowns.bezel.tattoo_corner`, `fmtowns.bezel.tattoo_file`, `fmtowns.bezel.resize_tattoo`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **VIDEO MODE `fmtowns.video`** | BGFX for post-processing, accel/opengl for raw image.\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **VSYNC `fmtowns.vsync`** | Fix screen tearing, but may drop frames.\\ => Off (Default) `0`, On `1`. |
| **BGFX GRAPHICS API `fmtowns.bgfxbackend`** | Depends on video mode being set to BGFX. Vulkan is better, when supported.\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `fmtowns.bgfxshaders`** | Apply a post-processing effect.\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, CRT Geom Deluxe (RGB) `crt-geom-deluxe-rgb`, CRT Geom Deluxe (Composite) `crt-geom-deluxe-composite`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `fmtowns.switchres`** | Allows the use of switchres profiles if present.\\ => Off `0`, On `1`. |
| **VERTICAL ROTATION (TATE) `fmtowns.rotation`** | Rotates screen by 90 degrees. Intended for rotating displays.\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ARTWORK CROP `fmtowns.artworkcrop`** | Crop artwork to only unused space, keeping the game as large as possible.\\ => Off (Default) `0`, On `1`. |
| **CUSTOM MAME CONFIG `fmtowns.customcfg`** | Set system-wide controls via MAME menu\\ => On `1`, Off `0`. |
| **DATA PLUGIN `fmtowns.dataplugin`** | Make game history, setup instructions, and special moves viewable in the menu\\ => Enabled `1`, Disabled (Default) `0`. |
| **OFF-SCREEN RELOAD BUTTON `fmtowns.offscreenreload`** | Set gun button 2 to reload.\\ => On `1`, Off (Default) `0`. |
| Settings specific to `fmtowns` ||
| **FM TOWNS MODEL `fmtowns.altmodel`** | Select model to emulate\\ => FM Towns Marty (Default) `fmtmarty`, FM Towns (Model 1/2) `fmtowns`, FM Towns II UX `fmtownsux`. |
| **ADD USER DISK `fmtowns.addblankdisk`** | Insert a disk into the floppy drive, a blank will be used if one doesn't exist\\ => Off (Default) `0`, On `1`. |
| **SOFTWARE LIST `fmtowns.softList`** | Use MAME software lists to identify ROM\\ => Don't Use (Default) `none`, Fujitsu FM Towns CD-ROMs `fmtowns_cd`, Fujitsu FM Towns cracked floppy disk images `fmtowns_flop_cracked`, Fujitsu FM Towns miscellaneous floppy disk images `fmtowns_flop_misc`, Fujitsu FM Towns original floppy disk images `fmtowns_flop_orig`. |
| **MEDIA TYPE `fmtowns.altromtype`** | Type of ROM file to load.\\ => Floppy Disk (Drive 1) `flop1`, Floppy Disk (Drive 2 - Model 1/2 & II UX) `flop2`, CD-ROM `cdrm`, Hard Drive (II UX) `hard1`. |
| **UI KEYS `fmtowns.enableui`** | Toggle with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |
| **CUSTOM CONFIG `fmtowns.pergamecfg`** | Enable per-game custom configuration via MAME menu.\\ => On `1`, Off `0`. |

## Controls
Here are the default Fujitsu FM-TOWNS's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).