# Nintendo Game Boy Color

**Source:** https://wiki.batocera.org/systems:gbc  
**Last fetched:** 2025-12-06 16:19:03

---

# Nintendo Game Boy Color
The Game Boy Color (GBC) is a 8-bit, fourth-generation handheld console released by [Nintendo](wp>Nintendo) on November 18, 1998. The Game Boy Color uses the same LR35902 core as the [original Game Boy](systems:gb); while it is clocked at 8.38 MHz, it can be underclocked to 4.19 MHz for backwards-compatibility purposes. It was named such from its color screen, but it also had a larger memory size and a faster CPU. The hardware similarities allow cross-compatibility between the two platforms and they are often treated as one.

The "Color" spelling remains consistent throughout the world, even in countries that opt to use the British spelling: "colour".

This system scrapes metadata for the "gbc" group and loads the `gbc` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Cores available:** [libretro: Gambatte](#libretro:_gambatte), [libretro: mGBA](#libretro:_mgba), [libretro: VBA-M](#libretro:_vba-m), [libretro: MesenS](#libretro:_mesens)
- **Folder:** `/userdata/roms/gbc`
- **Accepted ROM formats:** `.gbc`, `.zip`, `.7z`

## BIOS
No Game Boy Color emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Game Boy Color ROMs in `/userdata/roms/gbc`.

To play two virtually linked Game Boy Color instances for multiplayer games, refer to [GBC2Players](systems:gbc2players).

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `gbc.videomode`, `gbc.ratio`, `gbc.smooth`, `gbc.shaders`, `gbc.pixel_perfect`, `gbc.decoration`, `gbc.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `gbc.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `gbc.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `gbc.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: Gambatte
Gambatte is an accuracy-focused, open-source, cross-platform Game Boy Color emulator written in C++. It is based on hundreds of corner case hardware tests, as well as previous documentation and reverse engineering efforts. The accuracy of the emulator is among the highest and is based off numerous reverse engineering tests and document studies.

We use the latest [libretro](https:*github.com/libretro/gambatte-libretro) core. See the [official documentation](https:*docs.libretro.com/library/gambatte/) for more information.

##### libretro: Gambatte configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **SHOW BIOS BOOTLOGO `global.gb_bootloader`** | Show BIOS animation when starting content\\ => Off `disabled`, On `enabled`. |
| **GHOSTING EFFECT `global.gb_mix_frames`** | Simulate LCD ghosting effects\\ => Off `disabled`, Simple (Accurate) `mix`, Simple (Fast) `mix_fast`, LCD Ghosting (Accurate) `lcd_ghosting`, LCD Ghosting (Fast) `lcd_ghosting_fast`. |
| Settings specific to gbc ||
| **COLOR CORRECTION `gbc.gbc_color_correction`** | Adjusts output colors to imitate real hardware\\ => Off `disabled`, On `always`. |
| Settings specific to gb ||
| **COLORIZATION `gb.gb_colorization`** | Set the Game Boy palettes to use\\ => Off `none`, GB - Smart Coloring `GB - SmartColor`, GB - DMG `GB - DMG`, GB - Light `GB - Light`, GB - Pocket `GB - Pocket`, GB - Black and White `GB - Disabled`, GBC - Blue `GBC - Blue`, GBC - Brown `GBC - Brown`, GBC - Dark Blue `GBC - Dark Blue`, GBC - Dark Brown `GBC - Dark Brown`, GBC - Dark Green `GBC - Dark Green`, GBC - Grayscale `GBC - Grayscale`, GBC - Green `GBC - Green`, GBC - Inverted `GBC - Inverted`, GBC - Orange `GBC - Orange`, GBC - Pastel Mix `GBC - Pastel Mix`, GBC - Red `GBC - Red`, GBC - Yellow `GBC - Yellow`, SGB - 1A `SGB - 1A`, SGB - 1B `SGB - 1B`, SGB - 1C `SGB - 1C`, SGB - 1D `SGB - 1D`, SGB - 1E `SGB - 1E`, SGB - 1F `SGB - 1F`, SGB - 1G `SGB - 1G`, SGB - 1H `SGB - 1H`, SGB - 2A `SGB - 2A`, SGB - 2B `SGB - 2B`, SGB - 2C `SGB - 2C`, SGB - 2D `SGB - 2D`, SGB - 2E `SGB - 2E`, SGB - 2F `SGB - 2F`, SGB - 2G `SGB - 2G`, SGB - 2H `SGB - 2H`, SGB - 3A `SGB - 3A`, SGB - 3B `SGB - 3B`, SGB - 3C `SGB - 3C`, SGB - 3D `SGB - 3D`, SGB - 3E `SGB - 3E`, SGB - 3F `SGB - 3F`, SGB - 3G `SGB - 3G`, SGB - 3H `SGB - 3H`, SGB - 4A `SGB - 4A`, SGB - 4B `SGB - 4B`, SGB - 4C `SGB - 4C`, SGB - 4D `SGB - 4D`, SGB - 4E `SGB - 4E`, SGB - 4F `SGB - 4F`, SGB - 4G `SGB - 4G`, SGB - 4H `SGB - 4H`, Special 1 `Special 1`, Special 2 `Special 2`, Special 3 `Special 3`, Special 4 (TI-83 Legacy) `Special 4 (TI-83 Legacy)`, TWB64 - Pack 1 `TWB75 - WonderSwan`, TWB64 - Pack 2 `TWB76 - Yellow Banana`. |

#### libretro: mGBA
mGBA is an emulator for running Game Boy Advance games. It aims to be faster and more accurate than many existing Game Boy Advance emulators, as well as adding features that other emulators lack. It also supports Game Boy and Game Boy Color games.

##### libretro: mGBA configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **SHOW BIOS BOOTLOGO `global.skip_bios_mgba`** | Show BIOS animation when starting content\\ => Off `True`, On `False`. |
| Settings specific to gb ||
| **SUPER GB BORDERS `gb.sgb_borders`** | Only for Super Game Boy enhanced games\\ => Off `False`, On `True`. |
| **COLOR CORRECTION `gb.color_correction`** | Adjusts output colors to feel real hardware\\ => Off `False`, On `GBA`. |
| Settings specific to gbc ||
| **SUPER GB BORDERS `gbc.sgb_borders`** | Only for Super Game Boy enhanced games\\ => Off `False`, On `True`. |
| **COLOR CORRECTION `gbc.color_correction`** | Adjusts output colors to feel real hardware\\ => Off `False`, On `GBC`. |
| Settings specific to gba ||
| **SOLAR SENSOR LEVEL `gba.solar_sensor_level`** | Only for games that employed it (for Boktai)\\ => 0 `0`, 1 `1`, 2 `2`, 3 `3`, 4 `4`, 5 `5`, 6 `6`, 7 `7`, 8 `8`, 9 `9`, 10 `10`. |
| **FRAMESKIP `gba.frameskip_mgba`** | Skip frames to improve performance (smoothness)\\ => 0 `0`, 1 `1`, 2 `2`, 3 `3`, 4 `4`, 5 `5`, 6 `6`, 7 `7`, 8 `8`, 9 `9`, 10 `10`. |

#### libretro: VBA-M
VBA-M is a Game Boy Advance emulator with the goal to improve upon VisualBoyAdvance by integrating the best features from the various builds floating around. It also supports Game Boy, Game Boy Color and Super Game Boy (both borders and palettes).

##### libretro: VBA-M configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings specific to gb ||
| **COLORIZATION `gb.palettes`** | Set the Game Boy palettes to use\\ => original gameboy `original gameboy`, black and white `black and white`, gba sp `gba sp`, blue sea `blue sea`, dark knight `dark knight`, green forest `green forest`, hot desert `hot desert`, pink dreams `pink dreams`, weird colors `weird colors`. |
| **COLOR CORRECTION `gb.gbcoloroption_gb`** | Adjusts output colors to simulate real hardware\\ => Off `disabled`, On `enabled`. |
| **SUPER GB BORDERS `gb.showborders_gb`** | Only for Super Game Boy enhanced games\\ => Off `disabled`, On `enabled`. |
| Settings specific to gbc ||
| **COLOR CORRECTION `gbc.gbcoloroption_gbc`** | Adjusts output colors to simulate real hardware\\ => Off `disabled`, On `enabled`. |
| **SUPER GB BORDERS `gbc.showborders_gbc`** | Only for Super Game Boy enhanced games\\ => Off `disabled`, On `enabled`. |
| Settings specific to gba ||
| **SOLAR SENSOR LEVEL `gba.solarsensor`** | Only for games that employed it (for Boktai)\\ => 0 `0`, 1 `1`, 2 `2`, 3 `3`, 4 `4`, 5 `5`, 6 `6`, 7 `7`, 8 `8`, 9 `9`, 10 `10`. |
| **SENSOR SENSITIVITY (GYROSCOPE) `gba.gyro_sensitivity`** | For Gyro-enabled games (bound to left analog stick)\\ => 10 `10`, 15 `15`, 20 `20`, 25 `25`, 30 `30`, 35 `35`, 40 `40`, 45 `45`, 50 `50`, 55 `55`, 60 `60`, 65 `65`, 70 `70`, 75 `75`, 80 `80`, 85 `85`, 90 `90`, 95 `95`, 100 `100`, 105 `105`, 110 `110`, 115 `115`, 120 `120`. |
| **SENSOR SENSITIVITY (TILT) `gba.tilt_sensitivity`** | For Gyro-enabled games (bound to right analog stick)\\ => 10 `10`, 15 `15`, 20 `20`, 25 `25`, 30 `30`, 35 `35`, 40 `40`, 45 `45`, 50 `50`, 55 `55`, 60 `60`, 65 `65`, 70 `70`, 75 `75`, 80 `80`, 85 `85`, 90 `90`, 95 `95`, 100 `100`, 105 `105`, 110 `110`, 115 `115`, 120 `120`. |

#### libretro: MesenS

Wait does this actaully work for Game Boy *Color* games and not just ordinary Game Boy games?

Technically a SNES emulator, MesenS supports some Game Boy Color games via the Super Game Boy (or at least, an emulated version of it). Requires the appropriate BIOS files to function.

ROMs placed in the `roms/sgb` folder will appear in the SNES's game list, opening them from here will start the Game Boy Color game as if though you were playing it from the Super Game Boy. How neat!

## Controls
Here are the default Game Boy Color's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).