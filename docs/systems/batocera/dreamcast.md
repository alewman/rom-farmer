# Sega Dreamcast

**Source:** https://wiki.batocera.org/systems:dreamcast  
**Last fetched:** 2025-12-06 16:18:53

---

# Sega Dreamcast
The [Dreamcast](wp>Dreamcast) is a sixth-generation console released by Sega on November 27, 1998 in Japan and later on September 9, 1999 in NA. The system is available in most builds, except for RPi1/Zero and 2. [Here's a fun page about it.](https://www.copetti.org/writings/consoles/dreamcast/)

This system scrapes metadata for the "dreamcast" group and loads the `dreamcast` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.cdi`, `.cue`, `.gdi`, `.chd`, `.m3u`
- **Folder:** `/userdata/roms/dreamcast`

| Emulators |
| [libretro: Flycast](#libretro:_flycast) |
| [Flycast](#flycast) |
| [Redream](#redream) |

## BIOS
The "World" BIOS file and USA flash file which should work fine for the massive majority of games.

| MD5 checksum | Share file path | Description |
| `e10c53c2f8b90bab96ead2d368858623` | `bios/dc/dc_boot.bin` | Dreamcast BIOS file (World) |
| `0a93f7940c455905bea6e392dfde92a4` | `bios/dc/dc_flash.bin` | Dreamcast system configuration file (USA) |

Alternative BIOS files that are also acceptable:

| MD5 checksum | Share file path | Description |
| `d407fcf70b56acb84b8c77c93b0e5327` | `bios/dc/dc_boot.bin` | Dreamcast BIOS file (Region free) |
| `d552d8b577faa079e580659cd3517f86` | `bios/dc/dc_boot.bin` | Dreamcast BIOS file (Region free) |
| `93a9766f14159b403178ac77417c6b68` | `bios/dc/dc_flash.bin` | Dreamcast system configuration file (Region free) |
| `74e3f69c2bb92bc1fc5d9a53dcf6ffe2` | `bios/dc/dc_flash.bin` | Dreamcast system configuration file (Region free) |
| `23df18aa53c8b30784cd9a84e061d008` | `bios/dc/dc_flash.bin` | Dreamcast system configuration file (Europe) |
| `69c036adfca4ebea0b0c6fa4acfc8538` | `bios/dc/dc_flash.bin` | Dreamcast system configuration file (Japan) |

## ROMs
Dreamcast discs are a special form of CD named GD, which are capable of holding up to 1GB of data, compared to the ~700MB capacity of regular CDs. GDs were traditionally dumped off of the original console as GD-ROMs (which contains a `game.gdi` sheet, `info.txt` and `data.bin`/`.iso`/`.raw` track(s)), but some more modern tools may use the more universal `game.cue` sheet and `data.bin` track format. Most emulators can load either sheet format fine. You should load the `.gdi` or `.cue` sheet and not the `.bin`/`.iso`/`.raw` tracks. From Batocera v31 onwards, EmulationStation should avoid making duplicate entries for these files.

If you're currently missing the `.gdi` or `.cue` files, check out [the section on recovering them on this page](:cd_image_formats#cue_sbi_gdi_sheet_recovery).

WinCE games seem to not run on the RPi3B+.

### Disc compression
The recommended format for compressing disc images is [CHD](:disk_image_compression#chd).

If compressing the image into the CHD format ensure that you are using chdman version 0.230 or later, as earlier versions have issues with Dreamcast images. If your compressed ROMs are failing to launch in Batocera, users have reported having more success making chdman target a `.gdi` file instead of a `.cue` file. Most online .bat scripts only target `.cue` files. There is a custom version of chdman that supports rolling to and from CUE/BIN files [here](https://github.com/mamedev/mame/files/7437320/chdman.zip).

### Multi-disc games
To automatically load the next disc of a game, you can use a .m3u playlist file. To make one, simply create a text file with the same filename as your intended game name (it could be anything, really). Within that text file, write the names of the .gdi sheets or .chd files for your game discs. For instance, if your game's .gdi sheets were structured like

```

roms/
└─ dreamcast/
   ├─ Shenmue (Disc 1).gdi
   ├─ Shenmue (Disc 1).bin
   ├─ Shenmue (Disc 2).gdi
   ├─ Shenmue (Disc 2).bin
   ├─ Shenmue (Disc 3).gdi
   ├─ Shenmue (Disc 3).bin
   ├─ Shenmue (Passport disc).gdi
   └─ Shenmue (Passport disc).bin

```

you would put the following as text into the `Shenmue.m3u` text file:

```

Shenmue (Disc 1).gdi
Shenmue (Disc 2).gdi
Shenmue (Disc 3).gdi
Shenmue (Passport disc).gdi

```

Save the text file with the file extension .m3u and place it in the `dreamcast` folder along with the game's discs. When you get to the end of that disc, the next disc will be automatically loaded. In libretro cores, if this fails, you can utilize Retroarch's 'Disc Control' menu in the Quick Menu (Hotkey+) to manually eject a disc and insert another (Swap Disc is for legacy purposes and should not be used). Refer to [multi-disc games](:cd_image_formats#multi-disc_games) for more info.

## Emulators
### Flycast
[Flycast](https:*github.com/flyinghead/flycast) is a fork of [Reicast](https:*reicast.com/) (which itself is a fork of nullDC). A highly compatible and accurate standalone emulator.

Flycast can also be used to run [NAOMI arcade](:systems:naomi) games due to being nearly identical hardware.

#### Flycast configuration
Standardized features available to all cores of this emulator: `dreamcast.videomode`, `dreamcast.videomode`, `dreamcast.bezel`, `dreamcast.bezel_stretch`, `dreamcast.hud`, `dreamcast.bezel.tattoo`, `dreamcast.bezel.tattoo_corner`, `dreamcast.bezel.tattoo_file`, `dreamcast.bezel.resize_tattoo`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **SCREEN RATIO `dreamcast.flycast_ratio`** | Choose which screen ratio you want to use.\\ => Default `False`, Widescreen `True`. |
| **RENDER RESOLUTION `dreamcast.flycast_render_resolution`** | Choose which internal rendering resolution you want to use.\\ => 320x240 (Half) `240`, 640x480 (Native) `480`, 960x720 (x1.5) `720`, 1280x960 (x2) `960`, 1600x1200 (x2.5) `1200`, 1920x1440 (x3) `1440`, 2560x1920 (x4) `1920`, 2880x2160 (x4.5) `2160`. |
| **GRAPHICS API `dreamcast.flycast_renderer`** | Choose your graphics renderer.\\ => OpenGL (Default) `0`, Vulkan `4`. |
| **ROTATE SCREEN 90 DEGREES `dreamcast.flycast_rotate`** | Rotate the screen by 90 degrees.\\ => Normal `False`, Rotate `True`. |

All other configuration must be done via the `flycast-config` in the Applications folder (`[F1]` on the systems screen).

### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: Flycast
A fork of a fork of a fork... this is an identical version of standalone Flycast but inside of a libretro core. Makes use of RetroArch's features.

#### libretro: Flycast configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **SYNCHRONOUS RENDERING `global.reicast_synchronous_rendering`** | When threaded rendering is on (on by default), waits for the GPU to finish rendering the frame before dropping the current one. This can avoid certain emulation issues (flashing screens, glitchy video). Significant performance cost. Recommended "Off" for most games as they don't experience issues (or you have a weak machine), "On" if the game has these particular issues.\\ => Off `disabled`, On `enabled`. |
| **RENDERING RESOLUTION `global.reicast_internal_resolution`** | Enhancement. Increases the rendering resolution. Makes 3D objects clearer. Significant performance cost. Use 640x480 for native. Absurdly high values can degrade image quality (pixels beginning to shimmer).\\ => 1x (640x480) `640x480`, 1.25x (800x600) `800x600`, 1.5x (960x720) `960x720`, 1.6x (1024x768) `1024x768`, 2x (1280x960) `1280x960`, 2.25x (1440x1080) `1440x1080`, 2.5x (1600x1200) `1600x1200`, 3x (1920x1440) `1920x1440`, 4x (2560x1920) `2560x1920`, 5x (3200x2400) `3200x2400`, 6x (3840x2880) `3840x2880`, 7x (4480x3360) `4480x3360`, 8x (5120x3840) `5120x3840`, 9x (5760x4320) `5760x4320`, 10x (6400x4800) `6400x4800`, 11x (7040x5280) `7040x5280`, 12x (7680x5760) `7680x5760`. |
| **TARGET COLOR FOR PLAYER 1. `global.reicast_lightgun1_crosshair`** | \\ => Red `Red`, Blue `Blue`, Green `Green`, White `White`, Disabled `disabled`. |
| **TARGET COLOR FOR PLAYER 2. `global.reicast_lightgun2_crosshair`** | \\ => Red `Red`, Blue `Blue`, Green `Green`, White `White`, Disabled `disabled`. |
| **TARGET COLOR FOR PLAYER 3. `global.reicast_lightgun3_crosshair`** | \\ => Red `Red`, Blue `Blue`, Green `Green`, White `White`, Disabled `disabled`. |
| **TARGET COLOR FOR PLAYER 4. `global.reicast_lightgun4_crosshair`** | \\ => Red `Red`, Blue `Blue`, Green `Green`, White `White`, Disabled `disabled`. |
| **TEXTURE MIP-MAPPING (BLUR) `global.reicast_mipmapping`** | Enables [mip-mapping](:anti-aliasing#mip-mapping) to smooth out textures on distant 3D objects based on distance and angle. Dreamcast games natively utilized mipmapping to get extra performance out of the hardware, but the extra bluriness from doing this is more apparent on modern, higher fidelity screens. Has a minimal performance cost. `enabled` should be used in conjunction with anisotropic filtering to mitigate blurriness. Some users may prefer the "sharpness" of `disabled` better.\\ => Off `disabled`, On `enabled`. |
| **ANISOTROPIC FILTERING `global.reicast_anisotropic_filtering`** | Enables [anisotropic filtering](:anti-aliasing#anisotropic_filtering) to enhance perspective textures. Dramatically improves the clarity of textures on distant 3D objects when mip-mapping is turned on, especially at higher internal resolutions. Test Drive: Le Mans is the only Dreamcast game that natively utilizes this. Has a small performance cost. Generally safe to use 16x when mip-mapping is also enabled, leave on "Off" otherwise.\\ => Off `False`, 2x `2`, 4x `4`, 8x `8`, 16x `16`. |
| **TEXTURE UPSCALING (XBRZ) `global.reicast_texupscale`** | Enhancement. Applies [xBRZ upscaling to textures](:anti-aliasing#texture_enhancement) to improve their clarity. Improvements are subjective.\\ => Off `False`, 2x `2x`, 4x `4x`, 6x `6x`. |
| **FRAMESKIP `global.reicast_frame_skipping`** | Skip frames to improve performance, at the cost of choppy motion. Higher values can cause motion sickness if used for extended periods. Should only be turned up on weak hardware and if immune to motion sickness.\\ => Off `disabled`, 1 `1`, 2 `2`, 3 `3`, 4 `4`, 5 `5`, 6 `6`. |
| **FORCE WINDOWS CE MODE `global.reicast_force_wince`** | Some Dreamcast games (marked "Powered by Microsoft Windows CE" on the box, eg. Sega Rally 2) utilized the MMU Windows Compact Edition API on the Dreamcast to run. Batocera should automatically detect this but in case it doesn't you can manually override it here. Significant performance cost.\\ => Off `disabled`, On `enabled`. |
| **WIDESCREEN CHEAT (PRIORITY) `global.reicast_widescreen_cheats`** | Enhancement. Flycast has a database of cheats that can enable widescreen support in certain games, rendering them in [anamorphic widescreen](wp>Anamorphic_widescreen) without changing the internal resolution. Some games also natively support widescreen in their in-game options. A 16/9 ratio must be used and bezels must be disabled.\\ => Off `disabled`, On `enabled`. |
| **WIDESCREEN HACK `global.reicast_widescreen_hack`** | Enhancement. Changes the internal resolution to a widescreen ratio (eg. 640x480 becomes 853x480). Somewhat glitchy. Some games also natively support widescreen in their in-game options. A 16/9 ratio must be used and bezels must be disabled.\\ => Off `disabled`, On `enabled`. |
| **CONTROLLER 1 TYPE `global.controller1_dc`** | Chooses the controller plugged into port 1.\\ => Gamepad `1`, Keyboard `3`, Mouse `2`, Light Gun `4`. |
| **CONTROLLER 2 TYPE `global.controller2_dc`** | Same as above for port 2.\\ => Gamepad `1`, Keyboard `3`, Mouse `2`, Light Gun `4`. |
| **CONTROLLER 3 TYPE `global.controller3_dc`** | Same as above for port 3.\\ => Gamepad `1`, Keyboard `3`, Mouse `2`, Light Gun `4`. |
| **CONTROLLER 4 TYPE `global.controller4_dc`** | Same as above for port 4.\\ => Gamepad `1`, Keyboard `3`, Mouse `2`, Light Gun `4`. |

All other settings can be configured from RetroArch's **Quick Menu** -> **Options** (`[HOTKEY]` + ).

### Redream

Redream has been removed from Batocera **v36** and up on Wayland devices due to not supporting Wayland.

[Redream](https://redream.io/) is a multi-platform standalone emulator. Has high compatibility with low system requirements. Lacks some options compared to Flycast.

You cannot exit Redream via controller as the Hotkey+Start shortcut opens the Redream menu instead and you cannot navigate to the close button unless you have a mouse.

#### Redream configuration
Standardized features available to all cores of this emulator: `dreamcast.videomode`, `dreamcast.bezel`, `dreamcast.bezel_stretch`, `dreamcast.hud`, `dreamcast.bezel.tattoo`, `dreamcast.bezel.tattoo_corner`, `dreamcast.bezel.tattoo_file`, `dreamcast.bezel.resize_tattoo`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **RENDERING RESOLUTION `dreamcast.redreamResolution`** | Choose your render resolution (Requires personal redream.key file).\\ => 1x (640x480) `1`, 2x (1280x960) (Default) `2`, 3x (1920x1440) `3`, 4x (2560x1920) `4`, 5x (3200x2400) `5`, 6x (3840x2880) `6`. |
| **ASPECT RATIO `dreamcast.redreamRatio`** | Choose your preferred aspect ratio.\\ => 4:3 (Default) `4:3`, 16:9 `16:9`, Stretch `stretch`. |
| **FRAMESKIP `dreamcast.redreamFrameSkip`** | Enable auto frameskipping for performance on lower-end systems.\\ => Off (Default) `0`, On `1`. |
| **VSYNC `dreamcast.redreamVsync`** | Enable vertical sync to avoid tearing in some cases.\\ => Off (Default) `0`, On `1`. |
| **POLYGON SORT ACCURACY `dreamcast.redreamPolygon`** | Choose the amount of polygon sort accuracy (Higher may cause artifacts).\\ => Per-strip (Default) `0`, Per-pixel (32 layers) `32`, Per-pixel (64 layers) `64`. |
| **REGION `dreamcast.redreamRegion`** | Choose the Dreamcast console region.\\ => USA (Default) `usa`, Europe `europe`, Japan `japan`. |
| **LANGUAGE `dreamcast.redreamLanguage`** | Choose the Dreamcast console language.\\ => English (Default) `english`, German `german`, French `french`, Spanish `spanish`, Italian `italian`, Japanese `japanese`. |
| **BROADCAST `dreamcast.redreamBroadcast`** | Choose broadcast standard (for older TV's).\\ => NTSC (Default) `ntsc`, PAL `pal`, PAL_M `pal_m`, PAL_N `pal_n`. |
| **CABLE `dreamcast.redreamCable`** | Choose cable type for the TV.\\ => VGA (Default) `vga`, RGB `rgb`, Composite `composite`. |

Redream can also be configured from its `redream-config` application (`[F1]` on the system list -> **Applications**).

#### Redream license key
On PC, Redream locks some of settings behind a one-time purchase of a premium license. Once purchased, this can be downloaded (it's just a text file) from [https://redream.io/account](https://redream.io/account) after signing in:

Redream checks for its license key in `/userdata/system/configs/redream/redream.key`. If a valid license is found, additional rendering options (such as rendering resolution) will become unlocked.

This license is not required for ARM devices such as RPi.

## Texture packs
Flycast supports custom texture packs for games. To use them:
  - Copy the unzipped texture pack folder to `saves/dreamcast/flycast/textures/` (it should already be titled the proper game ID for the game that it supports)
  - In Batocera, launch `flycast-config` from the file manager -> Applications
  - Navigate to **Settings** -> **Video** and tick "Load Custom Textures" 
  - Exit with `[Alt]` + `[F4]` and then launch the game from Batocera

## Controls
Here are the default Sega Dreamcast's controls shown on a [Batocera Retropad](:configure_a_controller):

Each Dreamcast emulator handles the `[HOTKEY]`, its chords and the `[SELECT]` button differently.

- libretro/flycast
  - `[HOTKEY]` by itself does nothing.
  - `[HOTKEY]` + `[START]` closes the emulator.
  - `[SELECT]` does nothing.
- Flycast standalone
  - `[HOTKEY]` by itself opens Flycast's quick menu.
  - `[HOTKEY]` + `[START]` closes the emulator.
  - `[SELECT]` does nothing.
- Redream
  - `[HOTKEY]` by itself opens Redream's menu.
  - `[HOTKEY]` + `[START]` does nothing.
  - `[SELECT]` toggles fast-forward.

The `[HOTKEY]` + `[L1]` shortcut, which ordinarily takes a screenshot, will instead eject the disc in [libretro/Flycast](#libretro_flycast). Practice caution!

## Troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).