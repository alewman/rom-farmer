# Solarus

**Source:** https://wiki.batocera.org/systems:solarus  
**Last fetched:** 2025-12-06 16:19:49

---

This article needs some TLC. Read at your own risk.

# Solarus
[Solarus](https://solarus-games.org/en) is a lightweight, free and open source game engine designed with 16-bit era in mind. It was released in 2011.

This system scrapes metadata for the "solarus" group and loads the `solarus` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [solarus](#solarus)
- **Folder:** `/userdata/roms/solarus`
- **Accepted ROM formats:** `.zip`, `.solarus`

## BIOS
No Solarus emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Solarus ROMs in `/userdata/roms/solarus`.

Check out the list of games on [Solarus' website](https://solarus-games.org/en/games).

## Emulators
### Solarus
#### Solarus configuration
Standardized features available to all cores of this emulator: `solarus.videomode`, `solarus.decoration`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **CONTROL CHOICE `solarus.joystick`** | Choose which pad to control your hero.\\ => Joypad `normal`, Left stick `joystick1`, Right stick `joystick2`. |

## Controls
Here are the default Solarus's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).