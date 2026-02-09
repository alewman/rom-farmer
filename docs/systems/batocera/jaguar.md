# Atari Jaguar

**Source:** https://wiki.batocera.org/systems:jaguar  
**Last fetched:** 2025-12-06 16:19:08

---

# Atari Jaguar
The Atari Jaguar is a console developed by Atari. It was released in 1993.

It featured 64-bit graphical accelerators, making it technically the only console of its competitors (the [Saturn](systems:saturn) and the [PlayStation](systems:psx)) as it was proudly advertised as. However, this was *just* the graphical accelerators, the GPU itself was 32-bit and the CPU was only 16-bit, leading to some [controversy](wp>Atari_Jaguar#Bit_count_controversy). The console itself was capable of 3D polygonal graphics, but the quality of the titles that utilized them were more comparable to the SNES's SuperFX chip than the Saturn's and PlayStation's graphical fidelity.

The Jaguar was a commercial failure, selling less 150,000 units than and having only 50 cartridge games in its library. This would mark Atari's last major home console release, relegating themselves to producing [plug and play TV games](systems:plugnplay).

On May 14, 1999, Hasbro Interactive announced that it had released all patents to the Jaguar, declaring it an open platform, opening it up for homebrew developers to make their own software for it.

Emulation for the Jaguar is not that mature yet, there will be many instances of incompatible games.

The Atari Jaguar also received a CD add-on later in its life, with a total of twelve official games released using it.

This system scrapes metadata for the "jaguar" group and loads the `atarijaguar` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.cue`, `.j64`, `.jag`, `.cof`, `.abs`, `.cdi`, `.rom`, `.zip`, `.7z`
- **Folder:** `/userdata/roms/jaguar`

| Emulators |
| [libretro: virtualjaguar](#libretro:_virtualjaguar) |
| [BigPEmu](#bigpemu) |

## BIOS
No Atari Jaguar emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Atari Jaguar ROMs in `/userdata/roms/jaguar`.

## Saves
Saves can be found in `/userdata/saves/jaguar`.

When performing an in-game save, the Virtual Jaguar core creates both a Cartridge EEPROM save file and a CD-ROM EEPROM save file, regardless of the game type.

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