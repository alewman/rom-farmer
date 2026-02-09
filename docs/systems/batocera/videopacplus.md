# Videopac+ G7400

**Source:** https://wiki.batocera.org/systems:videopacplus  
**Last fetched:** 2025-12-06 16:19:57

---

## Videopac+ G7400
The Videopac+ G7400 is a console developed by Philips. It was released in 1983.

Place your ROMs in `/userdata/roms/videopacplus`. Most games were also backwards compatible with the original Videopac/Magnavox Oddyssey2, to play games in this backward compatibility mode adjust the **ADVANCED SYSTEM SETTINGS** -> **MODEL** or simply place your ROMs in `/userdata/roms/o2em`.

This system scrapes metadata for the "videopacplus" group(s) and loads the `videopacplus` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: O2EM](#libretro:_o2em)
- **Folder:** `/userdata/roms/videopacplus`
- **Accepted ROM formats:** `.bin`, `.zip`, `.7z`

## BIOS
| MD5 checksum | Share file path | Description |
| `562d5ebf9e030a40d6fabfc2f33139fd` | `o2rom.bin` | Odyssey2 BIOS - G7000 model |
| `f1071cdb0b6b10dde94d3bc8a6146387` | `c52.bin` | Videopac+ French BIOS - G7000 model |
| `c500ff71236068e0dc0d0603d265ae76` | `g7400.bin` | Videopac+ European BIOS - G7400 model |
| `279008e4a0db2dc5f1c048853b033828` | `jopac.bin` | Videopac+ French BIOS - G7400 model |

## ROMs
Place your Videopac+ ROMs in `/userdata/roms/videopacplus`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `odyssey2.videomode`, `odyssey2.ratio`, `odyssey2.smooth`, `odyssey2.shaders`, `odyssey2.pixel_perfect`, `odyssey2.decoration`, `odyssey2.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `odyssey2.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `odyssey2.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `odyssey2.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: O2EM
[O2EM](http:*o2em.sourceforge.net/) is an open-source Magnavox Odyssey² emulator. This is the [libretro port](https:*github.com/libretro/libretro-o2em) of that.

##### libretro: O2EM configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **EMULATED HARDWARE `global.o2em_bios`** | Choose what Odyssey/Videopac system to emulate\\ => Odyssey 2 (NTSC) `o2rom.bin`, Videopac G7000 (European) `c52.bin`, Videopac+ G7400 (European) `g7400.bin`, Videopac+ G7400 (France) `jopac.bin`. |
| **CONSOLE REGION `global.o2em_region`** | To force 60hz or 50hz if the auto detection fail\\ => Autodetect `autodetect`, NTSC `NTSC`, PAL `PAL`. |
| **SWAP GAMEPADS `global.o2em_swap_gamepads`** | Some games accept player 1 input from controller 2\\ => Off `disabled`, On `enabled`. |
| **CROP OVERSCAN `global.o2em_crop_overscan`** | Remove the border around the edges of the screen\\ => Off `disabled`, On `enabled`. |
| **GHOSTING EFFECT `global.o2em_mix_frames`** | Simulate CRT phosphor ghosting effects\\ => Off `disabled`, Simple `mix`, Ghosting (65%) `ghost_65`, Ghosting (75%) `ghost_75`, Ghosting (85%) `ghost_85`, Ghosting (95%) `ghost_95`. |
| **AUDIO FILTER `global.o2em_low_pass_range`** | Soften the hash sound effect from some games\\ => Off `0`, 10% `10`, 20% `20`, 30% `30`, 40% `40`, 50% `50`, 60% `60`, 70% `70`, 80% `80`, 90% `90`. |

## Voice samples
New to Batocera **v32**, a recent update to [libretro: O2EM](#libretro:_o2em) added sample support for emulating the voice synthesis module. Download the samples from [O2EM's homepage](http://o2em.sourceforge.net/) (hover over "Misc" near the top of the page) and extract them into `/userdata/bios/voice`. Sid the Spellbinder requires its own pack, but if you're not intending on playing that game they're not required.

To confirm they are loaded correctly, K.C.'s Krazy Chase! plays a voice sample almost immediately after starting a game.

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).