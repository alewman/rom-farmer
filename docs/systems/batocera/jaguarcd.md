# Atari Jaguar CD

**Source:** https://wiki.batocera.org/systems:jaguarcd  
**Last fetched:** 2025-12-06 16:19:08

---

# Atari Jaguar CD
The Atari Jaguar CD is a CD-ROM peripheral for the Jaguar video game console. Only 13 games were released for the Jaguar CD during its lifetime. However, previously unfinished and homebrew games have since been released. 

This system scrapes metadata for the "jaguar" group and loads the `atarijaguarcd` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.cue`, `.cdi`, `.bigpimg` (BigPEmu only)
- **Folder:** `/userdata/roms/jaguarcd`

| Emulators |
| [libretro: virtualjaguar](#libretro:_virtualjaguar) |
| [BigPEmu](#bigpemu) |

## BIOS
No Atari Jaguar emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Atari Jaguar ROMs in `/userdata/roms/jaguarcd`.

## Saves
Saves can be found in `/userdata/saves/jaguarcd`.

## Emulators
### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: virtualjaguar
[Virtual Jaguar](https:*icculus.org/virtualjaguar/) is an Atari Jaguar emulator, its compatibility can be checked near the bottom of [their webpage](https:*icculus.org/virtualjaguar/) (most notably, it does not support Jaguar CD games in any capacity). This is the [libretro port](https://github.com/libretro/virtualjaguar-libretro) of it.

##### libretro: virtualjaguar configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **FAST BLITTER (LESS COMPATIBLE) `global.usefastblitter`** | For weak machines. Some games will not work with this.\\ => Off `disabled`, On `enabled`. |
| **SHOW BIOS BOOTLOGO `global.bios_vj`** | Off is safer, On for specific games.\\ => Show `enabled`, Skip `disabled`. |
| **DOOM RES HACK `global.doom_res_hack`** | Enable for Doom to run at its correct resolution.\\ => Off `disabled`, On `enabled`. |

### BigPEmu
Created by [Rich Whitehouse](https://www.richwhitehouse.com/jaguar/), BigPEmu is the first Atari Jaguar emulator to offer compatibility with the entire library of commercially sold cartridges. It's worth noting that it was originally a closed-source emulator that was integrated into the Atari50 compilation. It has support for Jaguar CD games.

This emulator is only available for x86_64.

#### Jaguar Game Drive
Some games are locked to be used on the Jaguar Game Drive (a hardware extension for the Jaguar console). BigPEmu has an option to emulate this hardware and allow these locked games to be played. This option can be enabled by pressing the `[Esc]` key, then going to **System** -> **Settings** -> **Force JGD Emulation**.

#### Per-Game Profiles
BigPEmu supports per-game profiles. This is accomplished by creating a BigPEmu configuration file of the same name as the software image you're loading, with a `.bigpcfg` extension. For example, if your software image file is named `Cybermorph.j64`, you would create a `Cybermorph.bigpcfg` file alongside it.

In order to create the per-game configuration file, it's recommended that you make a copy of your central BigPEmu configuration file. Under Windows (FIXME this isn't windows though, this is batocera), you can find this file at `/userdata/saves/bigpemu-bottle/drive_c/users/root/AppData/Roaming/BigPEmu/BigPEmuConfig.bigpcfg`. It's sufficient to simply copy this file and rename it.

Once you've created the game-specific configuration file, all configuration changes made through the menus while the game in question is loaded will apply and be saved only to this configuration file. If the software is unloaded, the central configuration will be used.

## Controls
Here are the default Atari Jaguar's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).