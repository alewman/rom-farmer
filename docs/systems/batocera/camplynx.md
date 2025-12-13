# Camputers Lynx

**Source:** https://wiki.batocera.org/systems:camplynx  
**Last fetched:** 2025-12-06 16:18:46

---

This article needs some TLC. Read at your own risk.

# Camputers Lynx
The Camputers Lynx is a computer developed by Camputers. It was released in 1983.

This system scrapes metadata for the "camplynx" group(s) and loads the `camplynx` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.wav`, `.tap`, `.zip`, `.7z`
- **Folder:** `/userdata/roms/camplynx`

| Emulators |
| [libretro: mess](#libretro:_mess) |
| [MAME](#mame) |

## BIOS
| MD5 checksum | Share file path | Description |
| `b0ad5bf3070aea27b637e1998c81fa8c` | `bios/lynx48k.zip` | |
| `b665e10211bbdbfaf2defb32d5580892` | `bios/lynx48k.zip` | |
| `bc0760d8bf61c9683270266d259cd2ae` | `bios/lynx48k.zip` | |
| `dde90a794e5324002a9fd7f79cec3172` | `bios/lynx48k.zip` | |
| `a0a8f136f69b5891d33993627a185697` | `bios/lynx96k.zip` | |
| `fcb706b3ba2ba61f6f7af1c28f420f94` | `bios/lynx96k.zip` | |
| `815afa653b61cbe70936b01aff700912` | `bios/lynx96k.zip` | |
| `3ccdb9dfe6018892383fcbb1a9167d76` | `bios/lynx96k.zip` | |
| `01a9770efdab17f089bbbbe53f5d69fa` | `bios/lynx96k.zip` | |
| `89ba52f683cd79638646874e965476b6` | `bios/lynx96k.zip` | |
| `fcb706b3ba2ba61f6f7af1c28f420f94` | `bios/lynx128k.zip` | |
| `5017fe3a2ea47038ae61e2aeb4f43d65` | `bios/lynx128k.zip` | |
| `bf69d9538192f65571dbed43dc4a99bb` | `bios/lynx128k.zip` | |
| `f9f54913cdedb22bb8f0c549ad121379` | `bios/lynx128k.zip` | |

## ROMs
Place your Camputers Lynx ROMs in `/userdata/roms/camplynx`.

Requires MAME BIOS files lynx128k.zip, lynx96k.zip, lynx48k.zip
Using software list mode is recommended.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `camplynx.videomode`, `camplynx.videomode`, `camplynx.ratio`, `camplynx.shaderset`, `camplynx.smooth`, `camplynx.integerscale`, `camplynx.bezel`, `camplynx.bezel_stretch`, `camplynx.hud`, `camplynx.bezel.tattoo`, `camplynx.bezel.tattoo_corner`, `camplynx.bezel.tattoo_file`, `camplynx.bezel.resize_tattoo`, `camplynx.ai_service_enabled`, `camplynx.ai_target_lang`, `camplynx.ai_service_url`, `camplynx.ai_service_pause`, `camplynx.runahead`, `camplynx.secondinstance`, `camplynx.video_frame_delay_auto`, `camplynx.vrr_runloop_enable`, `camplynx.video_threaded`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `camplynx.gfxbackend`** | Choose which graphics API library to use. Vulkan may not work for every core.\\ => OpenGL `gl`, GLCore `glcore`, Vulkan `vulkan`. |
| **AUDIO LATENCY `camplynx.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **ALLOW ROTATION `camplynx.video_allow_rotate`** | Allow cores to set rotation.\\ => On `true`, Off `false`. |
| **CONTROLLER TO LIGHTGUN `camplynx.lightgun_map`** | Map controller inputs to lightgun inputs\\ => On `true`, Off `false`. |

#### libretro: mess
##### libretro: mess configuration
Standardized features for this core: `camplynx.autosave`, `camplynx.netplay`, `camplynx.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **OVERCLOCK (UNSTABLE) `global.mame_cpu_overclock`** | Enhancement. Reduces system slowdown. Causes issues in some games.\\ => default `default`, 30 `30`, 35 `35`, 40 `40`, 45 `45`, 50 `50`, 55 `55`, 60 `60`, 65 `65`, 70 `70`, 75 `75`, 80 `80`, 85 `85`, 90 `90`, 95 `95`, 100 `100`, 105 `105`, 110 `110`, 115 `115`, 120 `120`, 125 `125`, 130 `130`, 135 `135`, 140 `140`, 145 `145`, 150 `150`. |
| **RENDERING RESOLUTION `global.mame_altres`** | Enhancement. Increase the rendering resolution. Makes 3D objects clearer.\\ => 640x480 `640x480`, 800x600 `800x600`, 960x720 `960x720`, 1024x768 `1024x768`, 1280x720 `1280x720`, 1600x800 `1600x800`, 1920x1080 `1920x1080`, 2560x1440 `2560x1440`, 3840x2160 `3840x2160`. |
| **SHARE MAME ARTWORK `global.sharemameart`** | Use the same art paths as standalone MAME - not recommended if using decorations or shaders.\\ => On (Default) `1`, Off `0`. |
| **CROP ARTWORK `global.artworkcrop`** | Crop MAME artwork to maximize the game screen and only fill unused space.\\ => On (Default) `1`, Off `0`. |
| **CUSTOM MAME CONFIG `global.customcfg`** | Set system-wide controls via MAME menu\\ => On `1`, Off `0`. |
| **ALT DPAD MODE `global.altdpad`** | If the D-Pad is oriented incorrectly for your controller.\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |
| Settings specific to camplynx ||
| **SOFTWARE LIST `camplynx.softList`** | Use MAME software lists to identify ROM\\ => Don't Use (Default) `none`, Camputers Lynx cassettes `camplynx_cass`. |
| **LYNX MODEL `camplynx.altmodel`** | \\ => Lynx 128k (Default) `lynx128k`, Lynx 96k `lynx96k`, Lynx 48k `lynx48k`. |
| **UI KEYS `camplynx.enableui`** | Toggle with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |
| **CUSTOM GAME CONFIG `camplynx.pergamecfg`** | Enable per-game custom configuration via MAME menu.\\ => On `1`, Off `0`. |

### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `camplynx.videomode`, `camplynx.padtokeyboard`, `camplynx.videomode`, `camplynx.bezel`, `camplynx.bezel_stretch`, `camplynx.hud`, `camplynx.bezel.tattoo`, `camplynx.bezel.tattoo_corner`, `camplynx.bezel.tattoo_file`, `camplynx.bezel.resize_tattoo`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **VIDEO MODE `camplynx.video`** | BGFX for post-processing, accel/opengl for raw image.\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX GRAPHICS API `camplynx.bgfxbackend`** | Depends on video mode being set to BGFX. Vulkan is better, when supported.\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `camplynx.bgfxshaders`** | Apply a post-processing effect.\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, CRT Geom Deluxe (RGB) `crt-geom-deluxe-rgb`, CRT Geom Deluxe (Composite) `crt-geom-deluxe-composite`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `camplynx.switchres`** | Allows the use of switchres profiles if present.\\ => Off `0`, On `1`. |
| **VERTICAL ROTATION (TATE) `camplynx.rotation`** | Rotates screen by 90 degrees. Intended for rotating displays.\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ARTWORK CROP `camplynx.artworkcrop`** | Crop artwork to only unused space, keeping the game as large as possible.\\ => Off (Default) `0`, On `1`. |
| **ALT DPAD MODE `camplynx.altdpad`** | If the D-Pad is oriented incorrectly for your controller.\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |
| **CUSTOM MAME CONFIG `camplynx.customcfg`** | Set system-wide controls via MAME menu\\ => On `1`, Off `0`. |
| **DATA PLUGIN `camplynx.dataplugin`** | Make game history, setup instructions, and special moves viewable in the menu\\ => Enabled `1`, Disabled (Default) `0`. |
| Settings specific to `camplynx` ||
| **SOFTWARE LIST `camplynx.softList`** | Use MAME software lists to identify ROM\\ => Don't Use (Default) `none`, Camputers Lynx cassettes `camplynx_cass`. |
| **LYNX MODEL `camplynx.altmodel`** | \\ => Lynx 128k (Default) `lynx128k`, Lynx 96k `lynx96k`, Lynx 48k `lynx48k`. |
| **UI KEYS `camplynx.enableui`** | Toggle with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |
| **CUSTOM GAME CONFIG `camplynx.pergamecfg`** | Enable per-game custom configuration via MAME menu.\\ => On `1`, Off `0`. |

## Controls
Here are the default Camputers Lynx's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).