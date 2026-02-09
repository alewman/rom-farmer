# NEO•GEO

**Source:** https://wiki.batocera.org/systems:neogeo  
**Last fetched:** 2025-12-06 16:19:24

---

# NEO•GEO
The NEO•GEO MVS (Multi Video System) is an arcade machine developed by SNK, released in 1990. Somewhat unique for arcade machines at the time, it used swappable cartridges (included with optional kits) which the business owner could use to install more games into the system (and avoid having to buy a whole new machine). This system was not available to the average home user.

The NEO•GEO AES (Advanced Entertainment System) is a home console based on the same hardware as the MVS. It was released in 1991. Originally only designed as a rental system for stores to loan out, due to high demand it was eventually released as a home console and retailed for the high price of $649.99 USD. It was based on the NEO•GEO arcade hardware released a year prior, allowing for an arcade-perfect experience at the home. It was also the first console ever to feature a memory card to save the game, allowing the user to carry their save games to other units (including the MVS for compatible games). This hardware would be upgraded a few years later in the form of the [NEO•GEO CD](systems:neogeocd), with its ability to read disc-based media and being a lot cheaper.

Due to being nearly identical hardware-wise, NEO•GEO AES games are emulated much the same way that regular arcade games are, so the regular arcade emulators are used. There's generally no differences between the arcade versions and the home versions of the games (in fact, the cartridges between the systems were identical, but the different form-factor prevented the carts from being shared between the systems). It's recommended to read up on the generic [arcade guide](:arcade) first as it will answer many questions.

An interesting video covering the system: [Modern Vintage Gamer's "The SNK Neo Geo was ahead of its time"](https://www.youtube.com/watch?v=XPAAvXrHE8Y)

This system scrapes metadata for the "neogeo" and "arcade" groups and loads the `neogeo` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.7z`, `.zip`
- **Folder:** `/userdata/roms/neogeo`

| Emulators |
| [fba2x](systems:fbneo#fba2x) |
| [libretro: FBNeo](systems:fbneo#libretro:_fbneo) |
| [libretro: imame4all](systems:mame#libretro:_imame4all) |
| [libretro: mame078plus](systems:mame#libretro:_mame078plus) |
| [libretro: mame0139](systems:mame#libretro:_mame0139) |
| [libretro: mame](systems:mame#libretro:_mame) |
| [MAME](systems:mame#mame) |

## BIOS
The BIOS used is dependent on the [ROMset version](#roms). Here is one known working version:

| MD5 checksum | Share file path | Description |
| `dffb72f116d36d025068b23970a4f6df` | `bios/neogeo.zip` | Neo Geo BIOS |

## ROMs
Place your NEO•GEO ROMs in `/userdata/roms/neogeo`.

They'll also work equally as well if placed into `/userdata/roms/mame`, however by placing them specifically in `neogeo` they'll get their own little system list.

Keep in mind that each ROMset will (mostly) only work with other ROMs/BIOS files from the same set. Refer to the [arcade guide](:arcade) for more info.

## Emulators
### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: FBNeo/FBAlpha
FBNeo has [its own page](systems:fbneo).

#### libretro: imame4all/mame078plus/mame0139/mame
MAME has [its own page](systems:mame).

### MAME
MAME has [its own page](systems:mame).

### fba2x
FBNeo has [its own page](systems:fbneo).

## Controls
Here are the default NEO•GEO's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
Most questions are answered in the [generic arcade guide](:arcade).

For further troubleshooting, refer to the [generic support pages](:support).