# Amiga 1200/AGA

**Source:** https://wiki.batocera.org/systems:amiga1200  
**Last fetched:** 2025-12-06 16:18:32

---

This article needs some TLC. Read at your own risk.

# Amiga 1200/AGA
The Amiga 1200 (a.k.a. Amiga AGA, a.k.a. Amiga home computer) is a line of personal computers developed by Commodore. The first Advanced Graphics Architecture (AGA), the Amiga 4000, was released in 1992.

The AGA line is the last upgraded form of the Amiga home computer line, succeeding [the Amiga 8-bit computers](systems:amiga500). It includes the following models:
- Amiga 4000 (Motorola 68EC030/68040)
- Amiga 1200 (Motorola 68EC020)
- Amiga 4000T (Motorola 68040/68060)

The AGA graphic chipset could display up to 256 colors, boosting up to 262 thousand colors (selectable from a 16 million color palette) in HAM-8 mode.

The Amiga 1200 is the most well-known (probably because the Amiga 4000 was prohibitively expensive). It would be Commodore's last low-budget model before filing for bankruptcy in 1994.

The AGA line was different enough from the 8-bit computers that software/games were *usually* developed specific to both versions. If available, the AGA version (1200 commonly) is the superior version.

This system scrapes metadata for the "amiga" group(s) and loads the `amiga1200` set from the currently selected theme, if available.

Grouped with the "amiga" group of systems.

### Quick reference
- **Accepted ROM formats:** `.adf`, `.uae`, `.ipf`, `.dms`, `.dmz`, `.adz`, `.lha`, `.hdf`, `.exe`, `.m3u`, `.zip`
- **Folder:** `/userdata/roms/amiga1200`

| Emulators | Accepted ROM formats |
| [fsuae: A1200](#fsuae:_A1200) | `.adf`, `.uae`, `.ipf`, `.dms`, `.dmz`, `.adz`, `.lha`, `.hdf`, `.exe`, `.m3u`, `.zip` |
| [fsuae: A4000](#fsuae:_A4000) | `.adf`, `.uae`, `.ipf`, `.dms`, `.dmz`, `.adz`, `.lha`, `.hdf`, `.exe`, `.m3u`, `.zip` |
| [amiberry: A1200](#amiberry:_A1200) | `.adf`, `.uae`, `.ipf`, `.dms`, `.dmz`, `.adz`, `.lha`, `.hdf`, `.exe`, `.zip` |
| [amiberry: A4000](#amiberry:_A4000) | `.adf`, `.uae`, `.ipf`, `.dms`, `.dmz`, `.adz`, `.lha`, `.hdf`, `.exe`, `.zip` |
| [libretro: puae](#libretro:_puae) | `.adf`, `.uae`, `.ipf`, `.dms`, `.dmz`, `.adz`, `.lha`, `.hdf`, `.exe`, `.m3u`, `.zip` |
| [libretro: puae2021](#libretro:_puae2021) | `.adf`, `.uae`, `.ipf`, `.dms`, `.dmz`, `.adz`, `.lha`, `.hdf`, `.exe`, `.m3u`, `.zip` |
| [libretro: uae4arm](#libretro:_uae4arm) | `.adf`, `.uae`, `.ipf`, `.dms`, `.dmz`, `.adz`, `.lha`, `.hdf`, `.exe`, `.m3u`, `.zip` |

## BIOS
If only interested in emulating the Amiga 1200, only `bios/amiga/kick40068.A1200` is needed. The rest are for if desiring to emulate a specific model or needing to work around an in-game bug which only affects certain OS versions.

| MD5 checksum | Share file path | Description | Notes |
| `b7cc148386aa631136f510cd29e42fc3` | `bios/amiga/kick39106.A1200` | Kickstart v3.0 rev 39.106 | AmigaOS 3.0 (the OS bundled since 1992) |
| `646773759326fbac3b2311fd8c8793ee` | `bios/amiga/kick40068.A1200` | Kickstart v3.1 rev 40.068 | AmigaOS 3.1 (the OS bundled since 1993) |
| `9bdedde6a4f33555b4a270c8ca53297d` | `bios/amiga/kick40068.A4000` | Kickstart v3.1 rev 40.068 | AmigaOS 3.1 (the OS bundled since 1993) |
| `b7cc148386aa631136f510cd29e42fc3` | `bios/amiga/amiga-os-300-a1200.rom` | Kickstart v3.0 rev 39.106 | AmigaOS 3.0 (the OS bundled since 1992) |
| `646773759326fbac3b2311fd8c8793ee` | `bios/amiga/amiga-os-310-a1200.rom` | Kickstart v3.1 rev 40.068 | AmigaOS 3.1 (the OS bundled since 1993) |
| `413590e50098a056cfec418d3df0212d` | `bios/amiga/amiga-os-310-a3000.rom` | Kickstart v3.1 r40.68 (1993)(Commodore)(A3000).rom | AmigaOS 3.1 (the OS bundled since 1993). Only needed if you explicitly need to emulate Amiga 3000 (FIXME what why isn't this mentioned in the summary?). |
| `9bdedde6a4f33555b4a270c8ca53297d` | `bios/amiga/amiga-os-310-a4000.rom` | Kickstart v3.1 rev 40.068 | AmigaOS 3.1 (the OS bundled since 1993) |
| `730888fb1bd9a3606d51f772ed136528` | `bios/amiga/amiga-os-310.rom` | Kickstart v3.1 r40.68 (1993)(Commodore)(A4000)[h Cloanto].rom | AmigaOS 3.1 (the OS bundled since 1993). Is used as a base if `amiga-os-310-a4000.rom` is not available. Otherwise, is not required. |

## ROMs
Place your Amiga 1200 ROMs in `/userdata/roms/amiga1200`.

## Emulators
### fsuae
#### fsuae configuration
Standardized features available to all cores of this emulator: `amiga1200.videomode`, `amiga1200.padtokeyboard`, `amiga1200.videomode`, `amiga1200.ratio`, `amiga1200.bezel`, `amiga1200.bezel_stretch`, `amiga1200.hud`, `amiga1200.hud_corner`, `amiga1200.bezel.tattoo`, `amiga1200.bezel.tattoo_corner`, `amiga1200.bezel.tattoo_file`, `amiga1200.bezel.resize_tattoo`

### amiberry
#### amiberry configuration
Standardized features available to all cores of this emulator: `amiga1200.videomode`, `amiga1200.padtokeyboard`, `amiga1200.videomode`, `amiga1200.ratio`, `amiga1200.bezel`, `amiga1200.bezel_stretch`, `amiga1200.hud`, `amiga1200.hud_corner`, `amiga1200.bezel.tattoo`, `amiga1200.bezel.tattoo_corner`, `amiga1200.bezel.tattoo_file`, `amiga1200.bezel.resize_tattoo`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **LINE MODE `amiga1200.amiberry_linemode`** | Adjust screen line draw mode.\\ => SINGLE `none`, DOUBLE `double`, SCANLINES `scanlines`. |
| **VIDEO RESOLUTION `amiga1200.amiberry_resolution`** | Manually define which internal resolution to use. AUTO = High.\\ => Low `lores`, High `hires`, Super high `superhires`. |
| **SCALING METHOD `amiga1200.amiberry_scalingmethod`** | Change pixel scaling and filtering method.\\ => Automatic `automatic`, Pixelated (Nearest) `pixelated`, Smooth (Linear) `smooth`. |
| **REMOVE INTERLACE ARTIFACTS `amiga1200.amiberry_flickerfixer`** | Fix flickering in a static screen like Workbench.\\ => ON `True`, OFF `False`. |
| **AUTO HEIGHT `amiga1200.amiberry_auto_height`** | Resize automatically screen height.\\ => ON `True`, OFF `False`. |

### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: puae
##### libretro: puae configuration
Standardized features for this core: `amiga1200.rewind`, `amiga1200.autosave`, `amiga1200.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **AMIGA MODEL `global.puae_model`** | Force a specific model and prevent tags detection\\ => Autodetect (by game name tag) `automatic`, A500 (512KB Chip + 512KB Slow) `A500`, A500+ (1MB Chip) `A500PLUS`, A600 (2MB Chip + 8MB Fast) `A600`, A1200 (2MB Chip + 8MB Fast) `A1200`, A4000/040 (2MB Chip + 8MB Fast) `A4040`, CDTV (1MB Chip) `CDTV`, CD32 Default (2MB Chip) `CD32`, CD32 (2MB Chip + 8MB Fast) `CD32FR`. |
| **CPU COMPATIBILITY `global.cpu_compatibility`** | Help games which are too quick or that have bugs\\ => Normal `normal`, More compatible `compatible`, Cycle-exact `exact`. |
| **CPU MULTIPLIER (OVERCLOCK) `global.cpu_multiplier`** | Works with 'Cycle-exact' mode and for a few games\\ => Default by model `0`,  3.54 MHz `1`,  7.09 MHz (A500 speed) `2`, 14.18 MHz (A1200 speed) `4`, 28.37 MHz `8`, 35.46 MHz `10`, 42.56 MHz `12`, 56.75 MHz `16`. |
| **CPU SPEED (OVERCLOCK) `global.cpu_throttle`** | Ignored with 'Cycle-exact'\\ => -90% `-900.0`, -80% `-800.0`, -70% `-700.0`, -60% `-600.0`, -50% `-500.0`, -40% `-400.0`, -30% `-300.0`, -20% `-200.0`, -10% `-100.0`, Default `0.0`, +100% `1000.0`, +200% `2000.0`, +300% `3000.0`, +400% `4000.0`, +500% `5000.0`, +600% `6000.0`, +700% `7000.0`, +800% `8000.0`, +900% `9000.0`, +1000% `10000.0`. |
| **VIDEO STANDARD `global.video_standard`** | Switch frequency and resolution by region\\ => PAL 50Hz - 288/576px `PAL`, NTSC 60Hz - 240/480px `NTSC`. |
| **VIDEO RESOLUTION `global.video_resolution`** | Increase the video resolution\\ => Low 360p `lores`, High 720p `hires`, Super-high 1440p `superhires`. |
| **ZOOM MODE `global.zoom_mode`** | Crops the borders to fit various host screens\\ => Off `none`, Autofit screen `automatic`, minimum `minimum`, smaller `smaller`, small `small`, medium `medium`, large `large`, larger `larger`, maximum `maximum`. |
| **FRAMESKIP `global.gfx_framerate`** | Skip frames to improve performance (smoothness)\\ => Off `disabled`, 1 `1`, 2 `2`. |
| **MOUSE SPEED `global.mouse_speed`** | Affects mouse speed globally.\\ => original `100`, 50% `50`, 70% `70`, 120% `120`, 150% `150`, 170% `170`, 200% `200`. |
| Settings specific to amiga500 ||
| **FLOPPY TURBO SPEED `amiga500.puae_floppy_speed`** | Removes loading but can add possible glitches/crashes\\ => Off `100`, On `0`. |
| **2P GAMEPAD MAPPING (KEYRAH) `amiga500.keyrah_mapping`** | Keypad to joyport mappings for 2 players\\ => Off `disabled`, On `enabled`. |
| **WHDLOAD LAUNCHER `amiga500.whdload`** | Enable launching pre-installed WHDLoad installs\\ => Off `disabled`, On `config`. |
| **JUMP ON B `amiga500.pad_options`** | Makes second fire button press up\\ => Off `disabled`, On `jump`. |
| **DISABLE EMULATOR JOYSTICK `amiga500.disable_joystick`** | Passes all physical keyboard events for Pad2Key\\ => Off `disabled`, On `enabled`. |
| **CONTROLLER 1 TYPE `amiga500.controller1_puae`** | Select controller type for Amiga P1\\ => Retropad `1`, CD32 Pad `517`, Analog Joystick `773`, Joystick `261`, Keyboard `259`. |
| **CONTROLLER 2 TYPE `amiga500.controller2_puae`** | Select controller type for Amiga P2\\ => Retropad `1`, CD32 Pad `517`, Analog Joystick `773`, Joystick `261`, Keyboard `259`. |
| Settings specific to amiga1200 ||
| **FLOPPY TURBO SPEED `amiga1200.puae_floppy_speed`** | Removes loading but can add possible glitches/crashes\\ => Off `100`, On `0`. |
| **2P GAMEPAD MAPPING (KEYRAH) `amiga1200.keyrah_mapping`** | Keypad to joyport mappings for 2 players\\ => Off `disabled`, On `enabled`. |
| **WHDLOAD LAUNCHER `amiga1200.whdload`** | Enable launching pre-installed WHDLoad installs\\ => Off `disabled`, On `config`. |
| **JUMP ON B `amiga1200.pad_options`** | Makes second fire button press up\\ => Off `disabled`, On `jump`. |
| **DISABLE EMULATOR JOYSTICK `amiga1200.disable_joystick`** | Passes all physical keyboard events for Pad2Key\\ => Off `disabled`, On `enabled`. |
| **CONTROLLER 1 TYPE `amiga1200.controller1_puae`** | Select controller type for Amiga P1\\ => Retropad `1`, CD32 Pad `517`, Analog Joystick `773`, Joystick `261`, Keyboard `259`. |
| **CONTROLLER 2 TYPE `amiga1200.controller2_puae`** | Select controller type for Amiga P2\\ => Retropad `1`, CD32 Pad `517`, Analog Joystick `773`, Joystick `261`, Keyboard `259`. |
| Settings specific to amigacd32 ||
| **BOOT ANIMATION FIRST `amigacd32.puae_cd_startup_delayed_insert`** | Inserts CD during boot animation to prevent loading fail\\ => Off `disabled`, On `enabled`. |
| **CD TURBO SPEED `amigacd32.puae_cd_speed`** | Removes loading but can add possible glitches/crashes\\ => Off `100`, On `0`. |
| **JUMP ON A `amigacd32.puae_cd32pad_options`** | Makes Blue button press Up\\ => Off `disabled`, On `jump`. |
| Settings specific to amigacdtv ||
| **BOOT ANIMATION FIRST `amigacdtv.puae_cd_startup_delayed_insert`** | Inserts CD during boot animation prevent loading fail\\ => Off `disabled`, On `enabled`. |
| **CD TURBO SPEED `amigacdtv.puae_cd_speed`** | Removes loading but can add possible glitches/crashes\\ => Off `100`, On `0`. |

#### libretro: puae2021
An older version of PUAE that's more inaccurate but faster on weaker hardware such as the Raspberry Pi.

##### libretro: puae2021 configuration
Standardized features for this core: `amiga1200.rewind`, `amiga1200.autosave`, `amiga1200.padtokeyboard`

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
| Settings specific to amiga1200 ||
| **FLOPPY TURBO SPEED `amiga1200.puae_floppy_speed`** | Removes loading but can add possible glitches/crashes.\\ => Off `100`, On `0`. |
| **2P GAMEPAD MAPPING (KEYRAH) `amiga1200.keyrah_mapping`** | Keypad to joyport mappings for 2 players.\\ => Off `disabled`, On `enabled`. |
| **WHDLOAD LAUNCHER `amiga1200.whdload`** | Enable launching pre-installed WHDLoad installs.\\ => Off `disabled`, On `config`. |
| **JUMP ON B `amiga1200.pad_options`** | Makes second fire button press up instead.\\ => Off `disabled`, On `jump`. |
| **DISABLE EMULATOR JOYSTICK `amiga1200.disable_joystick`** | Passes all physical keyboard events for Pad2Key.\\ => Off `disabled`, On `enabled`. |
| **CONTROLLER 1 TYPE `amiga1200.controller1_puae`** | Select controller type for Amiga P1.\\ => Retropad `1`, CD32 Pad `517`, Analog Joystick `773`, Joystick `261`, Keyboard `259`. |
| **CONTROLLER 2 TYPE `amiga1200.controller2_puae`** | Select controller type for Amiga P2.\\ => Retropad `1`, CD32 Pad `517`, Analog Joystick `773`, Joystick `261`, Keyboard `259`. |

#### libretro: uae4arm
There is no configuration available for this emulator (yet).

## Controls
Here are the default Amiga 1200's controls shown on a [Batocera Retropad](:configure_a_controller):

If using [libretro: PUAE](#libretro:_puae), controls can be remapped per game or per folder by [editing its core options](:remapping_controls_per_emulator#libretropuae).

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).