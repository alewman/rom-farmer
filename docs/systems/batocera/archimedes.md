# Archimedes

**Source:** https://wiki.batocera.org/systems:archimedes  
**Last fetched:** 2025-12-06 16:18:38

---

This article needs some TLC. Read at your own risk.

# Archimedes
The Archimedes is a computer developed by Acorn Computers. It was released in 1987.

This system scrapes metadata for the "archimedes" group(s) and loads the `archimedes` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.mfi`, `.dfi`, `.hfe`, `.mfm`, `.td0`, `.imd`, `.d77`, `.d88`, `.1dd`, `.cqm`, `.cqi`, `.dsk`, `.ima`, `.img`, `.ufi`, `.360`, `.ipf`, `.adf`, `.apd`, `.jfd`, `.ads`, `.adm`, `.adl`, `.ssd`, `.bbc`, `.dsd`, `.st`, `.msa`, `.chd`, `.zip`, `.7z`
- **Folder:** `/userdata/roms/archimedes`

| Emulators |
| [libretro: mess](#libretro:_mess) |
| [MAME](#mame) |
| [CLK](#CLK) |

## BIOS
MAME and Libretro-Mess require these BIOS files:

| MD5 checksum | Share file path | Description |
| `374e4bcaa04cb98aad3b64a1555c3930` | `bios/aa310.zip` | |
| `b0b6a83029b6f85bb044bfc46bf3f0f6` | `bios/aa310.zip` | |
| `bf35bb799aa0278b7ee7719dd32f26bc` | `bios/aa310.zip` | |
| `e41af081535aae930d68ee4cbd672513` | `bios/aa310.zip` | |
| `7ecdccd760557ab0711edb37773faeb6` | `bios/aa310.zip` | |
| `c43bad04862ea03146ff5bf7441a1a24` | `bios/aa310.zip` | |
| `454c1977ad70a206f4f3a0bdca294d85` | `bios/aa310.zip` | |
| `6850da7a70b198eaf6fde5be503fa5cd` | `bios/aa310.zip` | |
| `84d305e248dab48a3a110af161dfb005` | `bios/aa310.zip` | |
| `64d7f085e6afb149ebc2e7f919429a19` | `bios/aa310.zip` | |
| `f7d0a9a4d1dae8eee057aa626b87715f` | `bios/aa310.zip` | |
| `763b015d85c7d9d17e06d5babc0a9d32` | `bios/aa310.zip` | |
| `b8fcd63c6a28d0c7034af2e6c5aff9a8` | `bios/aa310.zip` | |
| `6265551c5d6336f7ddd9f3fc78ceba93` | `bios/aa310.zip` | |
| `ca4379aeab4f7c7640c8ad34b27a9db6` | `bios/aa310.zip` | |
| `358d3c9d2685c076f6a141c26d45520c` | `bios/aa310.zip` | |
| `4ae429fbf23f8aa64ce2002cfb14c527` | `bios/aa310.zip` | |
| `83d0f0738468fdf9f23c13eef22dbeea` | `bios/aa310.zip` | |
| `636e4072c392916d2bf00865fee40984` | `bios/aa310.zip` | |
| `252b1993fdb66cac522a0edbeffc3407` | `bios/aa310.zip` | |
| `591f3bdd0f20a0a3d03c8748f2f75754` | `bios/aa310.zip` | |
| `f77f4a409c78c8495fc3876cd4e7d97c` | `bios/aa310.zip` | |
| `57d3a349407916f55129d6c8c0f56395` | `bios/aa310.zip` | |
| `ee4aa1ea0eebf88c5f6cae6315ed11a1` | `bios/aa310.zip` | |
| `a057124502e533ccd8865dc970cf7017` | `bios/aa310.zip` | |
| `3c40d2821595a7334a46ea3b46a5421d` | `bios/aa310.zip` | |
| `d1d51b8f603bba476d1f63bc5980040e` | `bios/aa310.zip` | |
| `7b096a93cc5ada80bcfb5249bca33768` | `bios/aa310.zip` | |
| `744e80abe4c6a845412f63a0f0b14e48` | `bios/aa310.zip` | |
| `9dac78cba6034c427d00f78fa94ab63d` | `bios/aa310.zip` | |
| `4c0b2e1fb29c8acd84e94d25c953173c` | `bios/aa310.zip` | |
| `f6bf5f8908a19a9aacf733633b1cd5cf` | `bios/aa310.zip` | |
| `eec46f5bd4cdb456b760b3cddf16a33c` | `bios/aa310.zip` | |
| `980e3be0c851a59d0f4602f4a94b2eef` | `bios/aa310.zip` | |
| `971a49d5c2dbb3fc01c17d1d5615781a` | `bios/aa310.zip` | |
| `9ce06a4d2a8331bc5b7fadb967d74f4f` | `bios/aa310.zip` | |
| `c74763f720c98e16dc3c6c421db21485` | `bios/aa310.zip` | |
| `6f564c8917f04594bda7385f6de61061` | `bios/aa310.zip` | |
| `232a302efe19278d9df6ecbc8ea3dc6c` | `bios/aa310.zip` | |
| `1a8617c1abe3e0729d20ce844e1e12a8` | `bios/archimedes_keyboard.zip` | |

CLK requires this BIOS file:

| MD5 checksum | Share file path | Description |
| `b7e46ab8c832d720942fcd2c8a66c294` | `bios/Archimedes/ROM311` | Risc OS 3.11 |

## ROMs
Place your Archimedes ROMs in `/userdata/roms/archimedes`.

MAME requires BIOS files aa310.zip and archimedes_keyboard.zip
Using software list mode is recommended.
Double-click the floppy drive in the lower left to open the contents, double-click the app/game to run it.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `archimedes.videomode`, `archimedes.videomode`, `archimedes.ratio`, `archimedes.shaderset`, `archimedes.smooth`, `archimedes.integerscale`, `archimedes.bezel`, `archimedes.bezel_stretch`, `archimedes.hud`, `archimedes.bezel.tattoo`, `archimedes.bezel.tattoo_corner`, `archimedes.bezel.tattoo_file`, `archimedes.bezel.resize_tattoo`, `archimedes.ai_service_enabled`, `archimedes.ai_target_lang`, `archimedes.ai_service_url`, `archimedes.ai_service_pause`, `archimedes.runahead`, `archimedes.secondinstance`, `archimedes.video_frame_delay_auto`, `archimedes.vrr_runloop_enable`, `archimedes.video_threaded`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `archimedes.gfxbackend`** | Choose which graphics API library to use. Vulkan may not work for every core.\\ => OpenGL `gl`, GLCore `glcore`, Vulkan `vulkan`. |
| **AUDIO LATENCY `archimedes.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **ALLOW ROTATION `archimedes.video_allow_rotate`** | Allow cores to set rotation.\\ => On `true`, Off `false`. |
| **CONTROLLER TO LIGHTGUN `archimedes.lightgun_map`** | Map controller inputs to lightgun inputs\\ => On `true`, Off `false`. |

#### libretro: mess
##### libretro: mess configuration
Standardized features for this core: `archimedes.autosave`, `archimedes.netplay`, `archimedes.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **OVERCLOCK (UNSTABLE) `global.mame_cpu_overclock`** | Enhancement. Reduces system slowdown. Causes issues in some games.\\ => default `default`, 30 `30`, 35 `35`, 40 `40`, 45 `45`, 50 `50`, 55 `55`, 60 `60`, 65 `65`, 70 `70`, 75 `75`, 80 `80`, 85 `85`, 90 `90`, 95 `95`, 100 `100`, 105 `105`, 110 `110`, 115 `115`, 120 `120`, 125 `125`, 130 `130`, 135 `135`, 140 `140`, 145 `145`, 150 `150`. |
| **RENDERING RESOLUTION `global.mame_altres`** | Enhancement. Increase the rendering resolution. Makes 3D objects clearer.\\ => 640x480 `640x480`, 800x600 `800x600`, 960x720 `960x720`, 1024x768 `1024x768`, 1280x720 `1280x720`, 1600x800 `1600x800`, 1920x1080 `1920x1080`, 2560x1440 `2560x1440`, 3840x2160 `3840x2160`. |
| **SHARE MAME ARTWORK `global.sharemameart`** | Use the same art paths as standalone MAME - not recommended if using decorations or shaders.\\ => On (Default) `1`, Off `0`. |
| **CROP ARTWORK `global.artworkcrop`** | Crop MAME artwork to maximize the game screen and only fill unused space.\\ => On (Default) `1`, Off `0`. |
| **CUSTOM MAME CONFIG `global.customcfg`** | Set system-wide controls via MAME menu\\ => On `1`, Off `0`. |
| **ALT DPAD MODE `global.altdpad`** | If the D-Pad is oriented incorrectly for your controller.\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |
| Settings specific to archimedes ||
| **SOFTWARE LIST `archimedes.softList`** | Use MAME software lists to identify ROM\\ => Don't Use (Default) `none`, Acorn Archimedes floppy images `archimedes`, Acorn Archimedes hard disks `archimedes_hdd`, Acorn Archimedes ROM images `archimedes_rom`. |
| **ARCHIMEDES MODEL `archimedes.altmodel`** | Select model to emulate\\ => Archimedes 310 `aa310`, BBC A3000 `aa3000`, Archimedes 440/1 (Default) `aa4401`, Archimedes 540 `aa540`. |
| **UI KEYS `archimedes.enableui`** | Toggle with hotkey + D-pad up or Scroll Lock in-game.\\ => Off at Start `0`, On at Start `1`. |
| **CUSTOM GAME CONFIG `archimedes.pergamecfg`** | Enable per-game custom configuration via MAME menu.\\ => On `1`, Off `0`. |

### MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well. MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. Overall it's a very complicated subject, we have a [guide specific to arcade](:arcade) just for it.

#### MAME configuration
MAME offers a **[Menu](https:*docs.mamedev.org/usingmame/ui.html)** in-game (`[HOTKEY]` +  or `[Tab]` on the keyboard). This can be used to manually adjust inputs or game settings. If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http://mess.redump.net/start). All options can also be edited by opening the `mame.ini` file.

Standardized features available to all versions of this emulator: `archimedes.videomode`, `archimedes.padtokeyboard`, `archimedes.videomode`, `archimedes.bezel`, `archimedes.bezel_stretch`, `archimedes.hud`, `archimedes.bezel.tattoo`, `archimedes.bezel.tattoo_corner`, `archimedes.bezel.tattoo_file`, `archimedes.bezel.resize_tattoo`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all versions of this emulator ||
| **VIDEO MODE `archimedes.video`** | BGFX for post-processing, accel/opengl for raw image.\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX GRAPHICS API `archimedes.bgfxbackend`** | Depends on video mode being set to BGFX. Vulkan is better, when supported.\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `archimedes.bgfxshaders`** | Apply a post-processing effect.\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, CRT Geom Deluxe (RGB) `crt-geom-deluxe-rgb`, CRT Geom Deluxe (Composite) `crt-geom-deluxe-composite`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `archimedes.switchres`** | Allows the use of switchres profiles if present.\\ => Off `0`, On `1`. |
| **VERTICAL ROTATION (TATE) `archimedes.rotation`** | Rotates screen by 90 degrees. Intended for rotating displays.\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ARTWORK CROP `archimedes.artworkcrop`** | Crop artwork to only unused space, keeping the game as large as possible.\\ => Off (Default) `0`, On `1`. |
| **ALT DPAD MODE `archimedes.altdpad`** | If the D-Pad is oriented incorrectly for your controller.\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |
| **CUSTOM MAME CONFIG `archimedes.customcfg`** | Set system-wide controls via MAME menu\\ => On `1`, Off `0`. |
| **DATA PLUGIN `archimedes.dataplugin`** | Make game history, setup instructions, and special moves viewable in the menu\\ => Enabled `1`, Disabled (Default) `0`. |

### CLK
[CLK aka Clock Signal](https://github.com/TomHarte/CLK) is a multi-system emulator that is focused on low-latency emulation, that can be used for Archimedes. CLK has been added to Batocera 42.

## Controls
Here are the default Archimedes's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).