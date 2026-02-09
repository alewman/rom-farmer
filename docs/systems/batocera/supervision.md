# Watara Supervision

**Source:** https://wiki.batocera.org/systems:supervision  
**Last fetched:** 2025-12-06 16:19:51

---

This article needs some TLC. Read at your own risk.

# Watara Supervision
The Watara Supervision, also known as the QuickShot Supervision in the UK, is a monochrome handheld game console, originating from Asia, and introduced in 1992 as a cut-price competitor for Nintendo's Game Boy. It came packaged with a game called Crystball, which is similar to Breakout. One unique feature of the Supervision was that it could be linked up to a television via a link cable. Games played in this way would display in four colors, much like Nintendo's Super Game Boy add-on for the SNES. A full color TV link was also in the works, but because of the Supervision's failure to make a major impression among gamers it was cancelled, along with the games which were in development for it.

The system was renamed from `watara` to `supervision` prior to Batocera v31.

This system scrapes metadata for the "supervision" group(s) and loads the `supervision` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro/potator](#libretro_potator)
- **Folder:** `/userdata/roms/supervision`
- **Accepted ROM formats:** `.sv`, `.zip`, `.7z`

## BIOS
No Watara Supervision emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Watara Supervision ROMs in `/userdata/roms/supervision`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro/(core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `supervision.videomode`, `supervision.ratio`, `supervision.smooth`, `supervision.shaders`, `supervision.pixel_perfect`, `supervision.decoration`, `supervision.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `supervision.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `supervision.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `supervision.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro/potator
A Watara Supervision Emulator based on Normmatt version. Batocera uses the latest [libretro core](https://github.com/libretro/potator).

##### libretro/potator configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **COLOR PALETTE `global.watara_palette`** | Choose which color palette is going to be used\\ => Green - GameKing `gameking`, GB - DMG `gb_dmg`, GB - Light `gb_light`, GB - Pocket `gb_pocket`, VB - Virtual Boy `virtual_boy`, Potator - Orangish - Amber `potator_amber`, Potator - Green `potator_green`, Potator - Blue `potator_blue`, Potator - Green - BGB `potator_bgb`, Potator - Green Wataroo `potator_wataroo`, Brownish - Travel Wood `travel_wood`, Blue - Bubbles Blue `bubbles_Blue`, Blue - Game Master `game_master`, Blue - Shiny Sky Blue `shiny_sky_blue`, Blue - Slime Blue `slime_blue`, Gold - Golden Wild `golden_wild`, Gold - Labo Fawn `labo_fawn`, Gold - Million Live Gold `million_live_gold`, Gold - Odyssey Gold `odyssey_Gold`, Grey - Greyscale `default`, Grey - Digivice `digivice`, Grey - Microvision `microvision`, Green - Buttercup Green `buttercup_green`, Green - Game.com `game_com`, Green - Greenscale `greenscale`, Green - Legendary Super Saiyan `legendary_super_saiyan`, Green - TI-83 `ti_83`, Orange - Hokage Orange `hokage_orange`, Pink - Blossom Pink `blossom_pink`. |
| **GHOSTING EFFECT `global.watara_ghosting`** | Simulation of LCD ghosting effects\\ => Off `0`, 1 Frame `1`, 2 Frames `2`, 3 Frames `3`, 4 Frames `4`, 5 Frames `5`, 6 Frames `6`, 7 Frames `7`, 8 Frames `8`. |

## Controls
Here are the default Watara Supervision's controls shown on a [Batocera Retropad](:configure_a_controller):

The default button mapping to the Watara Supervision is 1-to-1 with the [Nintendo Game Boy](systems:gb).

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).