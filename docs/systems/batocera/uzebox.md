# Uzebox

**Source:** https://wiki.batocera.org/systems:uzebox  
**Last fetched:** 2025-12-06 16:19:55

---

# Uzebox
The [Uzebox](http://uzebox.org/index.php) is a simple yet extremely efficient and effective open source console developed by Atmel. It was released in 2008.

The physical console features a AVR ATmega644, a widely available general purpose microcontroller based on Atmel's AVR architecture. It has 4K of RAM(!), 64K of flash for both code, sound and graphics data, lots of I/O lines and many peripheral features. Read more about it [at its description page](http://uzebox.org/howitsmade.htm).

Batocera features libretro's Uzem, the *official* emulator.

Most software available to it has been listed on their [official wiki](http://uzebox.org/wiki/Games_and_Demos).

This system scrapes metadata for the "uzebox" group and loads the `uzebox` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: Uzem](#libretro:_uzem)
- **Folder:** `/userdata/roms/uzebox`
- **Accepted ROM formats:** `.uze`

## BIOS
No Uzebox emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Uzebox ROMs in `/userdata/roms/uzebox`.

Most software available to it has been listed on their [official wiki](http://uzebox.org/wiki/Games_and_Demos).

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `uzebox.videomode`, `uzebox.ratio`, `uzebox.smooth`, `uzebox.shaders`, `uzebox.pixel_perfect`, `uzebox.decoration`, `uzebox.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `uzebox.gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `uzebox.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `uzebox.video_threaded`** | Improves performance at the cost of latency and more video stuttering.\\ => On `true`, Off `false`. |

#### libretro: Uzem
[Uzem](https://github.com/libretro/libretro-uzem) is the official emulator for the Uzebox.

##### libretro: Uzem configuration
## Controls

Same as NES, just without Select.

Here are the default Uzebox's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).