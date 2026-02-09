# IKEMEN

**Source:** https://wiki.batocera.org/systems:ikemen  
**Last fetched:** 2025-12-06 16:19:06

---

This article needs some TLC. Read at your own risk.

# IKEMEN
The IKEMEN is a port developed by Elecbyte. It was released in 2021.

This system scrapes metadata for the "ikemen" group(s) and loads the `ikemen` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [ikemen](#ikemen)
- **Folder:** `/userdata/roms/ikemen`
- **Accepted ROM formats:** `.ikemen`, `.pc`

## BIOS
No IKEMEN emulator in Batocera needs a BIOS file to run.

## ROMs
Place your IKEMEN ROMs in `/userdata/roms/ikemen`.

IKEMEN Go is a reimplementation of IKEMEN, an engine which extends the capacities of MUGEN for fighting games.

Certain IKEMEN games may require a specific version of IKEMEN to run. Those are best served by copying the entire engine into a WINE container instead. For reference, the versions of IKEMEN and the dates they were bumped can be found on the [changelog](https://batocera.org/changelog).

Batocera v36 to 39 use version 0.98.2. This is not mentioned in the changelog as of writing.

Batocera 40 uses 0.99, and some games need to be updated with new files when upgrading to 0.99.

## Emulators
### ikemen
#### ikemen configuration
Standardized features available to all cores of this emulator: `ikemen.videomode`, `ikemen.padtokeyboard`, `ikemen.videomode`, `ikemen.bezel`, `ikemen.bezel_stretch`, `ikemen.hud`, `ikemen.hud_corner`, `ikemen.bezel.tattoo`, `ikemen.bezel.tattoo_corner`, `ikemen.bezel.tattoo_file`, `ikemen.bezel.resize_tattoo`

## Controls
FIXME

## Troubleshooting
### Error window at the start of the game
You launch a game and get an error window telling:```

Error while loading the config file.
json: cannot unmarshal string into Go struct
(...)

```
A simple fix is often to remove the file `save/config.json` from your Ikemen game folder. This can happen when you upgrade from Ikemen 0.98.x to 0.99 (i.e. when you upgrade from a previous Batocera version to 40+). When you delete `config.json` it also means that you have to set up again the parameters from your Ikemen game: resolution, difficulty, etc.

### In-game: missing files
If you can launch the game, but then get an error telling that a file ending with the extension `.zss` is missing, this is also probably an error caused by upgrading Ikemen form 0.98 to 0.99. To fix that, go to the `data/` directory of your Ikemen game folder and verify that you have all the following files present:```

action.zss
common1.cns.zss
dizzy.zss
functions.zss
guardbreak.zss
score.zss
tag.zss
training.zss

```

If one or more of these files are missing, you can get them [from the Ikemen Go GitHub repository](https://github.com/ikemen-engine/Ikemen-GO/tree/develop/data), and add them into that directory.

### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).