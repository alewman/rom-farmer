# Super Game Boy

**Source:** https://wiki.batocera.org/systems:sgb  
**Last fetched:** 2025-12-06 16:19:46

---

# Super Game Boy
The Super Game Boy is an accessory for the SNES that allows playing Game Boy games on the big screen! It was released in 1994.

There were two versions of the Super Game Boy; the first one had a hardware timing bug that played the games in fast motion (including pitching up the sounds). This was fixed in the Super Game Boy 2.

In Batocera, the Super Game Boy is in a bit of a weird spot. It's considered its own system despite requiring [another system](systems:snes) to function, that uses the ROMs of a [portable handheld system](systems:gb) which can also be run inside of [a different handheld system](systems:gbc). So, where should this system go?

The answer is no one can really agree. The default behavior is to group it with the SNES games, such that all Super Game Boy ROMs copied to their own directory will appear in a subfolder. Ungrouped, the SGB will appear as its own system.

This system scrapes metadata for the "sgb" group and loads the `sgb` set from the currently selected theme, if available.

Grouped with the "snes" group of systems.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Cores available:** [libretro: mgba](#libretro:_mgba), [libretro: mesen-s](#libretro:_mesen-s)
- **Folder:** `/userdata/roms/sgb`
- **Accepted ROM formats:** `.gb`, `.gbc`, `.zip`, `.7z`

## BIOS
| MD5 checksum | Share file path | Description |
| `d574d4f9c12f305074798f54c091a8b4` | `bios/sgb_boot.bin` | |
| `e0430bca9925fb9882148fd2dc2418c1` | `bios/sgb2_boot.bin` | |
| `b15ddb15721c657d82c5bab6db982ee9` | `bios/SGB1.sfc` | |
| `8ecd73eb4edf7ed7e81aef1be80031d5` | `bios/SGB2.sfc` | |

## ROMs
Place your Super Game Boy ROMs in `/userdata/roms/sgb`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `sgb.videomode`, `sgb.ratio`, `sgb.smooth`, `sgb.shaders`, `sgb.pixel_perfect`, `sgb.decoration`, `sgb.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `sgb.gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `sgb.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `sgb.video_threaded`** | Improves performance at the cost of latency and more video stuttering.\\ => On `true`, Off `false`. |

#### libretro: mgba
A GBA emulator that also supports the SGB palettes of Game Boy games. It does not support the borders nor their animations.

##### libretro: mgba configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **SHOW BIOS BOOTLOGO `global.skip_bios_mgba`** | Requires BIOS file to be present.\\ => Show `False`, Skip `True`. |
| Settings specific to gb ||
| **SUPER GB BORDERS `gb.sgb_borders`** | Only for Super Game Boy enhanced games.\\ => Off `False`, On `True`. |
| **COLOR CORRECTION `gb.color_correction`** | Simulate LCD color inaccuracy.\\ => Off `False`, On `GBA`. |
| Settings specific to gbc ||
| **SUPER GB BORDERS `gbc.sgb_borders`** | Only for Super Game Boy enhanced games.\\ => Off `False`, On `True`. |
| **COLOR CORRECTION `gbc.color_correction`** | Simulate LCD color inaccuracy.\\ => Off `False`, On `GBC`. |
| Settings specific to gba ||
| **SOLAR SENSOR LEVEL `gba.solar_sensor_level`** | Value to use for the emulated solar sensor (Boktai).\\ => 0 `0`, 1 `1`, 2 `2`, 3 `3`, 4 `4`, 5 `5`, 6 `6`, 7 `7`, 8 `8`, 9 `9`, 10 `10`. |
| **FRAMESKIP `gba.frameskip_mgba`** | Skip frames to improve performance, at the cost of choppy motion.\\ => 0 `0`, 1 `1`, 2 `2`, 3 `3`, 4 `4`, 5 `5`, 6 `6`, 7 `7`, 8 `8`, 9 `9`, 10 `10`. |

#### libretro: mesen-s
A SNES emulator that fully supports the SGB features of Game Boy games. This includes the neat borders and animations of SGB:

##### libretro: mesen-s configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **BLARGG NTSC FILTER `global.mesen-s_ntsc_filter`** | Core-powered video filter.\\ => Disabled `disabled`, Composite (Blargg) `Composite (Blargg)`, S-Video (Blargg) `S-Video (Blargg)`, RGB (Blargg) `RGB (Blargg)`, Monochrome (Blargg) `Monochrome (Blargg)`. |
| **HIGH-RES BLENDING `global.mesen-s_blend_high_res`** | Blur high-res mode, allowing for better transparency effects.\\ => On `enabled`, Off `disabled`. |
| **CUBIC AUDIO INTERPOLATION `global.mesen-s_cubic_interpolation`** | Enhancement. Swap from SNES' guassian interpolation to cubic. Improves sound quality.\\ => On `enabled`, Off `disabled`. |
| **GAME BOY MODE `global.mesen-s_gbmodel`** | Change behaviour when emulating GB games. Auto uses SGB for GB and GBC for GBC.\\ => Game Boy `Game Boy`, Game Boy Color `Game Boy Color`, Super Game Boy `Super Game Boy`. |
| **SUPER GAME BOY 2 `global.mesen-s_sgb2`** | Emulate the Super Game Boy 2 for SGB. Runs games at the correct speed.\\ => On `enabled`, Off `disabled`. |
| **OVERCLOCK (UNSTABLE) `global.mesen-s_overclock`** | Enhancement. Reduces system slowdown. Causes issues in some games.\\ => None `None`, Low `Low`, Medium `Medium`, High `High`, Very High `Very High`. |
| **OVERCLOCK TYPE `global.mesen-s_overclock_type`** | Prefer "Before NMI", change to After NMI only if needed by the game.\\ => Before NMI `Before NMI`, After NMI `After NMI`. |
| **SUPER FX OVERCLOCK `global.mesen-s_superfx_overclock`** | Enhancement. Reduces slowdown in mode 7 games.\\ => 100% `100%`, 200% `200%`, 300% `300%`, 400% `400%`, 500% `500%`, 1000% `1000%`. |

## Controls
Here are the default Super Game Boy's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).