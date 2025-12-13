# Amiga 500

**Source:** https://wiki.batocera.org/systems:amiga500  
**Last fetched:** 2025-12-06 16:18:33

---

This article needs some TLC. Read at your own risk.

# Amiga 500
The Amiga 500 (a.k.a. Amiga OCS/ECS a.k.a. Amiga home computer) is a line of personal computers developed by Commodore/Escom/QuikPak. Its first, the Amiga 1000 model was released in 1985.

Early models were released with a Motorola 6800 CPU. These are referred to as the Original ChipSet (OCS). These include:
- Amiga 1000
- Amiga 2000 A-model
- Amiga 500
- Amiga 2000
- Amiga 2500((Technically the Amiga 2500 could be purchased with a 68030 CPU but it is still largely considered OCS.))
- Amiga 1500

The Amiga 500 is the most well-known of the computer line, so far as to skew the perception of the "Amiga home computer line" into being the "Amiga 500 line", even though it was the third in the family to be released.

Towards the end of the OCS lifespan, newer models with a Motorola 68030 CPU were released. These are referred to as the Enhance ChipSet (ECS). These include:
- Amiga 3000
- Amiga 3000T
- Amiga 3000UX
- Amiga 500+
- Amiga 600

Then the Advanced Graphics Architecture (AGA) models were released, which are considered [a separate system in Batocera](systems:amiga1200).

When available, the [Amiga 1200](systems:amiga1200) version of a game is usually superior and preferred.

The ECS chipset is capable of switching between PAL/NTSC modes as needed. Outside of that, the ECS chipset didn't offer much enhancement for games, just software, so Batocera really only concerns itself with the Amiga 500.

This system scrapes metadata for the "amiga" group and loads the `amiga500` set from the currently selected theme, if available.

Grouped with the "amiga" group of systems.

### Quick reference
- **Accepted ROM formats:** `.adf`, `.uae`, `.ipf`, `.dms`, `.dmz`, `.adz`, `.lha`, `.hdf`, `.exe`, `.m3u`, `.zip`
- **Folder:** `/userdata/roms/amiga500`

| Emulators | Accepted ROM formats |
| [fsuae: A500](#fsuae:_A500) | `.adf`, `.uae`, `.ipf`, `.dms`, `.dmz`, `.adz`, `.lha`, `.hdf`, `.exe`, `.m3u`, `.zip` |
| [fsuae: A500+](#fsuae:_A500+) | `.adf`, `.uae`, `.ipf`, `.dms`, `.dmz`, `.adz`, `.lha`, `.hdf`, `.exe`, `.m3u`, `.zip` |
| [fsuae: A600](#fsuae:_A600) | `.adf`, `.uae`, `.ipf`, `.dms`, `.dmz`, `.adz`, `.lha`, `.hdf`, `.exe`, `.m3u`, `.zip` |
| [fsuae: A1000](#fsuae:_A1000) | `.adf`, `.uae`, `.ipf`, `.dms`, `.dmz`, `.adz`, `.lha`, `.hdf`, `.exe`, `.m3u`, `.zip` |
| [fsuae: A3000](#fsuae:_A3000) | `.adf`, `.uae`, `.ipf`, `.dms`, `.dmz`, `.adz`, `.lha`, `.hdf`, `.exe`, `.m3u`, `.zip` |
| [amiberry: A500](#amiberry:_A500) | `.adf`, `.uae`, `.ipf`, `.dms`, `.dmz`, `.adz`, `.lha`, `.hdf`, `.exe`, `.zip` |
| [amiberry: A500+](#amiberry:_A500+) | `.adf`, `.uae`, `.ipf`, `.dms`, `.dmz`, `.adz`, `.lha`, `.hdf`, `.exe`, `.zip` |
| [libretro: puae](#libretro:_puae) | `.adf`, `.uae`, `.ipf`, `.dms`, `.dmz`, `.adz`, `.lha`, `.hdf`, `.exe`, `.m3u`, `.zip` |

## BIOS
If you're only interested in Amiga 500 games then the only BIOS that's required is `kick34005.A500`. The rest are if you'd like to emulate specific models/revisions, or need to work around an in-game bug that only affects certain OS versions.

| MD5 checksum | Share file path | Description | Notes |
| `85ad74194e87c08904327de1a9443b7a` | `bios/amiga/kick33180.A500` | Kickstart v1.2 rev 33.180 | AmigaOS 1.2 (the first OS bundled with the Amiga 1000 from 1985) |
| `82a21c1890cae844b3df741f2762d48d` | `bios/amiga/kick34005.A500` | Kickstart v1.3 rev 34.005 | AmigaOS 1.3 (the OS bundled since 1987, more common) |
| `dc10d7bdd1b6f450773dfb558477c230` | `bios/amiga/kick37175.A500` | Kickstart v2.04 rev 37.175 | AmigaOS 2.04 (the OS bundled since 1990) |
| `465646c9b6729f77eea5314d1f057951` | `bios/amiga/kick37350.A600` | Kickstart v2.05 rev 37.350 | AmigaOS 2.05 (the OS bundled since 1992) |
| `e40a5dfb3d017ba8779faba30cbd1c8e` | `bios/amiga/kick40063.A600` | Kickstart v3.1 rev 40.063 | AmigaOS 3.1 |
| `85ad74194e87c08904327de1a9443b7a` | `bios/amiga/amiga-os-120.rom` | Kickstart v1.2 rev 33.180 | AmigaOS 1.2 (the first OS bundled with the Amiga 1000 from 1985) |
| `82a21c1890cae844b3df741f2762d48d` | `bios/amiga/amiga-os-130.rom` | Kickstart v1.3 rev 34.005 | AmigaOS 1.3 (the OS bundled since 1987, more common) |
| `dc10d7bdd1b6f450773dfb558477c230` | `bios/amiga/amiga-os-204.rom` | Kickstart v2.04 rev 37.175 | AmigaOS 2.04 (the OS bundled since 1990) |
| `465646c9b6729f77eea5314d1f057951` | `bios/amiga/amiga-os-205.rom` | Kickstart v2.05 rev 37.350 | AmigaOS 2.05 (the OS bundled since 1992) |
| `e40a5dfb3d017ba8779faba30cbd1c8e` | `bios/amiga/amiga-os-310-a600.rom` | Kickstart v3.1 rev 40.063 | AmigaOS 3.1 (the OS bundled since 1993) |

The year of release of each OS version is an estimate.

## ROMs
Place your Amiga 500 ROMs in `/userdata/roms/amiga500`.

### Multi-disk games

Do standard m3u playlists work?

If using a libretro core, it is possible to use a single archive to store multi-disk games. Put the multiple disks in a ZIP archive and add `(MD)` to its filename. For example, the game Operation Wolf may exist as the following:

```

roms/amiga500/
     ├─ Operation Wolf (Disk 1).adf
     └─ Operation Wolf (Disk 2).adf

```

Compress the two disk files into a single ZIP and add `(MD)` to its filename:

```

roms/amiga500/
     └─ Operation Wolf (MD).zip
        ├─ Operation Wolf (Disk 1).adf
        └─ Operation Wolf (Disk 2).adf

```

Multi-disc features can then be access from RetroArch's Quick Menu (`[HOTKEY]` + ). (FIXME where exactly though?)

## Emulators
### fsuae
#### fsuae configuration
Standardized features available to all cores of this emulator: `amiga500.videomode`, `amiga500.ratio`, `amiga500.padtokeyboard`

### amiberry
#### amiberry configuration
Standardized features available to all cores of this emulator: `amiga500.videomode`, `amiga500.ratio`, `amiga500.padtokeyboard`

### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: puae
##### libretro: puae configuration
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
An older version of PUAE which is more innaccurate but runs faster on weaker hardware (such as the Raspberry Pi).

##### libretro: puae2021 configuration
Standardized features for this core: `amiga500.rewind`, `amiga500.autosave`, `amiga500.padtokeyboard`

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
| Settings specific to amiga500 ||
| **FLOPPY TURBO SPEED `amiga500.puae_floppy_speed`** | Removes loading but can add possible glitches/crashes.\\ => Off `100`, On `0`. |
| **2P GAMEPAD MAPPING (KEYRAH) `amiga500.keyrah_mapping`** | Keypad to joyport mappings for 2 players.\\ => Off `disabled`, On `enabled`. |
| **WHDLOAD LAUNCHER `amiga500.whdload`** | Enable launching pre-installed WHDLoad installs.\\ => Off `disabled`, On `config`. |
| **DISABLE EMULATOR JOYSTICK `amiga500.disable_joystick`** | Passes all physical keyboard events for Pad2Key.\\ => Off `disabled`, On `enabled`. |
| **CONTROLLER 1 TYPE `amiga500.controller1_puae`** | Select controller type for Amiga P1.\\ => Retropad `1`, CD32 Pad `517`, Analog Joystick `773`, Joystick `261`, Keyboard `259`. |
| **CONTROLLER 2 TYPE `amiga500.controller2_puae`** | Select controller type for Amiga P2.\\ => Retropad `1`, CD32 Pad `517`, Analog Joystick `773`, Joystick `261`, Keyboard `259`. |

#### libretro: uae4arm
No configuration is available for this emulator (yet).

## Controls
Here are the default Amiga OCS/ECS's controls shown on a [Batocera Retropad](:configure_a_controller):

If using [libretro: PUAE](#libretro:_puae), controls can be remapped per game or per folder by [editing its core options](:remapping_controls_per_emulator#libretropuae).

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).