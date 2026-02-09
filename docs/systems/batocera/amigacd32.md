# Amiga CD32

**Source:** https://wiki.batocera.org/systems:amigacd32  
**Last fetched:** 2025-12-06 16:18:34

---

This article needs some TLC. Read at your own risk.

# Amiga CD32
The Amiga CD32 is a fourth-generation home video game console developed by Commodore. It was released in 1994.

It is essentially an [Amiga 1200](systems:amiga1200) with a CD-ROM drive and a controller, backwards compatible with some [CDTV](systems:amigacdtv) games. It would be the first 32-bit system released in the Western market, however in Japan the FM Towns Marty would lay claim to that title.

Like with the 3DO and Atari's Jaguar, the Amiga CD32 failed to grasp a stable market share in the face of Sony's [PlayStation](systems:psx) and Sega's [Saturn](systems:saturn). The fact that the CD32 had lackluster 3D polygon support did not help the situation (further attributing to Sony's determination to release only 3D games in the West).

The CD32 would be discontinued only eight months after its debut.

This system scrapes metadata for the "amigacd32" group(s) and loads the `amigacd32` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.bin`, `.cue`, `.iso`, `.chd`
- **Folder:** `/userdata/roms/amigacd32`

| Emulators | Accepted ROM formats |
| [fsuae: CD32](#fsuae:_CD32) | `.bin`, `.cue`, `.iso`, `.chd` |
| [amiberry: CD32](#amiberry:_CD32) | `.bin`, `.cue`, `.iso` |
| [libretro: puae](#libretro:_puae) | `.bin`, `.cue`, `.iso`, `.chd` |
| [libretro: puae2021](#libretro:_puae2021) | `.bin`, `.cue`, `.iso`, `.chd` |
| [libretro: uae4arm](#libretro:_uae4arm) | `.bin`, `.cue`, `.iso`, `.chd` |

## BIOS
| MD5 checksum | Share file path | Description | Notes |
| `5f8924d013dd57a89cf349f4cdedc6b1` | `bios/kick40060.CD32` | CD32 Kickstart v3.1 rev 40.060 | AmigaOS 3.1 |
| `bb72565701b1b6faece07d68ea5da639` | `bios/kick40060.CD32.ext` | CD32 extended ROM rev 40.060 | CDTV extended ROM |
| `5f8924d013dd57a89cf349f4cdedc6b1` | `bios/amiga-os-310-cd32.rom` | CD32 Kickstart v3.1 rev 40.060 | AmigaOS 3.1 |
| `bb72565701b1b6faece07d68ea5da639` | `bios/amiga-ext-310-cd32.rom` | CD32 extended ROM rev 40.060 | CDTV extended ROM |

## ROMs
Place your Amiga CD32 ROMs in `/userdata/roms/amigacd32`.

## Emulators
### fsuae
#### fsuae configuration
Standardized features available to all cores of this emulator: `amigacd32.videomode`, `amigacd32.padtokeyboard`, `amigacd32.videomode`, `amigacd32.ratio`, `amigacd32.bezel`, `amigacd32.bezel_stretch`, `amigacd32.hud`, `amigacd32.hud_corner`, `amigacd32.bezel.tattoo`, `amigacd32.bezel.tattoo_corner`, `amigacd32.bezel.tattoo_file`, `amigacd32.bezel.resize_tattoo`

### amiberry
#### amiberry configuration
Standardized features available to all cores of this emulator: `amigacd32.videomode`, `amigacd32.padtokeyboard`, `amigacd32.videomode`, `amigacd32.ratio`, `amigacd32.bezel`, `amigacd32.bezel_stretch`, `amigacd32.hud`, `amigacd32.hud_corner`, `amigacd32.bezel.tattoo`, `amigacd32.bezel.tattoo_corner`, `amigacd32.bezel.tattoo_file`, `amigacd32.bezel.resize_tattoo`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **LINE MODE `amigacd32.amiberry_linemode`** | Adjust screen line draw mode.\\ => SINGLE `none`, DOUBLE `double`, SCANLINES `scanlines`. |
| **VIDEO RESOLUTION `amigacd32.amiberry_resolution`** | Manually define which internal resolution to use. AUTO = High.\\ => Low `lores`, High `hires`, Super high `superhires`. |
| **SCALING METHOD `amigacd32.amiberry_scalingmethod`** | Change pixel scaling and filtering method.\\ => Automatic `automatic`, Pixelated (Nearest) `pixelated`, Smooth (Linear) `smooth`. |
| **REMOVE INTERLACE ARTIFACTS `amigacd32.amiberry_flickerfixer`** | Fix flickering in a static screen like Workbench.\\ => ON `True`, OFF `False`. |
| **AUTO HEIGHT `amigacd32.amiberry_auto_height`** | Resize automatically screen height.\\ => ON `True`, OFF `False`. |

### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: puae
##### libretro: puae configuration
Standardized features for this core: `amigacd32.rewind`, `amigacd32.autosave`, `amigacd32.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **AMIGA MODEL `global.puae_model`** | Force a specific model and prevent tags detection.\\ => Autodetect (by game name tag) `automatic`, A500 (512KB Chip + 512KB Slow) `A500`, A500+ (1MB Chip) `A500PLUS`, A600 (2MB Chip + 8MB Fast) `A600`, A1200 (2MB Chip + 8MB Fast) `A1200`, A4000/040 (2MB Chip + 8MB Fast) `A4040`, CDTV (1MB Chip) `CDTV`, CD32 Default (2MB Chip) `CD32`, CD32 (2MB Chip + 8MB Fast) `CD32FR`. |
| **CPU COMPATIBILITY `global.cpu_compatibility`** | Help games which are too quick or that have bugs.\\ => Normal `normal`, More compatible `compatible`, Cycle-exact `exact`. |
| **CPU CLOCK `global.cpu_multiplier`** | Works with 'Cycle-exact' mode and for a few games.\\ => Default by model `0`,  3.54 MHz `1`,  7.09 MHz (A500 speed) `2`, 14.18 MHz (A1200 speed) `4`, 28.37 MHz `8`, 35.46 MHz `10`, 42.56 MHz `12`, 56.75 MHz `16`. |
| **CPU SPEED `global.cpu_throttle`** | Ignored with 'Cycle-exact'.\\ => -90% `-900.0`, -80% `-800.0`, -70% `-700.0`, -60% `-600.0`, -50% `-500.0`, -40% `-400.0`, -30% `-300.0`, -20% `-200.0`, -10% `-100.0`, Default `0.0`, +100% `1000.0`, +200% `2000.0`, +300% `3000.0`, +400% `4000.0`, +500% `5000.0`, +600% `6000.0`, +700% `7000.0`, +800% `8000.0`, +900% `9000.0`, +1000% `10000.0`. |
| **VIDEO FORMAT STANDARD `global.video_standard`** | \\ => PAL 288x576px 50Hz `PAL`, NTSC 240x480px 60Hz `NTSC`. |
| **VIDEO RESOLUTION `global.video_resolution`** | Manually define which resolution to use.&#x0a;Auto defaults to High and switches to Super-High when needed.\\ => Low 360p `lores`, High 720p `hires`, Super-high 1440p `superhires`. |
| **ZOOM (HIDE BORDERS) `global.zoom_mode`** | Hides borders on many games. Some games use the borders.\\ => Off `none`, Autofit screen `automatic`, minimum `minimum`, smaller `smaller`, small `small`, medium `medium`, large `large`, larger `larger`, maximum `maximum`. |
| **FRAMESKIP `global.gfx_framerate`** | Skip frames to improve performance, at the cost of choppy motion.\\ => Off `disabled`, 1 `1`, 2 `2`. |
| **MOUSE SPEED `global.mouse_speed`** | Affects mouse speed globally.\\ => original `100`, 50% `50`, 70% `70`, 120% `120`, 150% `150`, 170% `170`, 200% `200`. |
| Settings specific to amiga500 ||
| **FLOPPY TURBO SPEED `amiga500.puae_floppy_speed`** | Removes loading but can add possible glitches/crashes.\\ => Off `100`, On `0`. |
| **2P GAMEPAD MAPPING (KEYRAH) `amiga500.keyrah_mapping`** | Keypad to joyport mappings for 2 players.\\ => Off `disabled`, On `enabled`. |
| **WHDLOAD LAUNCHER `amiga500.whdload`** | Enable launching pre-installed WHDLoad installs.\\ => Off `disabled`, On `config`. |
| **JUMP ON B `amiga500.pad_options`** | Makes second fire button press up instead.\\ => Off `disabled`, On `jump`. |
| **DISABLE EMULATOR JOYSTICK `amiga500.disable_joystick`** | Passes all physical keyboard events for Pad2Key.\\ => Off `disabled`, On `enabled`. |
| **CONTROLLER 1 TYPE `amiga500.controller1_puae`** | Select controller type for Amiga P1.\\ => Retropad `1`, CD32 Pad `517`, Analog Joystick `773`, Joystick `261`, Keyboard `259`. |
| **CONTROLLER 2 TYPE `amiga500.controller2_puae`** | Select controller type for Amiga P2.\\ => Retropad `1`, CD32 Pad `517`, Analog Joystick `773`, Joystick `261`, Keyboard `259`. |
| Settings specific to amiga1200 ||
| **FLOPPY TURBO SPEED `amiga1200.puae_floppy_speed`** | Removes loading but can add possible glitches/crashes.\\ => Off `100`, On `0`. |
| **2P GAMEPAD MAPPING (KEYRAH) `amiga1200.keyrah_mapping`** | Keypad to joyport mappings for 2 players.\\ => Off `disabled`, On `enabled`. |
| **WHDLOAD LAUNCHER `amiga1200.whdload`** | Enable launching pre-installed WHDLoad installs.\\ => Off `disabled`, On `config`. |
| **JUMP ON B `amiga1200.pad_options`** | Makes second fire button press up instead.\\ => Off `disabled`, On `jump`. |
| **DISABLE EMULATOR JOYSTICK `amiga1200.disable_joystick`** | Passes all physical keyboard events for Pad2Key.\\ => Off `disabled`, On `enabled`. |
| **CONTROLLER 1 TYPE `amiga1200.controller1_puae`** | Select controller type for Amiga P1.\\ => Retropad `1`, CD32 Pad `517`, Analog Joystick `773`, Joystick `261`, Keyboard `259`. |
| **CONTROLLER 2 TYPE `amiga1200.controller2_puae`** | Select controller type for Amiga P2.\\ => Retropad `1`, CD32 Pad `517`, Analog Joystick `773`, Joystick `261`, Keyboard `259`. |
| Settings specific to amigacd32 ||
| **BOOT ANIMATION FIRST `amigacd32.puae_cd_startup_delayed_insert`** | Inserts CD during boot animation to prevent loading fail.\\ => Off `disabled`, On `enabled`. |
| **CD TURBO SPEED `amigacd32.puae_cd_speed`** | Removes loading but can add possible glitches/crashes.\\ => Off `100`, On `0`. |
| **JUMP ON A `amigacd32.puae_cd32pad_options`** | Makes the blue button press up instead.\\ => Off `disabled`, On `jump`. |
| Settings specific to amigacdtv ||
| **BOOT ANIMATION FIRST `amigacdtv.puae_cd_startup_delayed_insert`** | Inserts CD during boot animation prevent loading fail.\\ => Off `disabled`, On `enabled`. |
| **CD TURBO SPEED `amigacdtv.puae_cd_speed`** | Removes loading but can add possible glitches/crashes.\\ => Off `100`, On `0`. |

#### libretro: puae2021
##### libretro: puae2021 configuration
Standardized features for this core: `amigacd32.rewind`, `amigacd32.autosave`, `amigacd32.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **AMIGA MODEL `global.puae_model`** | Force a specific model and prevent tags detection.\\ => Autodetect (by game name tag) `automatic`, A500 (512KB Chip + 512KB Slow) `A500`, A500+ (1MB Chip) `A500PLUS`, A600 (2MB Chip + 8MB Fast) `A600`, A1200 (2MB Chip + 8MB Fast) `A1200`, A4000/040 (2MB Chip + 8MB Fast) `A4040`, CDTV (1MB Chip) `CDTV`, CD32 Default (2MB Chip) `CD32`, CD32 (2MB Chip + 8MB Fast) `CD32FR`. |
| **CPU COMPATIBILITY `global.cpu_compatibility`** | Help games which are too quick or that have bugs.\\ => Normal `normal`, More compatible `compatible`, Cycle-exact `exact`. |
| **CPU CLOCK `global.cpu_multiplier`** | Works with 'Cycle-exact' mode and for a few games.\\ => Default by model `0`,  3.54 MHz `1`,  7.09 MHz (A500 speed) `2`, 14.18 MHz (A1200 speed) `4`, 28.37 MHz `8`, 35.46 MHz `10`, 42.56 MHz `12`, 56.75 MHz `16`. |
| **CPU SPEED `global.cpu_throttle`** | Ignored with 'Cycle-exact'.\\ => -90% `-900.0`, -80% `-800.0`, -70% `-700.0`, -60% `-600.0`, -50% `-500.0`, -40% `-400.0`, -30% `-300.0`, -20% `-200.0`, -10% `-100.0`, Default `0.0`, +100% `1000.0`, +200% `2000.0`, +300% `3000.0`, +400% `4000.0`, +500% `5000.0`, +600% `6000.0`, +700% `7000.0`, +800% `8000.0`, +900% `9000.0`, +1000% `10000.0`. |
| **VIDEO FORMAT STANDARD `global.video_standard`** | \\ => PAL 288x576px 50Hz `PAL`, NTSC 240x480px 60Hz `NTSC`. |
| **VIDEO RESOLUTION `global.video_resolution`** | Manually define which resolution to use.&#x0a;Auto defaults to High and switches to Super-High when needed.\\ => Low 360p `lores`, High 720p `hires`, Super-high 1440p `superhires`. |
| **ZOOM/CROP (HIDE BORDERS) `global.zoom_mode`** | Hides borders on many games. Some games use the borders.\\ => Off `none`, Auto zoom `automatic`, minimum `minimum`, smaller `smaller`, small `small`, medium `medium`, large `large`, larger `larger`, maximum `maximum`. |
| **FRAMESKIP `global.gfx_framerate`** | Skip frames to improve performance, at the cost of choppy motion.\\ => Off `disabled`, 1 `1`, 2 `2`. |
| **MOUSE SPEED `global.mouse_speed`** | Affects mouse speed globally.\\ => original `100`, 50% `50`, 70% `70`, 120% `120`, 150% `150`, 170% `170`, 200% `200`. |
| **JUMP ON B `global.pad_options`** | Makes second fire button press up instead.\\ => Off `disabled`, On `jump`. |
| Settings specific to amigacd32 ||
| **BOOT ANIMATION FIRST `amigacd32.puae_cd_startup_delayed_insert`** | Inserts CD during boot animation to prevent loading fail.\\ => Off `disabled`, On `enabled`. |
| **CD TURBO SPEED `amigacd32.puae_cd_speed`** | Removes loading but can add possible glitches/crashes.\\ => Off `100`, On `0`. |
| **JUMP ON A `amigacd32.puae_cd32pad_options`** | Makes the blue button press up instead.\\ => Off `disabled`, On `jump`. |

#### libretro: uae4arm
No configuration is available for this emulator (yet).

## Controls
Here are the default Amiga CD32's controls shown on a [Batocera Retropad](:configure_a_controller):

If using [libretro: PUAE](#libretro:_puae), controls can be remapped per game or per folder by [editing its core options](:remapping_controls_per_emulator#libretropuae).

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).