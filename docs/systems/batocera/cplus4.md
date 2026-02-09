# Commodore Plus4

**Source:** https://wiki.batocera.org/systems:cplus4  
**Last fetched:** 2025-12-06 16:18:50

---

This article needs some TLC. Read at your own risk.

# Commodore Plus4
The Commodore Plus4 is a computer developed by Commodore. It was released in 1984.

This system scrapes metadata for the "c64" group(s) and loads the `cplus4` set from the currently selected theme, if available.

Grouped with the "c64" group of systems.

### Quick reference
- **Accepted ROM formats:** `.d64`, `.prg`, `.tap`, `.m3u`, `.zip`, `.7z`
- **Folder:** `/userdata/roms/cplus4`

| Emulators | Accepted ROM formats |
| [vice: xplus4](#vice:_xplus4) | `.d64`, `.prg`, `.tap`, `.zip` |
| [libretro: vice_xplus4](#libretro:_vice_xplus4) | `.d64`, `.prg`, `.tap`, `.m3u`, `.zip`, `.7z` |

## BIOS
No Commodore Plus4 emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Commodore Plus4 ROMs in `/userdata/roms/cplus4`.

## Emulators
### vice
#### vice configuration
Standardized features available to all cores of this emulator: `cplus4.videomode`, `cplus4.padtokeyboard`, `cplus4.videomode`, `cplus4.ratio`, `cplus4.bezel`, `cplus4.bezel_stretch`, `cplus4.hud`, `cplus4.bezel.tattoo`, `cplus4.bezel.tattoo_corner`, `cplus4.bezel.tattoo_file`, `cplus4.bezel.resize_tattoo`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **ZOOM (HIDE BORDERS) `cplus4.noborder`** | Hides borders on many games. Some games used the borders.\\ => NO (DEFAULT) `0`, YES `1`. |
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `cplus4.videomode`, `cplus4.videomode`, `cplus4.ratio`, `cplus4.shaderset`, `cplus4.smooth`, `cplus4.integerscale`, `cplus4.bezel`, `cplus4.bezel_stretch`, `cplus4.hud`, `cplus4.bezel.tattoo`, `cplus4.bezel.tattoo_corner`, `cplus4.bezel.tattoo_file`, `cplus4.bezel.resize_tattoo`, `cplus4.ai_service_enabled`, `cplus4.ai_target_lang`, `cplus4.ai_service_url`, `cplus4.ai_service_pause`, `cplus4.runahead`, `cplus4.secondinstance`, `cplus4.video_frame_delay_auto`, `cplus4.vrr_runloop_enable`, `cplus4.video_threaded`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `cplus4.gfxbackend`** | Choose which graphics API library to use. Vulkan may not work for every core.\\ => OpenGL `gl`, GLCore `glcore`, Vulkan `vulkan`. |
| **AUDIO LATENCY `cplus4.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **ALLOW ROTATION `cplus4.video_allow_rotate`** | Allow cores to set rotation.\\ => On `true`, Off `false`. |
| **CONTROLLER TO LIGHT GUN `cplus4.lightgun_map`** | Map controller inputs to light gun inputs.\\ => On `true`, Off `false`. |

#### libretro: vice_xplus4
##### libretro: vice_xplus4 configuration
Standardized features for this core: `cplus4.rewind`, `cplus4.autosave`, `cplus4.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **MODEL TYPE `global.plus4_model`** | \\ => PLUS4 PAL `PLUS4 PAL`, PLUS4 NTSC `PLUS4 NTSC`, C16 PAL `C16 PAL`, C16 NTSC `C16 NTSC`, V364 NTSC `V364 NTSC`, 232 NTSC `232 NTSC`. |
| **COLOR FILTER `global.vice_plus4_external_palette`** | Can be used to simulate colors of particular displays.\\ => default `default`, colodore_ted `colodore_ted`, yape-pal `yape-pal`, yape-ntsc `yape-ntsc`. |
| **ASPECT RATIO `global.vice_aspect_ratio`** | Change the output resolution ratio.\\ => PAL 576x312px `pal`, NTSC 492x262px `ntsc`. |
| **ZOOM (HIDE BORDERS) `global.vice_zoom_mode`** | Hides borders on many games. Some games used the borders.\\ => Auto-disable zoom `auto_disable`, Auto zoom `automatic`, Off `disabled`, small `small`, medium `medium`, maximum `maximum`. |
| **Button Options `global.vice_retropad_options`** | RetroPad Face Button Options.\\ => B = Fire `disabled`, B = Fire, A = Up `jump`, Y = Fire `rotate`, Y = Fire, B = Up `rotate_jump`. |
| **CONTROLLER PORT `global.vice_joyport`** | Most games use port 2, some use port 1.\\ => Port 1 `1`, Port 2 `2`. |
| **CONTROLLER TYPE `global.vice_joyport_type`** | \\ => Joystick `1`, Paddles `2`, Mouse (1351) `3`, Trackball (Atari CX-22) `6`, Koalapad `10`. |
| **KEYBOARD PASSTHROUGH `global.vice_keyboard_pass_through`** | Keyboard shortcuts unavailable if passing through the keyboard.\\ => Off `disabled`, On `enabled`. |

## Controls
Here are the default Commodore Plus4's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).