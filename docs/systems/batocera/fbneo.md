# FinalBurn Neo

**Source:** https://wiki.batocera.org/systems:fbneo  
**Last fetched:** 2025-12-06 16:18:55

---

# FinalBurn Neo
The [FinalBurn Neo](https://github.com/finalburnneo/FBNeo) is a specialized multi-arcade emulator forked from FinalBurn Alpha after... [stuff happened](hardware:capcom_home_arcade). It was released in 2019.

Due to the complex nature of the situation, Batocera refers to FBNeo and FBAlpha almost interchangeably. And to add to the complexity, FBNeo shares a lot of characteristic with MAME as well. It's <wrap em>strongly</wrap> recommended to read the [arcade guide](:arcade) to become familiar with how arcade games in general work first.

This system scrapes metadata for the "arcade" group(s) and loads the `fbneo` set from the currently selected theme, if available.

### Quick reference
- **Folders:** `/userdata/roms/fbneo`, `/userdata/roms/neogeo`
- **Accepted ROM formats:** `.zip`, `.7z`

| Emulators |
| [libretro: FBAlpha](#libretro:_fbalpha) |
| [libretro: FBNeo](#libretro:_fbneo) |
| [fba2x](#fba2x) |

## BIOS
FBNeo requires certain BIOS files to be placed in `/userdata/roms/fbneo`. These are:

- **FBNeo v1.0.0.0:**
  - `neogeo.zip` - Neo Geo [BIOS only]
  - `pgm.zip` - PGM (Polygame Master) System BIOS [BIOS only]
  - `skns.zip` - Super Kaneko Nova System BIOS [BIOS only]
- **FBNeo v1.0.0.2:**
  - `bubsys.zip` - Bubble System BIOS
  - `cchip.zip` - C-Chip Internal BIOS [Internal ROM only]
  - `decocass.zip` - DECO Cassette System [BIOS only]
  - `isgsm.zip` - ISG Selection Master Type 2006 System Bios [BIOS only]
  - `midssio.zip` - Midway SSIO Sound Board Internal pROM [Internal pROM only]
  - `namcoc69.zip` - Namco C69 (M37702) (Bios) [BIOS only]
  - `namcoc70.zip` - Namco C70 (M37702) (Bios) [BIOS only]
  - `namcoc75.zip` - Namco C75 (M37702) (Bios) [BIOS only]
  - `neogeo.zip` - Neo Geo [BIOS only]
  - `nmk004.zip` - NMK004 Internal ROM [Internal rom]
  - `pgm.zip` - PGM (Polygame Master) System BIOS [BIOS only]
  - `skns.zip` - Super Kaneko Nova System BIOS [BIOS only]
  - `ym2608.zip` - YM2608 Internal ROM [Internal ROM only]

## ROMs
FBNeo uses ROMsets in similar vein to MAME. A table of which ROMset version is being used in whatever version of Batocera can be found on [the arcade guide](:arcade#romset_version_per_stable_batocera_release). If you came here before reading the [arcade guide](:arcade), <wrap em>read the arcade guide</wrap>.

The ROMs themselves should not be decompressed, FBNeo expects them in their provided `.zip`/`.7z` format.

Place your Final Burn Neo ROMs in `/userdata/roms/fbneo`. You can also place your NeoGeo games in this folder as well, but if you'd like to organize them into their own "system" you can place them in `/userdata/roms/neogeo` instead. This will make them appear as a dedicated system in EmulationStation.

## Emulators
### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: FBAlpha
a.k.a. fbalpha2012, this is an older build of FinalBurn Alpha that performs better on weaker SBCs like the RPi Zero.

Todo for this emulator: like everything.

#### libretro: FBNeo
A [libretro port](https:*github.com/libretro/FBNeo) of [FinalBurn Neo](https:*github.com/finalburnneo/FBNeo) is a specialized multi-arcade emulator forked from Final Burn Alpha after… [stuff happened](https://wiki.batocera.org/hardware:capcom_home_arcade). This is the most current version of FBNeo available in Batocera.

##### libretro: FBNeo configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **CPU CLOCK `global.fbneo-cpu-speed-adjust`** | Overclock or underclock the emulated CPU. Can be used to fix slowdown that occurs on the real arcade machine, but introduces instability/other issues. Only supported by some drivers.\\ => 30% `30%`, 40% `40%`, 50% `50%`, 60% `60%`, 70% `70%`, 80% `80%`, 90% `90%`, 100% `100%`, 110% `110%`, 120% `120%`, 130% `130%`, 140% `140%`, 150% `150%`, 160% `160%`, 170% `170%`, 180% `180%`, 190% `190%`, 200% `200%`. |
| **FRAMESKIP `global.fbneo-frameskip`** | Skip frames to improve performance, at the cost of choppy motion.\\ => No skipping `0`, Skip rendering of 1 frames out of 2 `1`, Skip rendering of 2 frames out of 3 `2`, Skip rendering of 3 frames out of 4 `3`, Skip rendering of 4 frames out of 5 `4`. |
| **CROSSHAIR (LIGHTGUN) `global.fbneo-lightgun-hide-crosshair`** | Show crosshair if playing with a lightgun device.\\ => Off `enabled`, On `disabled`. |
| Settings specific to neogeo ||
| **NEOGEO MODE `neogeo.fbneo-neogeo-mode-switch`** | Load appropriate Bios depending on your choice\\ => Console AES World `AES Asia`, Console AES Japan `AES Japan`, Arcade MVS Europe `MVS Asia/Europe`, Arcade MVS USA `MVS USA`, Arcade MVS Japan `MVS Japan`, Arcade Universe BIOS (Cheats) `Universe BIOS`. |
| **MEMORY CARD MODE `neogeo.fbneo-memcard-mode`** | Change the behavior for the memory card\\ => Off `disabled`, Shared `shared`, Per-game `per-game`. |

Per-game dipswitch configuration can be accessed via RetroArch's Quick Menu. While in-game, press `[HOTKEY]` + , then go to **Options** -> **Dip switch settings**. For per-machine service menus, check the [Dip Switches/Diagnostic Input](:arcade#configuration_menu_dip_switches_service_mode_systemgame_configuration_diagnostic_input) section.

### fba2x
A standalone version of Final Burn Alpha, this is a specialized fork of an older build of FBAlpha that performs better on weaker SBCs like the RPi Zero.

Todo for this emulator: like everything.

## How is this different from MAME?
It's... complicated and no paragraph long block on a random wiki can properly explain it, so take the rest of this with caution. But the general agreement between users is that FBNeo "focuses" more on speed and performance than MAME, though in practice there aren't many cases where one emulator performs better than another on the same game (with the same versioning, settings, etc.). FBNeo also has a smaller supported library, but still supports an impressively large number of games.  One differentiator that may be significant is that FBNeo supports  [RetroAchievements](:retroachievements_settings#in-links) and MAME does not.  

When it boils down to the pragmatic differences, if you're having issues with an arcade game it's worth trying it out from sets for both MAME and FBNeo to see if one does better than the other. Some people may also prefer the *simpler* romset conventions that FBNeo uses.

## Controls
Here are the default Final Burn Neo's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Frequently Asked Questions
For problems related to FBNeo itself, refer to [libretro FBNeo's F.A.Q.](https://github.com/libretro/FBNeo/blob/master/src/burner/libretro/README.md#frequently-asked-questions)

### Further troubleshooting
Most questions are answered in the [generic arcade guide](:arcade).

For further troubleshooting, refer to the [generic support pages](:support).