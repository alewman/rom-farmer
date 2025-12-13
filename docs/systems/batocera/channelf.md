# Channel F

**Source:** https://wiki.batocera.org/systems:channelf  
**Last fetched:** 2025-12-06 16:18:48

---

# Channel F
The Fairchild Channel F (a.k.a. Video Entertainment System) is a first-generation home videogame console developed by Fairchild. It was released in November 1976 and retailed for $169.95 USD ($819 in 2021). It is the first console to use a *micro*processor.

The "F" in Channel F stands for "Fun"! :-D

This system scrapes metadata for the "channelf" group and loads the `channelf` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: FreeChaF](#libretro:_freechaf)
- **Folder:** `/userdata/roms/channelf`
- **Accepted ROM formats:** `.zip`, `.rom`, `.bin`, `.chf`

## BIOS
These two BIOS files are required:

| MD5 checksum | Share file path | Description |
| `ac9804d4c0e9d07e33472e3726ed15c3` | `bios/sl31253.bin` | Channel F BIOS (PSU 1) |
| `da98f4bb3242ab80d76629021bb27585` | `bios/sl31254.bin` | Channel F BIOS (PSU 2) |

The Channel F II BIOS is optional; games are compatible with either BIOS. If included, the Channel F II BIOS will be used instead of the equivalent Channel F BIOS.

| MD5 checksum | Share file path | Description |
| `95d339631d867c8f1d15a5f2ec26069d` | `bios/sl90025.bin` | Channel F II BIOS (PSU 1) |

## ROMs
Place your Channel-F ROMs in `/userdata/roms/channelf`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `channelf.videomode`, `channelf.ratio`, `channelf.smooth`, `channelf.shaders`, `channelf.pixel_perfect`, `channelf.decoration`, `channelf.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `channelf.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `channelf.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `channelf.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: FreeChaF
[FreeChaF](https://github.com/libretro/FreeChaF) is a libretro core for the Fairchild Channel F.

##### libretro: FreeChaF configuration
## Controls
Access to the console buttons is provided via an overlay. Pressing 'start' on either controller will display the console buttons. You can select a button by moving left and right and press the button with any of the face buttons (A, B, X, Y). Pressing 'start' a second time will hide the overlay.

Here are the default Channel-F's controls shown on a [Batocera Retropad](:configure_a_controller):

| FreeChaF Function         | Retropad                     |
| Forward                   | D-Pad Up, Left-Analog Up     |
| Backward                  | D-Pad Down, Left-Analog Down |
| Rotate Left               | Y, L, Right-Analog Left      |
| Rotate Right              | A, R, Right-Analog Right     |
| Pull Up                   | X, Right-Analog Up           |
| Push Down                 | B, Right-Analog Down         |
| Show/Hide Console Overlay | Start                        |
| Controller Swap           | Select                       |

- **Console Overlay:** Allows the user to view and select console buttons.
- **Controller Swap:** Controller Swap swaps the player 1 and player 2 controllers.

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).