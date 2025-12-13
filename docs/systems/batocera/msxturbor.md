# MSX Turbo-R

**Source:** https://wiki.batocera.org/systems:msxturbor  
**Last fetched:** 2025-12-06 16:19:19

---

This article needs some TLC. Read at your own risk.

# MSX Turbo-R
The MSX Turbo-R is a computer developed by Microsoft. It was released in 1990.

This system scrapes metadata for the "msx" group(s) and loads the `msxturbor` set from the currently selected theme, if available.

Grouped with the "msx" group of systems.

### Quick reference
- **Accepted ROM formats:** `.dsk`, `.mx2`, `.rom`, `.zip`, `.7z`
- **Folder:** `/userdata/roms/msxturbor`

| Emulators |
| [libretro: bluemsx](#libretro:_bluemsx) |
| [openmsx](#openmsx) |

## BIOS
No MSX Turbo-R emulator in Batocera needs a BIOS file to run.

## ROMs
Place your MSX Turbo-R ROMs in `/userdata/roms/msxturbor`.

## Emulators
### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: bluemsx
##### libretro: bluemsx configuration
Standardized features for this core: `msxturbor.rewind`, `msxturbor.autosave`, `msxturbor.padtokeyboard`, `msxturbor.cheevos`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **REDUCE SPRITE FLICKERING `global.bluemsx_nospritelimits`** | Enhancement. Remove the four sprites per line limit.\\ => Off `False`, On `True`. |

### openmsx
#### openmsx configuration
Standardized features available to all cores of this emulator: `msxturbor.videomode`, `msxturbor.padtokeyboard`, `msxturbor.videomode`, `msxturbor.bezel`, `msxturbor.bezel_stretch`, `msxturbor.hud`, `msxturbor.hud_corner`, `msxturbor.bezel.tattoo`, `msxturbor.bezel.tattoo_corner`, `msxturbor.bezel.tattoo_file`, `msxturbor.bezel.resize_tattoo`

## Controls
Here are the default MSX Turbo-R's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).