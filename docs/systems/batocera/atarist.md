# Atari ST

**Source:** https://wiki.batocera.org/systems:atarist  
**Last fetched:** 2025-12-06 16:18:42

---

# Atari ST
The Atari ST is a series of computers developed by Atari. The first model had a limited release in April 1985, with wider availability later in July. The monochrome display retailed for $799.99 USD ($2,063.94 in 2021), with the color display retailing for $999.99. Later models would be capable of outputting to standard TV sets. The last model was discontinued in 1993. Notable titles include Dungeon Master, Oids, Sundog and MIDI Maze.

Although this price might seem high by today's standards, it was actually one of the more affordable computers for the time. This, plus offering an all-around superior monochrome display in general, made it quite successful in the business market.

The "ST" stands for Sixteen Thirty-two, in reference to the 16 and 32-bit components it utilizes. It's also been said to be the initials of Sam Tramiel, the son of Jack Tramiel, who was president of Atari at the time.

Model list:
- Atari 520ST
- Atari 260ST
- Atari 520STM
- Atari STf
- Atari 520STE
- Atari 1040STE
- Atari MEGA ST
- Atari MEGA STE
- Atari TT030
- Atari Falcon

Interesting tidbit about the unreleased Falcon 040, [one of its prototype case designs would go on to inspire the case design](https://youtu.be/cBTXGgb__y4?t=1717) for the [Sony PlayStation 2](systems:ps2):

This system scrapes metadata for the "atarist" group and loads the `atarist` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.st`, `.msa`, `.stx`, `.dim`, `.ipf`, `.m3u`, `.zip`, `.7z`
- **Folder:** `/userdata/roms/atarist`

| Emulators | Notes |
| [libretro: Hatari](#libretro:_hatari) | |
| [Hatari](#hatari) | |
| [CLK](#clk) | starting with Batocera 42 |

## BIOS
Only `tos.img` is truly required, however many games will not function on this BIOS alone and other BIOS files need to be tried.

| MD5 checksum | Share file path | Description |
| `c1c57ce48e8ee4135885cee9e63a68a2` | `bios/tos.img` | |
| `25789a649faff0a1176dc7d9b98105c0` | `bios/tos100fr.img` | |
| `c87a52c277f7952b41c639fc7bf0a43b` | `bios/tos100uk.img` | |
| `d0f682ee6237497004339fb02172638b` | `bios/tos100us.img` | |
| `a622cc35d8d78703905592dfaa4d2ccb` | `bios/tos102de.img` | |
| `d6521785627d20c51edc566808a6bf28` | `bios/tos102fr.img` | |
| `b2a8570de2e850c5acf81cb80512d9f6` | `bios/tos102uk.img` | |
| `41b7dae4e24735f330b63ad923a0bfbc` | `bios/tos104de.img` | |
| `143343f7b8e0b1162af206fe8f46b002` | `bios/tos104es.img` | |
| `0087e2707c57efa2106a0aa7576655c0` | `bios/tos104fr.img` | |
| `036c5ae4f885cbf62c9bed651c6c58a8` | `bios/tos104uk.img` | |
| `736adb2dc835df4d323191fdc8926cc9` | `bios/tos104us.img` | |
| `992bac38e01633a529121a2a65f0779e` | `bios/tos106de.img` | |
| `30f69d70fe7c210300ed83f991b12de9` | `bios/tos106es.img` | |
| `bc7b224d0dc3f0cc14c8897db89c5787` | `bios/tos106fr.img` | |
| `6033f2b9364edfed321c6931a8181fd2` | `bios/tos106uk.img` | |
| `a0982e760f9807d82667ff5a69e78f6b` | `bios/tos106us.img` | |
| `94a75c1c65408d9f974b0463e15a3b11` | `bios/tos162de.img` | |
| `ed5fbaabe0219092df74c6c14cea3f8e` | `bios/tos162fr.img` | |
| `1cbc4f55295e469fc8cd72b7efdea1da` | `bios/tos162uk.img` | |
| `febb00ba8784798293a7ae709a1dafcb` | `bios/tos162us.img` | |
| `7aeabdc25f8134590e25643a405210ca` | `bios/tos205de.img` | |
| `7449b131681f1dfe62ebed1392847057` | `bios/tos205es.img` | |
| `61b620ad951815a25cb37895c81a947c` | `bios/tos205fr.img` | |
| `7e87d8fe7e24e0b4c55ad1b7955beae3` | `bios/tos205it.img` | |
| `7cdd45b6aac66a21bfb357d9334e46db` | `bios/tos205us.img` | |
| `0604dbb85928f0598d04144a8b554bbe` | `bios/tos206de.img` | |
| `b2873004a408b8db36321f98daafa251` | `bios/tos206fr.img` | |
| `4a0d4f282c3f2a0196681adf88862dd4` | `bios/tos206.img` | |
| `e690bec90d902024beed549d22150755` | `bios/tos206uk.img` | |
| `c9093f27159e7d13ac0d1501a95e53d4` | `bios/tos206us.img` | |
| `066f39a7ea5789d5afd59dd7b3104fa6` | `bios/tos306de.img` | |
| `dd1010ec566efbd71047d6c4919feba5` | `bios/tos306uk.img` | |
| `ed2647936ce4bd283c4d7dfd7ae09d1c` | `bios/tos400.img` | |
| `9e880168d0a004f7f5e852be758f39e4` | `bios/tos402.img` | |
| `e5ea0f216fb446f1c4a4f476bc5f03d4` | `bios/tos404.img` | |

For CLK, only the following BIOS file is required:

| MD5 checksum | Share file path | Description |
| `c87a52c277f7952b41c639fc7bf0a43b` | `bios/AtariST/tos100.img` | This is the UK version of TOS, same file as `bios/tos100uk.img` above |

## ROMs
Place your Atari ST ROMs in `/userdata/roms/atarist`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `atarist.videomode`, `atarist.ratio`, `atarist.smooth`, `atarist.shaders`, `atarist.decoration`, `atarist.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `atarist.gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `atarist.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `atarist.video_threaded`** | Improves performance at the cost of latency and more video stuttering.\\ => On `true`, Off `false`. |

#### libretro: Hatari
This is the [libretro port](https://github.com/libretro/hatari) of the [Hatari](#hatari) emulator.

##### libretro: Hatari configuration
Open the Hatari GUI in-game with . This is typically required to configure games properly before they'll begin launching.

### Hatari
[Hatari](http://hatari.tuxfamily.org/) is an Atari ST/STE/TT/Falcon emulator.

#### Hatari configuration
Standardized features available to all cores of this emulator: `atarist.videomode`, `atarist.padtokeyboard`, `atarist.decoration`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **MODEL `atarist.model`** | \\ => 520 ST / AUTO `520st_auto`, 520 ST / TOS 1.00 `520st_100`, 520 ST / TOS 1.02 `520st_102`, 520 ST / TOS 1.04 `520st_104`, 1040 STE / AUTO `1040ste_auto`, 1040 STE / 1.06 `1040ste_106`, 1040 STE / 1.62 `1040ste_162`, Mega STE / AUTO `megaste_auto`, Mega STE / 2.05 `megaste_205`, Mega STE / 2.06 `megaste_206`. |
| **LANGUAGE `atarist.language`** | TOS languages.\\ => DE `de`, ES `es`, FR `fr`, IT `it`, NL `nl`, RU `ru`, SE `se`, UK `uk`, US `us`. |
| **EMULATED RAM SIZE `atarist.ram`** | \\ => 520K `0`, 1M `1`, 2M `2`, 4M `4`. |

### CLK
[CLK aka Clock Signal](https://github.com/TomHarte/CLK) is a multi-system emulator that is focused on low-latency emulation, that can be used for Atari ST. CLK has been added to Batocera 42.

## Controls
Here are the default Atari ST's controls shown on a [Batocera RetroPad](:configure_a_controller):

| Batocera RetroPad | Libretro Hatari |
|  | Fire |
|  | Open Hatari GUI |
| D-pad | Directions |
| `[L1]` | Joystick number |
| `[R1]` | Cursor speed |
| `[L2]` | Toggle m/k status |
| `[START]` | On-screen keyboard |
| `[START]` | Mouse mode toggle |

## Troubleshooting
### Game X does not work
Atari ST is one of the harder emulators to get set up and working properly. Libretro has a [quick guide on their documentation site](https://docs.libretro.com/library/hatari/#getting-started-with-hatari). For more in-depth issues, read on.

To quote [Hatari's FAQ page](http://hatari.tuxfamily.org/docs.html):

>  * Many ST games often need a certain TOS version to run right. Old games often only work with TOS 1.00 or TOS 1.02, so you should try these TOS versions first. If the game still does not work, you should also try TOS 1.04 and 2.06. Some games also either need a NTSC (US American) or a PAL (European) TOS, so it might be useful to test these different types, too.
>  * There are also some games which do not work in STE mode - but there are also some few games which only work in STE mode and not in ST mode. So changing the machine type might be worth a try, too.
>  * Some games also need certain RAM sizes, for example some games do not work with 4 MB memory size!
>  * And finally, try to enable the "Slower but more compatible CPU" and/or disable the "Patch Timer-D" in the system options dialog. This slightly increases compatibility with the real ST. In some few cases you also have to enable the "Slow floppy access" option in the floppy options dialog to mimic the speed of the original floppy disk drive.

The [full manual](http://hatari.tuxfamily.org/doc/manual.html) offers more insight.

Check the [compatibility list](http://hatari.tuxfamily.org/doc/compatibility.html) 

### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).