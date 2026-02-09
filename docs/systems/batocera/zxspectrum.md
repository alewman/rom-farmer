# ZXSpectrum

**Source:** https://wiki.batocera.org/systems:zxspectrum  
**Last fetched:** 2025-12-06 16:20:08

---

This article needs some TLC. Read at your own risk.

# ZXSpectrum
The ZXSpectrum is a range of models of 8-bit computers developed by Sinclair. It was first released in April 1982, and the last model was discontinued in 1992.

During development, the ZX Spectrum was referred to as the ZX81 Colour and the ZX82. The rename to Spectrum was done to highlight the machine's new color capabilities.

The Spectrum was released as eight different models with different capabilities for their budget, going from the entry-level model only having 16KB RAM to the high-end +3 with 128KB RAM and built-in floppy disk drive.

Model list:
- ZX Spectrum 16K
- ZX Spectrum 48K
- ZX Spectrum+
- ZX Spectrum 128
- ZX Spectrum+2
- ZX Spectrum+2A
- ZX Spectrum+3
- ZX Spectrum+2B
- ZX Spectrum+3B

The Spectrum was a cultural phenomena to British culture. The Spectrum's creator, Clive Sinclair, was knighted in 1983 for his services to the British industry. Spectrum game development continues to this very day.

This system scrapes metadata for the "zxspectrum" group and loads the `zxspectrum` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch), [CLK](#clk)
- **Core:** [libretro: fuse](#libretro:_fuse)
- **Folder:** `/userdata/roms/zxspectrum`
- **Accepted ROM formats:** `.tzx`, `.tap`, `.z80`, `.rzx`, `.scl`, `.trd`, `.zip`, `.7z`

## BIOS
Libretro-based emulators for ZXSpectrum in Batocera need no BIOS file to run.

CLK requires the following BIOS files:

| MD5 checksum | Share file path | Description |
| `05de80a055b5e7866f55769db0584d6e` | `bios/ZXSpectrum/plus3.rom` | the UK +2a/+3 ROM file, 64kb in size ||
| `238f77692156a5c49d20c0aa2862e8bb` | `bios/ZXSpectrum/plus2.rom` | the UK +2 ROM file, 32kb in size |
| `85fede415f4294cc777517d7eada482e` | `bios/ZXSpectrum/128.rom` | the UK 128kb ROM file, 32kb in size |
| `4c42a2f075212361c3117015b107ff68` | `bios/ZXSpectrum/48.rom` | the 16/48kb ROM file, 16kb in size |

## ROMs
Place your ZXSpectrum ROMs in `/userdata/roms/zxspectrum`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `zxspectrum.videomode`, `zxspectrum.ratio`, `zxspectrum.smooth`, `zxspectrum.shaders`, `zxspectrum.decoration`, `zxspectrum.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `zxspectrum.gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `zxspectrum.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `zxspectrum.video_threaded`** | Improves performance at the cost of latency and more video stuttering.\\ => On `true`, Off `false`. |

#### libretro: fuse
##### libretro: fuse configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **ZOOM (HIDE BORDERS) `global.fuse_hide_border`** | Hides borders on many games. Some games used the borders.\\ => Off `disabled`, On `enabled`. |

All other configuration must be done using RetroArch's **Quick Menu** (`[HOTKEY]` + ).

## Controls
There are seven types of joysticks emulated:

- Cursor
- Kempston
- Sinclair 1
- Sinclair 2
- Timex 1
- Timex 2
- Fuller Joystick

Users 1 and 2 can choose any of the joysticks as their device types, user 3 can only choose the Sinclair Keyboard.

| Batocera RetroPad | Joystick |
|  | Fire |
|  | Fire |
|  | Fire |
|  | Up arrow |
| `[L1]` | Return |
| `[R1]` | Space |
| `[SELECT]` | On-screen keyboard |

There are some conflicts in the way the input devices interact because of the use of the physical keyboard keys as joystick buttons. For a good gaming experience, set the user device types as follows:

- For joystick games: Set user 1 to a joystick type. Optionally, set user 2 to another joystick type (local cooperative games). Set user 3 to none.

- For keyboard games: Set users 1 and 2 to none, and user 3 to Sinclair Keyboard. You won't have any joystick and the embedded keyboard won't work, but the entire physical keyboard will be available for you to type in those text adventure commands.

What does the following part even mean?

If you set a joystick along with the keyboard, the joystick will work just fine except for the bindings to Return and Space keys, and the keyboard won't register the keys assigned to the Cursor joystick, or to the `[L1]` and `[R1]` buttons for all other joystick types.

Here are the default ZXSpectrum's controls shown on a [Batocera RetroPad](:configure_a_controller):

### CLK
[CLK aka Clock Signal](https://github.com/TomHarte/CLK) is a multi-system emulator that is focused on low-latency emulation, that can be used for ZXSpectrum. CLK has been added to Batocera 42.

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).