# Family Computer Disk System

**Source:** https://wiki.batocera.org/systems:fds  
**Last fetched:** 2025-12-06 16:18:55

---

# Family Computer Disk System
The Family Computer Disk System is an attachment to the regular [Famicom](systems:nes). It was released in 1986 only in Japan.

The FDS enhanced the original Famicom's sound processing, in addition to extra data storage space. It also had a microphone (used by [Kaiketsu Yanchamaru](wp>The_Legend_of_Zelda_(video_game)) and [Light Mythology: Palutena's Mirror](wp>Kid_Icarus)). With the delay of the NES to the Western market, by the time it came out the mapper solution developed for cartridges made the disk system redundant (although NES cartridges never really had the ability to hold save data, which is a feature that would stay exclusive to the disk system).

This system scrapes metadata for the "fds" group and loads the `fds` set from the currently selected theme, if available.

Grouped with the "nes" group of systems.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Cores available:** [libretro: fceumm](#libretro:_fceumm), [libretro: Nestopia](#libretro:_nestopia)
- **Folder:** `/userdata/roms/fds`
- **Accepted ROM formats:** `.fds`, `.zip`, `.7z`

## BIOS
| MD5 checksum | Share file path | Description |
| `ca30b50f880eb660a320674ed365ef7a` | `bios/disksys.rom` | |

## ROMs
Place your Family Computer Disk System ROMs in `/userdata/roms/fds`.

## Emulators
Since the FDS is essentially just the Famicom, emulators are identical between the "systems".

### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `fds.videomode`, `fds.ratio`, `fds.smooth`, `fds.shaders`, `fds.pixel_perfect`, `fds.decoration`, `fds.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `fds.gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `fds.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `fds.video_threaded`** | Improves performance at the cost of latency and more video stuttering.\\ => On `true`, Off `false`. |

#### libretro: fceumm
##### libretro: fceumm configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **REDUCE SPRITE FLICKERING `global.fceumm_nospritelimit`** | Remove the eight sprites per line limit.\\ => Off `disabled`, On `enabled`. |
| **CROP OVERSCAN `global.fceumm_cropoverscan`** | Crops out video edge hidden under bezel of analog TV\\ => None `none`, Horizontal `h`, Vertical `v`, Both `both`. |
| **COLOR PALETTE `global.fceumm_palette`** | Choose which color palette is going to be used\\ => default `default`, asqrealc `asqrealc`, nintendo-vc `nintendo-vc`, rgb `rgb`, yuv-v3 `yuv-v3`, unsaturated-final `unsaturated-final`, sony-cxa2025as-us `sony-cxa2025as-us`, pal `pal`, bmf-final2 `bmf-final2`, bmf-final3 `bmf-final3`, smooth-fbx `smooth-fbx`, composite-direct-fbx `composite-direct-fbx`, pvm-style-d93-fbx `pvm-style-d93-fbx`, ntsc-hardware-fbx `ntsc-hardware-fbx`, nes-classic-fbx-fs `nes-classic-fbx-fs`, nescap `nescap`, wavebeam `wavebeam`, custom `custom`. |
| **NTSC FILTER `global.fceumm_ntsc_filter`** | Enable blargg NTSC video filters\\ => Off `disabled`, Composite (color bleeding + artifacts) `composite`, SVideo (color bleeding only) `svideo`, RGB (crisp image) `rgb`. |
| **SOUND QUALITY (HIGHER DEVICES) `global.fceumm_sndquality`** | Increase sound quality for games using expansion audio\\ => Low `Low`, High `High`, Very High `Very High`. |
| **PPU OVERCLOCKING `global.fceumm_overclocking`** | Minimize ingame slowdowns of some games (Contra Force)\\ => disabled `disabled`, 2x-Postrender `2x-Postrender`, 2x-VBlank `2x-VBlank`. |
| **CONTROLLER 1 TYPE `global.controller1_nes`** | Select NES Gamepad or Gun (must use a mouse)\\ => Autodetect `1`, NES Gamepad `513`, NES Zapper `258`. |
| **CONTROLLER 2 TYPE `global.controller2_nes`** | Select NES Gamepad, Paddle or Gun (must use a mouse)\\ => Autodetect `1`, NES Gamepad `513`, NES Zapper `258`, Arkanoid paddle `514`. |

#### libretro: Nestopia
##### libretro: Nestopia configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **REDUCE SPRITE FLICKERING `global.nestopia_nospritelimit`** | Remove the eight sprites per line limit.\\ => Off `disabled`, On `enabled`. |
| **CROP OVERSCAN `global.nestopia_cropoverscan`** | Crops out video edge hidden under bezel of analog TV\\ => None `none`, Horizontal `h`, Vertical `v`, Both `both`. |
| **COLOR PALETTE `global.nestopia_palette`** | Choose which color palette is going to be used\\ => consumer `consumer`, cxa2025as `cxa2025as`, canonical `canonical`, alternative `alternative`, rgb `rgb`, pal `pal`, composite-direct-fbx `composite-direct-fbx`, pvm-style-d93-fbx `pvm-style-d93-fbx`, ntsc-hardware-fbx `ntsc-hardware-fbx`, nes-classic-fbx-fs `nes-classic-fbx-fs`, custom `custom`. |
| **NTSC FILTER `global.nestopia_blargg_ntsc_filter`** | Enable blargg NTSC video filters\\ => Off `disabled`, Composite (color bleeding + artifacts) `composite`, SVideo (color bleeding only) `svideo`, RGB (crisp image) `rgb`. |
| **CPU OVERCLOCK `global.nestopia_overclock`** | Minimize ingame slowdowns of some games (Contra Force)\\ => Off `1x`, 2x `2x`. |
| **4 PLAYER ADAPTER `global.nestopia_select_adapter`** | Manually select a 4 Player Adapter for some games\\ => Autodetect `automatic`, NTSC (NES) `ntsc`, Famicom (FDS) `famicom`. |

## Controls
Here are the default Family Computer Disk System's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).