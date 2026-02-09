# Nintendo Game Boy Advance

**Source:** https://wiki.batocera.org/systems:gba  
**Last fetched:** 2025-12-06 16:19:02

---

# Nintendo Game Boy Advance
The Game Boy Advance (often shortened to GBA) is a 32-bit handheld video game console developed by Nintendo. It is the successor to the Game Boy Color. It was released in Japan on March 21, 2001; in North America on June 11, 2001; in Australia and Europe on June 22, 2001. It has a ARM7TDMI CPU at 16.78 MHz and a Zilog Z80 CPU at 8 MHz and 4 MHz. It has 32KB of RAM and 96KB of VRAM. 

This system scrapes metadata for the "gba" group and loads the `gba` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Cores available:** [libretro: mGBA](#libretro:_mgba), [libretro: vba-m](#libretro:_VBA-M), [libretro: gpsp](#libretro:_gpsp)
- **Folder:** `/userdata/roms/gba`
- **Accepted ROM formats:** `.gba`, `.zip`, `.7z`

## BIOS
The BIOS file are optional for GBA emulation, however it is the only way to see the cool boot animation on start-up.

| MD5 checksum | Share file path | Description |
| `a860e8c0b6d573d191e4ec7db1b1e4f6` | `bios/gba_bios.bin` | Game Boy Advance BIOS |

## ROMs
Place your Game Boy Advance ROMs in `/userdata/roms/gba`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `gba.videomode`, `gba.ratio`, `gba.smooth`, `gba.shaders`, `gba.pixel_perfect`, `gba.decoration`, `gba.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `gba.gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `gba.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `gba.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: mGBA
mGBA is an emulator for running Game Boy Advance games. It aims to be faster and more accurate than many existing Game Boy Advance emulators, as well as adding features that other emulators lack. It also supports Game Boy and Game Boy Color games.

We use the latest [libretro](https:*github.com/libretro/mgba) core. See the [official documentation](https:*docs.libretro.com/library/mgba/) for more information.

##### libretro: mGBA configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **SHOW BIOS BOOTLOGO `global.skip_bios_mgba`** | Show BIOS animation when starting content. Requires BIOS file to be present.\\ => Off `True`, On `False`. |
| Settings specific to gb ||
| **SUPER GB BORDERS `gb.sgb_borders`** | Only for Super Game Boy enhanced games.\\ => Off `False`, On `True`. |
| **COLOR CORRECTION `gb.color_correction`** | Simulate LCD color inaccuracy. More accurate to how the game would have appeared on the real hardware.\\ => Off `False`, On `GBA`. |
| Settings specific to gbc ||
| **SUPER GB BORDERS `gbc.sgb_borders`** | Only for Super Game Boy enhanced games.\\ => Off `False`, On `True`. |
| **COLOR CORRECTION `gbc.color_correction`** | Simulate LCD color inaccuracy. More accurate to how the game would have appeared on the real hardware.\\ => Off `False`, On `GBC`. |
| Settings specific to gba ||
| **SOLAR SENSOR LEVEL `gba.solar_sensor_level`** | Can be used by games that employed the use of a [solar sensor](https://boktai.neoseeker.com/wiki/Solar_sensor) on their cartridges. Use it for the few solar sensor games available, namely the Boktai series.\\ => 0 `0`, 1 `1`, 2 `2`, 3 `3`, 4 `4`, 5 `5`, 6 `6`, 7 `7`, 8 `8`, 9 `9`, 10 `10`. |
| **FRAMESKIP `gba.frameskip_mgba`** | Skip frames to improve performance (smoothness)\\ => 0 `0`, 1 `1`, 2 `2`, 3 `3`, 4 `4`, 5 `5`, 6 `6`, 7 `7`, 8 `8`, 9 `9`, 10 `10`. |

#### libretro: VBA-M
VBA-M is a Game Boy Advance emulator with the goal to improve upon VisualBoyAdvance by integrating the best features from the various builds floating around. It also supports Game Boy, Game Boy Color and Super Game Boy (borders, palette).

##### libretro: VBA-M configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings specific to gb ||
| **COLORIZATION `gb.palettes`** | Set the Game Boy palettes to use\\ => original gameboy `original gameboy`, black and white `black and white`, gba sp `gba sp`, blue sea `blue sea`, dark knight `dark knight`, green forest `green forest`, hot desert `hot desert`, pink dreams `pink dreams`, weird colors `weird colors`. |
| **COLOR CORRECTION `gb.gbcoloroption_gb`** | Simulate LCD color inaccuracy. More accurate to how the game would have appeared on the real hardware.\\ => Off `disabled`, On `enabled`. |
| **SUPER GB BORDERS `gb.showborders_gb`** | Only for Super Game Boy enhanced games.\\ => Off `disabled`, On `enabled`. |
| Settings specific to gbc ||
| **COLOR CORRECTION `gbc.gbcoloroption_gbc`** | Simulate LCD color inaccuracy. More accurate to how the game would have appeared on the real hardware.\\ => Off `disabled`, On `enabled`. |
| **SUPER GB BORDERS `gbc.showborders_gbc`** | Only for Super Game Boy enhanced games.\\ => Off `disabled`, On `enabled`. |
| Settings specific to gba ||
| **SOLAR SENSOR LEVEL `gba.solarsensor`** | Can be used by games that employed the use of a [solar sensor](https://boktai.neoseeker.com/wiki/Solar_sensor) on their cartridges. Use it for the few solar sensor games available, namely the Boktai series.\\ => 0 `0`, 1 `1`, 2 `2`, 3 `3`, 4 `4`, 5 `5`, 6 `6`, 7 `7`, 8 `8`, 9 `9`, 10 `10`. |
| **SENSOR SENSITIVITY (GYROSCOPE) `gba.gyro_sensitivity`** | For Gyro-enabled games (bound to left analog stick)\\ => 10 `10`, 15 `15`, 20 `20`, 25 `25`, 30 `30`, 35 `35`, 40 `40`, 45 `45`, 50 `50`, 55 `55`, 60 `60`, 65 `65`, 70 `70`, 75 `75`, 80 `80`, 85 `85`, 90 `90`, 95 `95`, 100 `100`, 105 `105`, 110 `110`, 115 `115`, 120 `120`. |
| **SENSOR SENSITIVITY (TILT) `gba.tilt_sensitivity`** | For Gyro-enabled games (bound to right analog stick)\\ => 10 `10`, 15 `15`, 20 `20`, 25 `25`, 30 `30`, 35 `35`, 40 `40`, 45 `45`, 50 `50`, 55 `55`, 60 `60`, 65 `65`, 70 `70`, 75 `75`, 80 `80`, 85 `85`, 90 `90`, 95 `95`, 100 `100`, 105 `105`, 110 `110`, 115 `115`, 120 `120`. |

#### libretro: gpsp
##### libretro: gpsp configuration
## Controls
Here are the default Game Boy Advance's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).