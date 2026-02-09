# Oric Atmos

**Source:** https://wiki.batocera.org/systems:oricatmos  
**Last fetched:** 2025-12-06 16:19:29

---

# Oric Atmos
Oric was a brand of home computers sold in the 1980s by Tangerine Computer Systems, a United Kingdom-based company, which was popular primarily in Europe.

In 1984 the Oric Atmos was launched and became their most successful computer, an 8-bit computer with a MOS 6502A CPU running at 1 MHz and 16kB of RAM. 

### Quick reference
- **Accepted ROM formats:** `.tap`, `.dsk`, `.zip`
- **Folder:** `/userdata/roms/oricatmos`

| Emulators |
| [CLK Clock Signal](#CLK) |

## BIOS
| MD5 checksum | Share file path | Description |
| `a330779c42ad7d0c4ac6ef9e92788ec6` | `bios/Oric/basic11.rom` | Required |
| `c888b36bf0fc222c3585c3fabe556d21` | `bios/Oric/colour.rom` | Required for several games |
## ROMs
Place your Oric tapes or disk ROMs in `/userdata/roms/oricatmos`.

The CLK emulator requires the Basic1.1 ROM listed above.

## Emulators
#### CLK
[CLK aka Clock Signal](https://github.com/TomHarte/CLK) is a multi-system emulator that is focused on low-latency emulation. It emulates both Oric Atmos and its predecessor Oric 1 (and a bunch of other old computers).

## Controls
Most Oric games are played with the keyboard. There is a minimal [pad2key](https://wiki.batocera.org/remapping_controls_per_emulator#pad2key) configuration provided, but if you use only a joystick, you will most probably have to remap the keyboard to play your game.

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).