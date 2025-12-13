# Nintendo DS

**Source:** https://wiki.batocera.org/systems:nds  
**Last fetched:** 2025-12-06 16:19:24

---

## Nintendo DS
The Nintendo DS is a very popular handheld game console produced by Nintendo, released in 2004 in Japan and North America and 2005 for the rest of the world. 

DS stands for "Dual Screen", with this distinctive new feature to handheld games: two LCD screens working in tandem (the bottom one being a touchscreen).

This system scrapes metadata for the "nds" group(s) and loads the `nds` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.nds`, `.bin`, `.zip`, `.7z`
- **Folder:** `/userdata/roms/nds`

| Emulators |
| [libretro: DeSmuME](#libretro:_desmume) |
| [libretro: melonDS](#libretro:_melonds) |
| [melonDS](#melonds) |
| [DraStic](#drastic) |

## BIOS
These BIOS files are required for any NDS emulation:

**v33** and below:
| MD5 checksum | Share file path | Description |
| `94bc5094607c5e6598d50472c52f27f2` | `bios/firmware.bin` | NDS firmware |
| `df692a80a5b1bc90728bc3dfc76cd948` | `bios/bios7.bin` | NDS ARM7 BIOS |
| `a392174eb3e572fed6447e956bde4b25` | `bios/bios9.bin` | NDS ARM9 BIOS |

**v34**:
| MD5 checksum | Share file path | Description |
| `94bc5094607c5e6598d50472c52f27f2` | `bios/dsfirmware.bin` | NDS firmware |
| `df692a80a5b1bc90728bc3dfc76cd948` | `bios/biosnds7.bin` | NDS ARM7 BIOS |
| `a392174eb3e572fed6447e956bde4b25` | `bios/biosnds9.bin` | NDS ARM9 BIOS |

**v35** and above:
| MD5 checksum | Share file path | Description |
| `94bc5094607c5e6598d50472c52f27f2` | `bios/firmware.bin` | NDS firmware |
| `df692a80a5b1bc90728bc3dfc76cd948` | `bios/bios7.bin` | NDS ARM7 BIOS |
| `a392174eb3e572fed6447e956bde4b25` | `bios/bios9.bin` | NDS ARM9 BIOS |

If you'd like to optionally emulate DSi specifically, you'll also need these:

**v34** and below:
| MD5 checksum | Share file path | Description |
| `559dae4ea78eb9d67702c56c1d791e81` | `bios/biosdsi7.bin` | DSi ARM7 BIOS |
| `87b665fce118f76251271c3732532777` | `bios/biosdsi9.bin` | DSi ARM9 BIOS |
| `74f23348012d7b3e1cc216c47192ffeb` | `bios/dsifirmware.bin` | DSi firmware |
| `d71edf897ddd06bf335feeb68edeb272` | `bios/dsinand.bin` | DSi NAND |
| FIXME | `bios/dsi_sd_card.bin` | DSi SD card (if wanting to emulate the SD card as well) |

**v35** and above:
| MD5 checksum | Share file path | Description |
| `559dae4ea78eb9d67702c56c1d791e81` | `bios/dsi_bios7.bin` | DSi ARM7 BIOS |
| `87b665fce118f76251271c3732532777` | `bios/dsi_bios9.bin` | DSi ARM9 BIOS |
| `74f23348012d7b3e1cc216c47192ffeb` | `bios/dsi_firmware.bin` | DSi firmware |
| `d71edf897ddd06bf335feeb68edeb272` | `bios/dsi_nand.bin` | DSi NAND |
| FIXME | `bios/dsi_sd_card.bin` | DSi SD card (if wanting to emulate the SD card as well) |

## ROMs
Place your Nintendo DS ROMs in `/userdata/roms/nds`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `nds.videomode`, `nds.ratio`, `nds.smooth`, `nds.shaders`, `nds.pixel_perfect`, `nds.decoration`, `nds.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `nds.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `nds.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `nds.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: DeSmuME
A libretro port of the prolific DeSmuME DS emulator.

##### libretro: DeSmuME configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **VIDEO RESOLUTION `global.internal_resolution_desmume`** | Improve the fidelity of 3D models (does not affect 2D sprites)\\ => 256x192 `256x192`, 512x384 `512x384`, 768x576 `768x576`, 1024x768 `1024x768`, 1280x960 `1280x960`, 1536x1152 `1536x1152`, 1792x1344 `1792x1344`, 2048x1536 `2048x1536`, 2304x1728 `2304x1728`, 2560x1920 `2560x1920`. |
| **TEXTURE UPSCALING (XBRZ) `global.texture_scaling`** | Upscales textures on 3D objects\\ => Off `1`, 2x `2`, 4x `4`. |
| **TEXTURE SMOOTHING `global.texture_smoothing`** | Smooths out textures on 3D objects\\ => Off `disabled`, On `enabled`. |
| **ANTI-ALIASING (MSAA) `global.multisampling`** | Smooth out jagged edges on 3D object polygons\\ => Off `disabled`, 2x `2`, 4x `4`, 8x `8`, 16x `16`, 32x `32`. |
| **SCREEN LAYOUT `global.screens_layout`** | Allows you to arrange the DS screens\\ => top/bottom `top/bottom`, bottom/top `bottom/top`, left/right `left/right`, right/left `right/left`, top only `top only`, bottom only `bottom only`, quick switch `quick switch`, hybrid/top `hybrid/top`, hybrid/bottom `hybrid/bottom`. |
| **FRAMESKIP `global.frameskip_desmume`** | Skip frames to improve performance (smoothness)\\ => Off `0`, 1 `1`, 2 `2`, 3 `3`, 4 `4`, 5 `5`, 6 `6`, 7 `7`, 8 `8`, 9 `9`. |

#### libretro: melonDS
An up-and-coming Nintendo DS emulator by StapleButter, ported to libretro. Still in its early phases but its game compatibility is already comparable to DeSmuME.

##### libretro: melonDS configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **SKIP DS SYSTEM MENU `global.melonds_boot_directly`** | Use it to configure options like time and language\\ => Off `disabled`, On `enabled`. |
| **SCREEN LAYOUT `global.melonds_screen_layout`** | Allows you to arrange the DS screens\\ => top/bottom `Top/Bottom`, bottom/top `Bottom/Top`, left/right `Left/Right`, right/left `Right/Left`, top only `Top Only`, bottom only `Bottom Only`, hybrid top ratio 2 `Hybrid Top-Ratio2`, hybrid top ratio 3 `Hybrid Top-Ratio3`, hybrid bottom ratio 2 `Hybrid Bottom-Ratio2`, hybrid bottom ratio 3 `Hybrid Bottom-Ratio3`. |

### melonDS
An up-and-coming Nintendo DS emulator by StapleButter. Still in its early phases but its game compatibility is already comparable to DeSmuME.

#### melonDS configuration
Standardized features available to this emulator: `nds.videomode`

### DraStic
A standalone closed-source NDS emulator that originally started out as a paid app on Android. A free version of this is used on Raspberry Pi builds.

--> If you're curious as to why, click here.#

To quote Exophase:
> It's on Raspberry Pi because I released the port for it, as a semi-closed beta. I asked people not to distribute it but since I did link to it publicly somewhere it was basically inevitable. It still would have been nice if maintainers of a major front end didn't decide to incorporate it prematurely. That said, I still plan to release an "official" first version although at this point the lines have been really blurred as to what that even means.
>
> As for why they get to use it for free, I guess I don't have much of an answer for that other than that it's simply up to my discretion and I don't think the RPi ecosystem or community is a good fit for paid apps. This isn't completely without precedent, I released the Pandora version of DraStic (which the RPi one is more similar to than the Android) without charging, and before the Android version.

Source: [Posted by Exophase on the drastic-ds.com forum at Wed Feb 01, 2017 2:47 am.](https://drastic-ds.com/viewtopic.php?t=4307)

<--

#### DraStic configuration
Standardized features available to this emulator: `nds.videomode`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to this emulator ||
| **HI-RES `nds.drastic_hires`** | Improve the fidelity of 3D models\\ => Off `0`, On `1`. |
| **THREADED 3D `nds.drastic_threaded`** | Improves performance in 3D games (can cause glitches)\\ => Off `0`, On `1`. |
| **FIX 2D SCREEN `nds.drastic_fix2d`** | Fix main 2D Screen to follow action\\ => Off `0`, On `1`. |

## Controls
Here are the default Nintendo DS's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Why are my DS games in a different language?
Sometimes you want to launch an NDS game, but the language doesn't match the one you set in Batocera (like by default, you have Spanish for many EU games). That's because the NDS emulator manages its own language.

To fix that, go to the **ADVANCED SYSTEM OPTIONS** for the NDS and set **SKIP DS SYSTEM MENU** to **OFF**. This will enable you to get into the Nintendo DS system menu and set the language you want to use for the games. Click on the tiny "DS" icon at the bottom center of the screen with either the stylus or via D-pad navigation.

Once this is done, you can set "Skip DS system menu" back to **AUTO**, the language you set will be used for all your games.

### Further troubleshooting
For DraStic specific issues, check [their FAQ](https://www.drastic-ds.com/viewtopic.php?f=4&t=2) first (although it is focused on the Android version, it can still be quite helpful).

For further troubleshooting, refer to the [generic support pages](:support).