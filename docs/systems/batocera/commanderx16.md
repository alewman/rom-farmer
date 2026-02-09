# Commander X16

**Source:** https://wiki.batocera.org/systems:commanderx16  
**Last fetched:** 2025-12-06 16:18:49

---

# Commander X16
Extract your Commander X16 games in their own directory.

The games with .IMG .PRG extensions will show in EmulationStation to run accordingly.

If you have a game without an appropriate extension you can create a .BAS file with DOS commands.

i.e. in the game folder create a PLANETX16.BAS file.

Then add into the file the DOS commands to load the game, like so...

LOAD "PLANETX16"
RUN

If you have an .IMG file which doesn't load then create an autorun.cmd file with the DOS commands also.

i.e. X16 Wars would contain the following...

LOAD "WARS.PRG"
...
RUN

### Quick reference
- **Accepted ROM formats:** `.bas`, `.img`, `.prg`
- **Folder:** `/userdata/roms/commanderx16`

| Emulators |
| x16emu |

## ROMs
Place your Commander X16 in `/userdata/roms/commanderx16`.

## Controls
Here are the default Commander X16 controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).