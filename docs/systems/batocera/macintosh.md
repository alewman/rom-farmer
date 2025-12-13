# Macintosh

**Source:** https://wiki.batocera.org/systems:macintosh  
**Last fetched:** 2025-12-06 16:19:12

---

This article needs some TLC. Read at your own risk.

# Macintosh
The Macintosh is a computer developed by Apple. It was released in 1984.

This system scrapes metadata for the "macintosh" group(s) and loads the `macintosh` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.dsk`, `.zip`, `.7z`, `.mfi`, `.dfi`, `.hfe`, `.mfm`, `.td0`, `.imd`, `.d77`, `.d88`, `.1dd`, `.cqm`, `.cqi`, `.dsk`, `.ima`, `.img`, `.ufi`, `.ipf`, `.dc42`, `.woz`, `.2mg`, `.360`, `.chd`, `.cue`, `.toc`, `.nrg`, `.gdi`, `.iso`, `.cdr`, `.hd`, `.hdv`, `.2mg`, `.hdi`
- **Folder:** `/userdata/roms/macintosh`

| Emulators | Accepted ROM formats |
| [libretro: minivmac](#libretro:_minivmac) | `.zip`, `.dsk` |
| [libretro: mame](#libretro:_mame) | `.dsk`, `.zip`, `.7z`, `.mfi`, `.dfi`, `.hfe`, `.mfm`, `.td0`, `.imd`, `.d77`, `.d88`, `.1dd`, `.cqm`, `.cqi`, `.dsk`, `.ima`, `.img`, `.ufi`, `.ipf`, `.dc42`, `.woz`, `.2mg`, `.360`, `.chd`, `.cue`, `.toc`, `.nrg`, `.gdi`, `.iso`, `.cdr`, `.hd`, `.hdv`, `.2mg`, `.hdi` |
| [MAME](#mame) | `.dsk`, `.zip`, `.7z`, `.mfi`, `.dfi`, `.hfe`, `.mfm`, `.td0`, `.imd`, `.d77`, `.d88`, `.1dd`, `.cqm`, `.cqi`, `.dsk`, `.ima`, `.img`, `.ufi`, `.ipf`, `.dc42`, `.woz`, `.2mg`, `.360`, `.chd`, `.cue`, `.toc`, `.nrg`, `.gdi`, `.iso`, `.cdr`, `.hd`, `.hdv`, `.2mg`, `.hdi` |
| [CLK](#CLK) | `.zip`, `.dsk` (maybe more?)|

## BIOS
MAME and libretro-based emulators require these files:

| MD5 checksum | Share file path | Description |
| `66223be1497460f1e60885eeb35e03cc` | `bios/MacII.ROM` | |
| `2a8a4c7f2a38e0ab0771f59a9a0f1ee4` | `bios/MacIIx.ROM` | |
| `bc04a4252ee96826c1f41f927c145225` | `bios/mac128k.zip` | |
| `409d8b9a04db15b7bfbbd5fcb931bf2e` | `bios/mac128k.zip` | |
| `9d09a9a51c9ef3ea5719e19db22e7901` | `bios/mackbd_m0110.zip` | |
| `9d09a9a51c9ef3ea5719e19db22e7901` | `bios/mackbd_m0120.zip` | |
| `b4118b89fa68a913a225f0cf9a751fae` | `bios/mac512k.zip` | |
| `ab4e461833e98ef7106f24455a07769d` | `bios/mac512k.zip` | |
| `1467a42dee57ac265d063b3f351189fc` | `bios/macplus.zip` | |
| `25b1bf85b3b072d957499cef4d7e313f` | `bios/macplus.zip` | |
| `cf7c3259844245a8967556fa40d81243` | `bios/macplus.zip` | |
| `d5584762b43a9b1cb24a981f9b9b4198` | `bios/macplus.zip` | |
| `f83069fd7ff1fb011958f819cbff4c88` | `bios/macplus.zip` | |
| `875919e2544644cd628f44b5c11db036` | `bios/macplus.zip` | |
| `efcefe8f11c10541a503d48a07878201` | `bios/macplus.zip` | |
| `f4b06da98500df0747a764dfbf1862b9` | `bios/macplus.zip` | |
| `9fb38bdcc0d53d9d380897ee53dc1322` | `bios/macse.zip` | |
| `c229bb677cb41b84b780c9e38a09173e` | `bios/macclasc.zip` | |
| `2a8a4c7f2a38e0ab0771f59a9a0f1ee4` | `bios/mac2fdhd.zip` | |
| `1bf16eefb23a1bea02f031f1ef1de528` | `bios/nb_48gc.zip` | |
| `2a8a4c7f2a38e0ab0771f59a9a0f1ee4` | `bios/maciix.zip` | |
| `fa16d49527c4e6e9c0d9e46904133d39` | `bios/maclc3.zip` | |
| `9e8ea1552153c5e0f895e247e7d3ec1c` | `bios/mackbd_m0110a.zip` | |
| `93155ac7bad0fec36837252bb1e408f2` | `bios/nb_image.zip` | |
| `96665499f5cf2bb5b4aae6fdaf0a9fb5` | `bios/egret.zip` | |
| `b955ecbdf6d2f979f3683dd1d6884643` | `bios/egret.zip` | |
| `5035d321c5d5fa1eab5ce6bf986676e4` | `bios/egret.zip` | |

CLK requires this BIOS file:

| MD5 checksum | Share file path | Description |
| `db7e6d3205a2b48023fba5aa867ac6d6` | `bios/Macintosh/mac512k.rom` | Macintosh 512k ROM |

## ROMs
Place your Macintosh ROMs in `/userdata/roms/macintosh`.

MAME requires a number of BIOS and device files, place in the bios folder in zip format.

Boot disks are from MAME's software lists, floppy images need to be extracted and renamed.

It is recommended to use a hard drive option if available, System 6.0.8 if not.

From mac_flop:
- macos3.img = sytem tools.img from sys30.zip
- macos608.img = system tools.img from sys608.zip

From mac_hdflop:
- macos701 = disk tools.img from sys701.zip
- macos75 = SSW750_DiskTools.img from sys75.zip

From mac_hdd:
- mac601.chd
- mac701.chd
- mac755.chd

If booting from a hard drive, floppies may not load at boot. For best results, make a copy of one of the bootable drives, load disks manually via the MAME menu, and copy or install them to the hard drive image.

Disk images will only load on Mac IIx and are not bootable.

## Emulators
### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: minivmac
lr-minivmac requires MacII.ROM and MacIIx.ROM.

#### libretro: mame
##### libretro: mame configuration
Standardized features for this core: `macintosh.autosave`, `macintosh.netplay`

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
| Settings specific to macintosh ||
| **SOFTWARE LIST `macintosh.softList`** | Use MAME software lists to identify ROM\\ => Don't Use (Default) `none`, Macintosh 400K/800K Disk images `mac_flop`, Macintosh High Density Disk images `mac_hdflop`, Mac Harddisks `mac_hdd`. |
| **MAC MODEL `macintosh.altmodel`** | Select model of Mac (Recommendations are Mac Plus for B&W, Mac LC 3 for Color)\\ => Mac 128k (128kb RAM, 2 LD Floppies) `mac128k`, Mac 512k (512kb RAM, 2 LD Floppies) `mac512k`, Mac Plus (4Mb RAM, 2 LD Floppies/HDD) `macplus`, Mac SE (4Mb RAM, 2 LD Floppies/HDD) `macse`, Mac Classic (4Mb RAM, 2 HD Floppies/HDD) `macclasc`, Mac II (2Mb RAM, Color, 2 HD Floppies/CD/HDD) `mac2fdhd`, Mac IIx (2Mb RAM, Color, 2 HD Floppies/CD/HDD/Image Reader) `maciix`, Mac LC 3 (Default) (4Mb RAM, Color, 2 HD Floppies/CD/HDD) `maclc3`. |
| **IMAGE READER `macintosh.imagereader`** | Install the image reader card to read idks image files (Mac IIx only)\\ => Disabled `disabled`, Slot A (Default) `nba`, Slot B `nbb`, Slot C `nbc`, Slot D `nbd`, Slot E `nbe`. |
| **RAM SIZE `macintosh.ramsize`** | How much RAM the emulated Mac will have installed (Mac IIx & Mac LC 3 only)\\ => 2MB `2`, 4MB `4`, 8MB `8`, 16MB `16`, 32MB `32`, 48MB `48`, 64MB `64`, 96MB `96`, 128MB `128`. |
| **MEDIA TYPE `macintosh.altromtype`** | Type of ROM file to load\\ => Floppy Disk `flop1`, CD `cdrm`, Hard Drive `hard`. |
| **BOOT DISK `macintosh.bootdisk`** | Select a boot disk or hard drive if needed\\ => System 3.0 (LD Floppy) `macos3`, System 6.0.8 (LD Floppy) `macos608`, System 7.0.1 (HD Floppy) `macos701`, System 7.5 (HD Floppy) `macos75`, System 6.0.8 (Hard Drive) `mac608`, System 7.0.1 (Hard Drive) `mac701`, System 7.5.5 (Hard Drive) `mac755`. |
| **UI KEYS `macintosh.enableui`** | Toggle with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |
| **CUSTOM GAME CONFIG `macintosh.pergamecfg`** | Enable per-game custom configuration via MAME menu.\\ => On `1`, Off `0`. |

### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `macintosh.videomode`, `macintosh.padtokeyboard`, `macintosh.videomode`, `macintosh.bezel`, `macintosh.bezel_stretch`, `macintosh.hud`, `macintosh.hud_corner`, `macintosh.bezel.tattoo`, `macintosh.bezel.tattoo_corner`, `macintosh.bezel.tattoo_file`, `macintosh.bezel.resize_tattoo`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **VIDEO MODE `macintosh.video`** | BGFX for post-processing, accel/opengl for raw image.\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **VSYNC `macintosh.vsync`** | Fix screen tearing, but may drop frames.\\ => Off (Default) `0`, On `1`. |
| **BGFX GRAPHICS API `macintosh.bgfxbackend`** | Depends on video mode being set to BGFX. Vulkan is better, when supported.\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `macintosh.bgfxshaders`** | Apply a post-processing effect.\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, CRT Geom Deluxe (RGB) `crt-geom-deluxe-rgb`, CRT Geom Deluxe (Composite) `crt-geom-deluxe-composite`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `macintosh.switchres`** | Allows the use of switchres profiles if present.\\ => Off `0`, On `1`. |
| **VERTICAL ROTATION (TATE) `macintosh.rotation`** | Rotates screen by 90 degrees. Intended for rotating displays.\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ARTWORK CROP `macintosh.artworkcrop`** | Crop artwork to only unused space, keeping the game as large as possible.\\ => Off (Default) `0`, On `1`. |
| **CUSTOM MAME CONFIG `macintosh.customcfg`** | Set system-wide controls via MAME menu\\ => On `1`, Off `0`. |
| **DATA PLUGIN `macintosh.dataplugin`** | Make game history, setup instructions, and special moves viewable in the menu\\ => Enabled `1`, Disabled (Default) `0`. |
| **OFF-SCREEN RELOAD BUTTON `macintosh.offscreenreload`** | Set gun button 2 to reload.\\ => On `1`, Off (Default) `0`. |
| Settings specific to `macintosh` ||
| **SOFTWARE LIST `macintosh.softList`** | Use MAME software lists to identify ROM\\ => Don't Use (Default) `none`, Macintosh 400K/800K Disk images `mac_flop`, Macintosh High Density Disk images `mac_hdflop`, Mac Harddisks `mac_hdd`. |
| **MAC MODEL `macintosh.altmodel`** | Select model of Mac (Recommendations are Mac Plus for B&W, Mac LC 3 for Color)\\ => Mac 128k (128kb RAM, 2 LD Floppies) `mac128k`, Mac 512k (512kb RAM, 2 LD Floppies) `mac512k`, Mac Plus (4Mb RAM, 2 LD Floppies/HDD) `macplus`, Mac SE (4Mb RAM, 2 LD Floppies/HDD) `macse`, Mac Classic (4Mb RAM, 2 HD Floppies/HDD) `macclasc`, Mac II (2Mb RAM, Color, 2 HD Floppies/CD/HDD) `mac2fdhd`, Mac IIx (2Mb RAM, Color, 2 HD Floppies/CD/HDD, Image Reader) `maciix`, Mac LC 3 (Default) (4Mb RAM, Color, 2 HD Floppies/CD/HDD) `maclc3`. |
| **IMAGE READER `macintosh.imagereader`** | Install the image reader card to read idks image files (Mac IIx only)\\ => Disabled `disabled`, Slot A (Default) `nba`, Slot B `nbb`, Slot C `nbc`, Slot D `nbd`, Slot E `nbe`. |
| **RAM SIZE `macintosh.ramsize`** | How much RAM the emulated Mac will have installed (Mac IIx & Mac LC 3 only)\\ => 2MB `2`, 4MB `4`, 8MB `8`, 16MB `16`, 32MB `32`, 48MB `48`, 64MB `64`, 96MB `96`, 128MB `128`. |
| **MEDIA TYPE `macintosh.altromtype`** | Type of ROM file to load. Disk Image requires Mac IIx and Image Reader\\ => Floppy Disk `flop1`, CD `cdrm`, Hard Drive `hard`, Disk Image `disk`. |
| **BOOT DISK `macintosh.bootdisk`** | Select a boot disk or hard drive if needed\\ => System 3.0 (LD Floppy) `macos3`, System 6.0.8 (LD Floppy) `macos608`, System 7.0.1 (HD Floppy) `macos701`, System 7.5 (HD Floppy) `macos75`, System 6.0.8 (Hard Drive) `mac608`, System 7.0.1 (Hard Drive) `mac701`, System 7.5.5 (Hard Drive) `mac755`. |
| **UI KEYS `macintosh.enableui`** | Toggle with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |
| **CUSTOM GAME CONFIG `macintosh.pergamecfg`** | Enable per-game custom configuration via MAME menu.\\ => On `1`, Off `0`. |

### CLK
[CLK aka Clock Signal](https://github.com/TomHarte/CLK) is a multi-system emulator that is focused on low-latency emulation, that can be used for Apple Macintosh. CLK has been added to Batocera 42.

## Controls
Here are the default Macintosh's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).