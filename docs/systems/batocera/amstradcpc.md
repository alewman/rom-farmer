# Amstrad Color Personal Computer

**Source:** https://wiki.batocera.org/systems:amstradcpc  
**Last fetched:** 2025-12-06 16:18:35

---

# Amstrad Color Personal Computer
The Amstrad Color Personal Computer (CPC) is a line of computers developed by Amstrad. The first model, the CPC 464, was released in 1984.

Models released include:
- CPC 464
- CPC664
- CPC6128
- 464plus
- 6128plus

And of course, the ill-fated [GX4000 videogame console](systems:gx4000) based on the plus series of computers.

It was one of the first computers to be sold as the "complete package" to the home market, including the keyboard, drive storage and monitor all in one (most home-oriented computers relied on the user having a domestic TV set). It predated the Macintosh by almost a year.

Infamously, Amstrad founder Alan Sugar wanted the machine to resemble a "real computer," and not to look like "a pregnant calculator".

It enjoyed a health community, even having multiple dedicated magazine lines in parts of Europe and Australia. Following the CPC's end of production, Amstrad gave permission for the CPC ROMs to be distributed freely as long as the copyright message is not changed and that it is acknowledged that Amstrad still holds copyright, giving emulator authors the possibility to ship the CPC firmware with their programs. ((https:*web.archive.org/web/20080510131526/http:*web.ukonline.co.uk/cliff.lawson/cpchomec.htm))

This system scrapes metadata for the "amstradcpc" group and loads the `amstradcpc` set from the currently selected theme, if available.

### Quick reference
- **Emulators:** [RetroArch](#retroarch) or [CLK](#CLK) 
- **Core:** [libretro: cap32](#libretro:_cap32) or [CLK](#CLK)
- **Folder:** `/userdata/roms/amstradcpc`
- **Accepted ROM formats:** `.dsk`, `.sna`, `.tap`, `.cdt`, `.voc`, `.m3u`, `.zip`, `.7z`

## BIOS
CAP32 does not need a BIOS file to run.

Starting with Batocera 42, you can also use CLK as an Amstrad CPC emulator. CLK requires the following BIOS files:

| MD5 checksum | Share file path | Description |
| `25629dfe870d097469c217b95fdc1c95` | `bios/AmstradCPC/amsdos.rom` | Required - Amstrad Disk Operating System|
| `2cc1ba759f835c98a480a152d786b877` | `bios/AmstradCPC/basic6128.rom` | Required - Locomotive Basic CPC6128|
| `9ba1b052c77713024bf2eb224cad2062` | `bios/AmstradCPC/os6128.rom` | Required - ROM CPC6128|

## ROMs
Place your Amstrad CPC ROMs in `/userdata/roms/amstradcpc`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `amstradcpc.videomode`, `amstradcpc.ratio`, `amstradcpc.smooth`, `amstradcpc.shaders`, `amstradcpc.pixel_perfect`, `amstradcpc.decoration`, `amstradcpc.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `amstradcpc.gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `amstradcpc.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `amstradcpc.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: cap32
##### libretro: cap32 configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **CPC MODEL `global.cap32_model`** | Choose which Amstrad CPC model to emulate.\\ => 464 `464`, 6128 `6128`, 6128+ `6128+`. |
| **RAM SIZE `global.cap32_ram`** | CPC physical RAM size in kB.\\ => 64 `64`, 128 `128`, 192+ `192`, 512 `512`, 576+ `576`. |

## Controls
To enable gamepad support, go in RetroArch menu with `[HOTKEY]` + , then change **Input** -> **User 1 Device type: Retropad** to "Amstrad Joystick".

Here are the default Amstrad CPC's controls shown on a [Batocera Retropad](:configure_a_controller):

### CLK
[CLK aka Clock Signal](https://github.com/TomHarte/CLK) is a multi-system emulator that is focused on low-latency emulation, that can be used for Amstrad CPC. CLK has been added to Batocera 42.

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).