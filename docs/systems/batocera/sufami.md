# SuFami Turbo

**Source:** https://wiki.batocera.org/systems:sufami  
**Last fetched:** 2025-12-06 16:19:50

---

This article needs some TLC. Read at your own risk.

# SuFami Turbo
The SuFami Turbo is an accessory released by Bandai for Nintendo's Super Famicom system and was released in 1996, retailing for ¥3,980 JPY.

The unit would be inserted into the Super Famicom and offer its own two separate cartridge slots. The idea being that not having to rely on Nintendo to manufacture expensive cartridges for game distribution would cut down on the costs of game distribution. The product itself was officially endorsed by Nintendo, under the condition that Bandai would handle all aspects of hardware manufacturing itself.

The dual slot design would allow multiple games to communicate with each other, the idea for the game in slot 1 to be the one that's currently being played and the game in slot 2 being the one providing additional data for the game currently being played. Of the thirteen games released for the SuFami Turbo, nine of them can link up.

This system scrapes metadata for the "sufami" group and loads the `sufami` set from the currently selected theme, if available.

Grouped with the "snes" group of systems.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: snes9x](#libretro:_snes9x)
- **Folder:** `/userdata/roms/sufami`
- **Accepted ROM formats:** `.st`, `.fig`, `.bs`, `.smc`, `.sfc`, `.zip`, `.7z`

## BIOS
| MD5 checksum | Share file path | Description |
| `d3a44ba7d42a74d3ac58cb9c14c6a5ca` | `bios/STBIOS.bin` | |

## ROMs
Place your SuFami Turbo ROMs in `/userdata/roms/sufami`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `sufami.videomode`, `sufami.ratio`, `sufami.smooth`, `sufami.shaders`, `sufami.pixel_perfect`, `sufami.decoration`, `sufami.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `sufami.gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `sufami.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `sufami.video_threaded`** | Improves performance at the cost of latency and more video stuttering.\\ => On `true`, Off `false`. |

#### libretro: snes9x
##### libretro: snes9x configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **REDUCE SPRITE FLICKERING (UNSTABLE) `global.reduce_sprite_flicker`** | Enhancement. Remove the thirty-two sprites per line limit. Crashes certain games.\\ => Off `disabled`, On `enabled`. |
| **OVERCLOCK (UNSTABLE) `global.reduce_slowdown`** | Overclock the SNES CPU (Gradius 3, Super R-Type).\\ => Off `disabled`, Light (load times) `light`, Compatible `compatible`, Max (demanding games) `max`. |
| **SUPER FX OVERCLOCK `global.overclock_superfx`** | Enhancement. Reduces slowdown in mode 7 games.\\ => 50% `50%`, 60% `60%`, 70% `70%`, 80% `80%`, 90% `90%`, 100% `100%`, 150% `150%`, 200% `200%`, 250% `250%`, 300% `300%`, 350% `350%`, 400% `400%`, 450% `450%`, 500% `500%`. |
| **BLEND HIGH-RES MODE `global.hires_blend`** | Blur high-res mode, allowing for better transparency effects.\\ => Off `disabled`, Merge `merge`, Blur `blur`. |
| **CONTROLLER 1 TYPE `global.controller1_snes9x`** | \\ => SNES Gamepad `1`, SNES Mouse `2`. |
| **CONTROLLER 2 TYPE `global.controller2_snes9x`** | Lightguns can only be used in port 2.\\ => SNES Gamepad `1`, SNES Mouse `2`, SNES Multitap `257`, Super Scope `260`, Konami Justifier `516`, M.A.C.S. Rifle `1028`. |
| **CONTROLLER 3 TYPE `global.controller3_snes9x`** | Konami Justifier P2 is daisy chained from controller 2, appears as port 3 to system.\\ => SNES Gamepad `1`, Konami Justifier (P2) `772`. |

## Controls
Here are the default SuFami Turbo's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).