# Commodore PET

**Source:** https://wiki.batocera.org/systems:pet  
**Last fetched:** 2025-12-06 16:19:33

---

This article needs some TLC. Read at your own risk.

# Commodore PET
The Commodore PET is a computer developed by Commodore. It was released in 1977.

This system scrapes metadata for the "c64" group(s) and loads the `pet` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.a0`, `.b0`, `.crt`, `.d64`, `.d81`, `.prg`, `.tap`, `.t64`, `.m3u`, `.zip`, `.7z`
- **Folder:** `/userdata/roms/pet`

| Emulators | Accepted ROM formats |
| [vice: xpet](#vice:_xpet) | `.a0`, `.b0`, `.crt`, `.d64`, `.d81`, `.prg`, `.tap`, `.t64`, `.zip` |
| [libretro: vice_xpet](#libretro:_vice_xpet) | `.a0`, `.b0`, `.crt`, `.d64`, `.d81`, `.prg`, `.tap`, `.t64`, `.m3u`, `.zip`, `.7z` |

## BIOS
No Commodore PET emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Commodore PET ROMs in `/userdata/roms/pet`.

## Emulators
### vice
#### vice configuration
Standardized features available to all cores of this emulator: `pet.videomode`, `pet.padtokeyboard`, `pet.videomode`, `pet.ratio`, `pet.bezel`, `pet.bezel_stretch`, `pet.hud`, `pet.bezel.tattoo`, `pet.bezel.tattoo_corner`, `pet.bezel.tattoo_file`, `pet.bezel.resize_tattoo`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **ZOOM (HIDE BORDERS) `pet.noborder`** | Hides borders on many games. Some games used the borders.\\ => NO (DEFAULT) `0`, YES `1`. |
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `pet.videomode`, `pet.videomode`, `pet.ratio`, `pet.shaderset`, `pet.smooth`, `pet.integerscale`, `pet.bezel`, `pet.bezel_stretch`, `pet.hud`, `pet.bezel.tattoo`, `pet.bezel.tattoo_corner`, `pet.bezel.tattoo_file`, `pet.bezel.resize_tattoo`, `pet.ai_service_enabled`, `pet.ai_target_lang`, `pet.ai_service_url`, `pet.ai_service_pause`, `pet.runahead`, `pet.secondinstance`, `pet.video_frame_delay_auto`, `pet.vrr_runloop_enable`, `pet.video_threaded`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `pet.gfxbackend`** | Choose which graphics API library to use. Vulkan may not work for every core.\\ => OpenGL `gl`, GLCore `glcore`, Vulkan `vulkan`. |
| **AUDIO LATENCY `pet.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **ALLOW ROTATION `pet.video_allow_rotate`** | Allow cores to set rotation.\\ => On `true`, Off `false`. |
| **CONTROLLER TO LIGHT GUN `pet.lightgun_map`** | Map controller inputs to light gun inputs.\\ => On `true`, Off `false`. |

#### libretro: vice_xpet
##### libretro: vice_xpet configuration
Standardized features for this core: `pet.rewind`, `pet.autosave`, `pet.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **MODEL TYPE `global.pet_model`** | \\ => 8032 `8032`, 2001 `2001`, 3008 `3008`, 3016 `3016`, 3032 `3032`, 3032B `3032B`, 4016 `4016`, 4032 `4032`, 4032B `4032B`, 8096 `8096`, 8296 `8296`, SUPERPET `SUPERPET`. |
| **COLOR FILTER `global.vice_pet_external_palette`** | Can be used to simulate colors of particular displays.\\ => default `default`, green `green`, amber `amber`, white `white`. |
| **ASPECT RATIO `global.vice_aspect_ratio`** | Change the output resolution ratio.\\ => PAL 576x312px `pal`, NTSC 492x262px `ntsc`. |
| **ZOOM (HIDE BORDERS) `global.vice_zoom_mode`** | Hides borders on many games. Some games used the borders.\\ => Auto-disable zoom `auto_disable`, Auto zoom `automatic`, Off `disabled`, small `small`, medium `medium`, maximum `maximum`. |
| **Button Options `global.vice_retropad_options`** | RetroPad Face Button Options.\\ => B = Fire `disabled`, B = Fire, A = Up `jump`, Y = Fire `rotate`, Y = Fire, B = Up `rotate_jump`. |
| **CONTROLLER PORT `global.vice_joyport`** | Most games use port 2, some use port 1.\\ => Port 1 `1`, Port 2 `2`. |
| **CONTROLLER TYPE `global.vice_joyport_type`** | \\ => Joystick `1`, Paddles `2`, Mouse (1351) `3`, Trackball (Atari CX-22) `6`, Koalapad `10`. |
| **KEYBOARD PASSTHROUGH `global.vice_keyboard_pass_through`** | Keyboard shortcuts unavailable if passing through the keyboard.\\ => Off `disabled`, On `enabled`. |

## Controls
Here are the default Commodore PET's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).