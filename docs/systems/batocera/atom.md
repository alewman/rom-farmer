# Atom

**Source:** https://wiki.batocera.org/systems:atom  
**Last fetched:** 2025-12-06 16:18:43

---

This article needs some TLC. Read at your own risk.

# Atom
The Atom is a computer developed by Acorn Computers. It was released in 1979.

This system scrapes metadata for the "atom" group(s) and loads the `atom` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.wav`, `.tap`, `.csw`, `.uef`, `.mfi`, `.dfi`, `.hfe`, `.mfm`, `.td0`, `.imd`, `.d77`, `.d88`, `.1dd`, `.cqm`, `.cqi`, `.dsk`, `.40t`, `.atm`, `.bin`, `.rom`, `.zip`, `.7z`
- **Folder:** `/userdata/roms/atom`

| Emulators |
| [libretro: mess](#libretro:_mess) |
| [MAME](#mame) |

## BIOS
| MD5 checksum | Share file path | Description |
| `b7b7f8a608339fa39d44a3bcfa2cc3f0` | `bios/atom.zip` | |
| `baa26f458acf5745388177ffc7368124` | `bios/atom.zip` | |
| `9627dfb5f8302db8dd5702dbf7c09f72` | `bios/atom.zip` | |

## ROMs
Place your Atom ROMs in `/userdata/roms/atom`.

Requires MAME BIOS file atom.zip
Using software list mode is recommended. Software list cassettes don't work but floppies do.
Disks will automatically show contents, if the program isn't auto-launched, type the program name followed by a double quote (mapped to shift-2) and hit enter to run.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `atom.videomode`, `atom.videomode`, `atom.ratio`, `atom.shaderset`, `atom.smooth`, `atom.integerscale`, `atom.bezel`, `atom.bezel_stretch`, `atom.hud`, `atom.bezel.tattoo`, `atom.bezel.tattoo_corner`, `atom.bezel.tattoo_file`, `atom.bezel.resize_tattoo`, `atom.ai_service_enabled`, `atom.ai_target_lang`, `atom.ai_service_url`, `atom.ai_service_pause`, `atom.runahead`, `atom.secondinstance`, `atom.video_frame_delay_auto`, `atom.vrr_runloop_enable`, `atom.video_threaded`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `atom.gfxbackend`** | Choose which graphics API library to use. Vulkan may not work for every core.\\ => OpenGL `gl`, GLCore `glcore`, Vulkan `vulkan`. |
| **AUDIO LATENCY `atom.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **ALLOW ROTATION `atom.video_allow_rotate`** | Allow cores to set rotation.\\ => On `true`, Off `false`. |
| **CONTROLLER TO LIGHTGUN `atom.lightgun_map`** | Map controller inputs to lightgun inputs\\ => On `true`, Off `false`. |

#### libretro: mess
##### libretro: mess configuration
Standardized features for this core: `atom.autosave`, `atom.netplay`, `atom.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **OVERCLOCK (UNSTABLE) `global.mame_cpu_overclock`** | Enhancement. Reduces system slowdown. Causes issues in some games.\\ => default `default`, 30 `30`, 35 `35`, 40 `40`, 45 `45`, 50 `50`, 55 `55`, 60 `60`, 65 `65`, 70 `70`, 75 `75`, 80 `80`, 85 `85`, 90 `90`, 95 `95`, 100 `100`, 105 `105`, 110 `110`, 115 `115`, 120 `120`, 125 `125`, 130 `130`, 135 `135`, 140 `140`, 145 `145`, 150 `150`. |
| **RENDERING RESOLUTION `global.mame_altres`** | Enhancement. Increase the rendering resolution. Makes 3D objects clearer.\\ => 640x480 `640x480`, 800x600 `800x600`, 960x720 `960x720`, 1024x768 `1024x768`, 1280x720 `1280x720`, 1600x800 `1600x800`, 1920x1080 `1920x1080`, 2560x1440 `2560x1440`, 3840x2160 `3840x2160`. |
| **SHARE MAME ARTWORK `global.sharemameart`** | Use the same art paths as standalone MAME - not recommended if using decorations or shaders.\\ => On (Default) `1`, Off `0`. |
| **CROP ARTWORK `global.artworkcrop`** | Crop MAME artwork to maximize the game screen and only fill unused space.\\ => On (Default) `1`, Off `0`. |
| **CUSTOM MAME CONFIG `global.customcfg`** | Set system-wide controls via MAME menu\\ => On `1`, Off `0`. |
| **ALT DPAD MODE `global.altdpad`** | If the D-Pad is oriented incorrectly for your controller.\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |
| Settings specific to atom ||
| **SOFTWARE LIST `atom.softList`** | Use MAME software lists to identify ROM\\ => Don't Use (Default) `none`, Acorn Atom cassettes `atom_cass`, Acorn Atom disk images `atom_flop`, Acorn Atom Utility ROMs `atom_rom`. |
| **MEDIA TYPE `atom.altromtype`** | Type of ROM file to load.\\ => Cassette `cass`, Disk (Drive 1) `flop1`, Disk (Drive 2) `flop2`, Cartridge `cart`, Quickload `quik`. |
| **UI KEYS `atom.enableui`** | Toggle with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |
| **CUSTOM GAME CONFIG `atom.pergamecfg`** | Enable per-game custom configuration via MAME menu.\\ => On `1`, Off `0`. |

### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `xegs.videomode`, `xegs.padtokeyboard`, `xegs.videomode`, `xegs.bezel`, `xegs.bezel_stretch`, `xegs.hud`, `xegs.bezel.tattoo`, `xegs.bezel.tattoo_corner`, `xegs.bezel.tattoo_file`, `xegs.bezel.resize_tattoo`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **VIDEO MODE `atom.video`** | BGFX for post-processing, accel/opengl for raw image.\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX GRAPHICS API `atom.bgfxbackend`** | Depends on video mode being set to BGFX. Vulkan is better, when supported.\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `atom.bgfxshaders`** | Apply a post-processing effect.\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, CRT Geom Deluxe (RGB) `crt-geom-deluxe-rgb`, CRT Geom Deluxe (Composite) `crt-geom-deluxe-composite`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `atom.switchres`** | Allows the use of switchres profiles if present.\\ => Off `0`, On `1`. |
| **VERTICAL ROTATION (TATE) `atom.rotation`** | Rotates screen by 90 degrees. Intended for rotating displays.\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ARTWORK CROP `atom.artworkcrop`** | Crop artwork to only unused space, keeping the game as large as possible.\\ => Off (Default) `0`, On `1`. |
| **ALT DPAD MODE `atom.altdpad`** | If the D-Pad is oriented incorrectly for your controller.\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |
| **CUSTOM MAME CONFIG `atom.customcfg`** | Set system-wide controls via MAME menu\\ => On `1`, Off `0`. |
| **DATA PLUGIN `atom.dataplugin`** | Make game history, setup instructions, and special moves viewable in the menu\\ => Enabled `1`, Disabled (Default) `0`. |

## Controls
Here are the default Atom's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).