# Atari 800

**Source:** https://wiki.batocera.org/systems:atari800  
**Last fetched:** 2025-12-06 16:18:41

---

This article needs some TLC. Read at your own risk.

# Atari 800
The Atari 800 is a line of computers developed by Atari. The first computers in the line, 400 and 800, were released in 1979.

The first two models, the 400 and 800, had the 16KB and 48KB of user-expandable RAM installed, while the later XL and XE models would have 64KB and 128KB installed, populating all the available slots.

The current emulation of the Atari 800 based family of computers is not complete or fail safe. This wiki article only gives basic instructions so you can run some popular games. The full technical background on these issues can be found in this article: [Atari 8-Bit Guide (Raph Koster)](https://www.raphkoster.com/about-raph/hobbies/emulation/atari-8-bit-guide-for-lr-atari800-and-retropie/). The script mentioned in these pages is **not** integrated into Batocera yet, so you are stuck with the manual fixes until then.

This system scrapes metadata for the "atari800" group and loads the `atari800` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: atari800](#libretro:_atari800)
- **Folder:** `/userdata/roms/atari800`
- **Accepted ROM formats:** `.rom`, `.xfd`, `.atr`, `.atx`, `.cdm`, `.cas`, `.car`, `.bin`, `.a52`, `.xex`, `.zip`, `.7z`

## BIOS
| MD5 checksum | Share file path | Description |
| `eb1f32f5d9f382db1bbfb8d7f9cb343a` | `bios/ATARIOSA.ROM` | First PAL version of the OS. |
| `a3e8d617c95d08031fe1b20d541434b2` | `bios/ATARIOSB.ROM` | PC Xformer patched NTSC OS B ROM (Batocera v38 and earlier). |
| `4177f386a3bac989a981d3fe3388cb6c` | `bios/ATARIOSB.ROM` | Second NTSC revision of the OS (Batocera v39 and later). |
| `06daac977823773a3eea3422fd26a703` | `bios/ATARIXL.ROM` | Atari XL/XE extended ROM. |
| `0bac0c6a50104045d902df4503a4c30b` | `bios/ATARIBAS.ROM` | Atari BASIC interpreter, a programming engine required by some games (but usually not). |

There are subtle differences in machine type between the different Atari Computers, including different version of the OS (BIOS). Some games will crash unless you manually select a different BIOS.

## ROMs
Place your Atari 800 ROMs in `/userdata/roms/atari800`.

Multi-Disk games can only be used with an internal menu of the emulator. Playlists and RetroArch features for these games are not supported.

## Emulators
### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: atari800
A [libretro port](https:*github.com/libretro/libretro-atari800) of [Atari800](https:*atari800.github.io/). Originally written by David Firth in 1995 and released under the GPL.

##### libretro: atari800 configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings specific to atari800 ||
| **ATARI SYSTEM `atari800.atari800_system`** | Choose what Atari System to emulate.\\ => 400/600XL/800 (48K) (OS B) `400/800 (OS B)`, 800XL/1200XL/XEGS (64K) `800XL (64K)`, 130XE (128K) `130XE (128K)`, Modern XL/XE (320K CS) `Modern XL/XE(320K CS)`, Modern XL/XE (576K) `Modern XL/XE(576K)`, Modern XL/XE (1088K) `Modern XL/XE(1088K)`. |
| **VIDEO FORMAT STANDARD `atari800.atari800_ntscpal`** | Switch frequency and resolution by region.\\ => NTSC 240x480px 60Hz `NTSC`, PAL 288x576px 50Hz `PAL`. |
| **SIO ACCELERATION `atari800.atari800_sioaccel`** | Speeds up the virtual file loading. Some games won't load with this enabled.\\ => Off `disabled`, On `enabled`. |
| **HI-RES ARTIFACTING `atari800.atari800_artifacting`** | Emulate NTSC quirks to show more colors in hi-res mode. Most NTSC games took advantage of this quirk to show more than just two colors on the screen at once. Only very few PAL games were designed to only use two colors.\\ => Off `disabled`, On `enabled`. |
| **INTERNAL RESOLUTION `atari800.atari800_resolution`** | Use an alternate resolution. Some games need this.\\ => 336x240 `336x240`, 320x240 `320x240`, 384x240 `384x240`, 384x272 `384x272`, 384x288 `384x288`, 400x300 `400x300`. |
| Settings specific to atari5200 ||
| **JOYSTICK HACK (FOR ROBOTRON 2084) `atari5200.atari800_opt2`** | Treats the right analog stick as the second joystick.\\ => Off `disabled`, On `enabled`. |

## Controls
Analogue joysticks are supported only via hard-coded mouse inputs (bypassing RetroPad and default controls). The analog sticks of gamepads are NOT supported. This makes some games unplayable unless you connect a mouse.

Sure that it's not possible to [remap](:remapping_controls_per_emulator) them?

Here are the default Atari 800's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### My game is black and white!
Many (US) games look wrong because they use specific video artifacts to generate colors on NTSC TVs but look black and white in emulation, unless you set specific parameters.

What parameters?

### Game is not booting
Most ROM sets are in a format that requires one additional input at the start of a ROM. Sometimes the selection screen is not visible making it look like the emulator crashed.

So what buttons are common to try to get out of this?

### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).