# Electron

**Source:** https://wiki.batocera.org/systems:electron  
**Last fetched:** 2025-12-06 16:18:54

---

This article needs some TLC. Read at your own risk.

# Electron
The Electron is a computer developed by Acorn Computers. It was released in 1983.

This system scrapes metadata for the "electron" group(s) and loads the `electron` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.wav`, `.csw`, `.uef`, `.mfi`, `.dfi`, `.hfe`, `.mfm`, `.td0`, `.imd`, `.d77`, `.d88`, `.1dd`, `.cqm`, `.cqi`, `.dsk`, `.ssd`, `.bbc`, `.img`, `.dsd`, `.adf`, `.ads`, `.adm`, `.adl`, `.rom`, `.bin`, `.zip`, `.7z`
- **Folder:** `/userdata/roms/electron`

| Emulators |
| [libretro: mess](#libretro:_mess) |
| [MAME](#mame) |
| [CLK](#CLK) |

## BIOS
MAME and libretro-mess require the following BIOS files:

| MD5 checksum | Share file path | Description |
| `4688a93aa298b9431c1788c9b90378c8` | `bios/electron.zip` | |
| `2cc67be4624df4dc66617742571a8e3d` | `bios/electron64.zip` | |
| `df01cfe5894276de96bbd1c45b7e834c` | `bios/electron64.zip` | |
| `f3a39227b401a2ce8cdc7e4b7a860aaf` | `bios/electron_plus1.zip` | |
| `9aa334b4e8f6d7565e6323e0f77110de` | `bios/electron_plus3.zip` | |
| `83e15ca501899b0d5b2ce3f5ef696069` | `bios/electron_plus3.zip` | |
| `b60ee811f4b805638478acd5297b16e0` | `bios/electron_plus3.zip` | |
| `62f5e1d3dae3a68d8fe4406a6f603dc3` | `bios/electron_plus3.zip` | |
| `5c39baa89fe8a40a5167a53cc5ae7791` | `bios/electron_plus3.zip` | |

CLK requires the following BIOS files:

| MD5 checksum | Share file path | Description |
| `2cc67be4624df4dc66617742571a8e3d` | `bios/Electron/basic.rom` | Acorn BASIC II ROM |
| `b1707bd3132f6d791c9530dad623e7c6` | `bios/Electron/os.rom` | Electron MOS ROM v1.00 |

## ROMs
Place your Electron ROMs in `/userdata/roms/electron`.

Requires MAME BIOS files electron.zip, electron64.zip, electron_plus1.zip, electron_plus3.zip
Using software list mode (cassette) is recommended.
Tapes should auto-load, use the MAME menu to stop/play/rewind if needed.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `electron.videomode`, `electron.videomode`, `electron.ratio`, `electron.shaderset`, `electron.smooth`, `electron.integerscale`, `electron.bezel`, `electron.bezel_stretch`, `electron.hud`, `electron.bezel.tattoo`, `electron.bezel.tattoo_corner`, `electron.bezel.tattoo_file`, `electron.bezel.resize_tattoo`, `electron.ai_service_enabled`, `electron.ai_target_lang`, `electron.ai_service_url`, `electron.ai_service_pause`, `electron.runahead`, `electron.secondinstance`, `electron.video_frame_delay_auto`, `electron.vrr_runloop_enable`, `electron.video_threaded`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `electron.gfxbackend`** | Choose which graphics API library to use. Vulkan may not work for every core.\\ => OpenGL `gl`, GLCore `glcore`, Vulkan `vulkan`. |
| **AUDIO LATENCY `electron.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **ALLOW ROTATION `electron.video_allow_rotate`** | Allow cores to set rotation.\\ => On `true`, Off `false`. |
| **CONTROLLER TO LIGHTGUN `electron.lightgun_map`** | Map controller inputs to lightgun inputs\\ => On `true`, Off `false`. |

#### libretro: mess
##### libretro: mess configuration
Standardized features for this core: `electron.autosave`, `electron.netplay`, `electron.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **OVERCLOCK (UNSTABLE) `global.mame_cpu_overclock`** | Enhancement. Reduces system slowdown. Causes issues in some games.\\ => default `default`, 30 `30`, 35 `35`, 40 `40`, 45 `45`, 50 `50`, 55 `55`, 60 `60`, 65 `65`, 70 `70`, 75 `75`, 80 `80`, 85 `85`, 90 `90`, 95 `95`, 100 `100`, 105 `105`, 110 `110`, 115 `115`, 120 `120`, 125 `125`, 130 `130`, 135 `135`, 140 `140`, 145 `145`, 150 `150`. |
| **RENDERING RESOLUTION `global.mame_altres`** | Enhancement. Increase the rendering resolution. Makes 3D objects clearer.\\ => 640x480 `640x480`, 800x600 `800x600`, 960x720 `960x720`, 1024x768 `1024x768`, 1280x720 `1280x720`, 1600x800 `1600x800`, 1920x1080 `1920x1080`, 2560x1440 `2560x1440`, 3840x2160 `3840x2160`. |
| **SHARE MAME ARTWORK `global.sharemameart`** | Use the same art paths as standalone MAME - not recommended if using decorations or shaders.\\ => On (Default) `1`, Off `0`. |
| **CROP ARTWORK `global.artworkcrop`** | Crop MAME artwork to maximize the game screen and only fill unused space.\\ => On (Default) `1`, Off `0`. |
| **CUSTOM MAME CONFIG `global.customcfg`** | Set system-wide controls via MAME menu\\ => On `1`, Off `0`. |
| **ALT DPAD MODE `global.altdpad`** | If the D-Pad is oriented incorrectly for your controller.\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |
| Settings specific to electron ||
| **SOFTWARE LIST `electron.softList`** | Use MAME software lists to identify ROM\\ => Don't Use (Default) `none`, Acorn Electron Disks `electron_flop`, Acorn Electron Cassettes `electron_cass`, Acorn Electron Cartridges `electron_cart`, Acron Electron ROMs `electron_rom`. |
| **ELECTRON MODEL `electron.altmodel`** | Select model to emulate\\ => Electron w/64k Master RAM Board (default) `electron64`, Electron `electron`. |
| **UI KEYS `electron.enableui`** | Toggle with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |
| **CUSTOM GAME CONFIG `electron.pergamecfg`** | Enable per-game custom configuration via MAME menu.\\ => On `1`, Off `0`. |

### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `electron.videomode`, `electron.padtokeyboard`, `electron.videomode`, `electron.bezel`, `electron.bezel_stretch`, `electron.hud`, `electron.bezel.tattoo`, `electron.bezel.tattoo_corner`, `electron.bezel.tattoo_file`, `electron.bezel.resize_tattoo`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **VIDEO MODE `electron.video`** | BGFX for post-processing, accel/opengl for raw image.\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX GRAPHICS API `electron.bgfxbackend`** | Depends on video mode being set to BGFX. Vulkan is better, when supported.\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `electron.bgfxshaders`** | Apply a post-processing effect.\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, CRT Geom Deluxe (RGB) `crt-geom-deluxe-rgb`, CRT Geom Deluxe (Composite) `crt-geom-deluxe-composite`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `electron.switchres`** | Allows the use of switchres profiles if present.\\ => Off `0`, On `1`. |
| **VERTICAL ROTATION (TATE) `electron.rotation`** | Rotates screen by 90 degrees. Intended for rotating displays.\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ARTWORK CROP `electron.artworkcrop`** | Crop artwork to only unused space, keeping the game as large as possible.\\ => Off (Default) `0`, On `1`. |
| **ALT DPAD MODE `electron.altdpad`** | If the D-Pad is oriented incorrectly for your controller.\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |
| **CUSTOM MAME CONFIG `electron.customcfg`** | Set system-wide controls via MAME menu\\ => On `1`, Off `0`. |
| **DATA PLUGIN `electron.dataplugin`** | Make game history, setup instructions, and special moves viewable in the menu\\ => Enabled `1`, Disabled (Default) `0`. |
| Settings specific to `electron` ||
| **SOFTWARE LIST `electron.softList`** | Use MAME software lists to identify ROM\\ => Don't Use (Default) `none`, Acorn Electron Disks `electron_flop`, Acorn Electron Cassettes `electron_cass`, Acorn Electron Cartridges `electron_cart`, Acron Electron ROMs `electron_rom`. |
| **ELECTRON MODEL `electron.altmodel`** | Select model to emulate\\ => Electron w/64k Master RAM Board (default) `electron64`, Electron `electron`. |
| **UI KEYS `electron.enableui`** | Toggle with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |
| **CUSTOM GAME CONFIG `electron.pergamecfg`** | Enable per-game custom configuration via MAME menu.\\ => On `1`, Off `0`. |

### CLK
[CLK aka Clock Signal](https://github.com/TomHarte/CLK) is a multi-system emulator that is focused on low-latency emulation, that can be used for Electron. CLK has been added to Batocera 42.

## Controls
Here are the default Electron's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).