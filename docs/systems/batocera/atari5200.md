# Atari 5200

**Source:** https://wiki.batocera.org/systems:atari5200  
**Last fetched:** 2025-12-06 16:18:40

---

# Atari 5200
The [Atari 5200](wp>Atari_5200) is the video game console version of the [Atari 400 computer](systems:atari800) developed by Atari. It was released in 1982.

Initially conceived to compete against the [Intellivision](systems:intellivision), it ended up primarily competing against the [ColecoVision](systems:colecovision). Despite beating both systems in performance and value per dollar, the 5200 was considered a commercial failure, only reaching 1 million units sold compared to the [2600](systems:atari2600)'s 30 million units.

Its unique joystick allowed for 360 degrees of input values and a keypad, along with featuring more utility buttons such as Start, Pause and Reset. 

Although software is not directly compatible between the Atari 5200 and the [8-bit Atari computers](wp>Atari_8-bit_family) it was based on, most Atari 5200 emulators are compatible with software designed for either system. Because of this, Batocera refers to the Atari 5200 the same as the Atari 800 internally sometimes.

This system scrapes metadata for the "atari5200" group(s) and loads the `atari5200` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: atari800](#libretro:_atari800)
- **Folder:** `/userdata/roms/atari5200`
- **Accepted ROM formats:** `.rom`, `.xfd`, `.atr`, `.atx`, `.cdm`, `.cas`, `.car`, `.bin`, `.a52`, `.xex`, `.zip`, `.7z`

## BIOS
| MD5 checksum | Share file path | Description |
| `281f20ea4320404ec820fb7ec0693b38` | `bios/5200.rom` | Atari 5200 BIOS |

## ROMs
Place your Atari 5200 ROMs in `/userdata/roms/atari5200`.

ROMs in the `.a52` format require an additional selection of the ROM type at the start of the emulator and sometimes that selection screen is not visible and requires a blind button press. You can convert the `.a52` files into a different format, `.car`, which contains additional information so that the selection screen is bypassed. The method of doing that inside the emulator together with a list of this information for all known Atari 5200 ROMs can be found here: [Cartridge Type Code List](https://retropie.org.uk/forum/topic/16556/cartridge-type-code-list-for-atari-5200-games)

## Emulators
### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: atari800
[Atari800](https://github.com/libretro/docs/blob/master/docs/library/atari800.md) is an Atari 400, 800, 600 XL, 800XL and 130XE computer and Atari 5200 console emulator libretro core by Petr Stehlik.

This is a bit more complicated than I thought. Needs confirmination about which settings actually apply to only 5200.

##### libretro: atari800 configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings specific to atari800 ||
| **ATARI SYSTEM `atari800.atari800_system`** | Choose what Atari System to emulate\\ => 400/600XL/800 (48K) (OS B) `400/800 (OS B)`, 800XL/1200XL/XEGS (64K) `800XL (64K)`, 130XE (128K) `130XE (128K)`, Modern XL/XE (320K CS) `Modern XL/XE(320K CS)`, Modern XL/XE (576K) `Modern XL/XE(576K)`, Modern XL/XE (1088K) `Modern XL/XE(1088K)`. |
| **VIDEO STANDARD `atari800.atari800_ntscpal`** | Switch frequency and resolution by region\\ => NTSC `NTSC`, PAL `PAL`. |
| **SIO ACCELERATION `atari800.atari800_sioaccel`** | Speeds up file loading (a few games will not load)\\ => Off `disabled`, On `enabled`. |
| **HI-RES ARTIFACTING `atari800.atari800_artifacting`** | Artificial color filters to mimic actual hardware\\ => Off `disabled`, On `enabled`. |
| **INTERNAL RESOLUTION `atari800.atari800_resolution`** | Enables alternate resolutions for some games\\ => 336x240 `336x240`, 320x240 `320x240`, 384x240 `384x240`, 384x272 `384x272`, 384x288 `384x288`, 400x300 `400x300`. |
| Settings specific to atari5200 ||
| **JOYSTICK HACK (FOR ROBOTRON) `atari5200.atari800_opt2`** | Treats the second analog stick as joystick 2\\ => Off `disabled`, On `enabled`. |

Many required settings for the emulator are not exposed to RetroArch or EmulationStation but need to be set inside the emulator itself. You can access this menu by pushing in `[L3]` or the `[F1]` key.

## Controls
Analogue joysticks are supported only via hard-coded mouse inputs (bypassing RetroPad and default controls). The analog sticks of gamepads are **not** supported. This makes some games unplayable unless you connect a mouse.

Sure that it's not possible to [remap](:remapping_controls_per_emulator) them?

Here are the default Atari 5200's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).