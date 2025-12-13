# DAPHNE LaserDisc

**Source:** https://wiki.batocera.org/systems:daphne  
**Last fetched:** 2025-12-06 16:18:51

---

# DAPHNE LaserDisc
[DAPHNE](http:*www.daphne-emu.com) is the **F**irst **E**ver **M**ultiple **A**rcade **L**aserdisc **E**mulator!((As quoted on their website: http:*www.daphne-emu.com)) For legacy reasons, the [Hypseus fork](https://github.com/DirtBagXon/hypseus-singe) of the emulator may be referred to as simply DAPHNE.

A LaserDisc video game is an [arcade](:arcade) game that uses pre-recorded video (either live-action or animation) played from a LaserDisc. The first LaserDisc video game was Sega's Astron Belt released in 1983. The genre was popularized by Dragon's Lair released shortly after in the same year. The usage of LaserDiscs provided graphics close to an animated or live-action film which was vastly ahead of other arcade games at the time. However, with the drawback of limited interactivity compared to regular arcade games.

Cool website about Laserdisc games: http://www.dragons-lair-project.com/games/

Another useful resource is AmberElec's wiki entry on it: https://amberelec.org/System-Laserdisc.html

This system scrapes metadata for the `daphne, arcade` group(s) and loads the `daphne` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [DAPHNE/Hypseus](#daphne/hypseus)
- **Folder:** `/userdata/roms/daphne`
- **Accepted ROM formats:** `.daphne` `.squashfs`

## BIOS
No Daphne emulator in Batocera needs a BIOS file to run.

## ROMs
Place your DAPHNE ROMs (**not to be confused with [singe](systems:singe)**) in `/userdata/roms/daphne/`. 

The file structure consists of a directory with the ending `.daphne` (containing video, audio and text files) and a corresponding `.zip` file in the folder roms. For example, `Dragon's Lair Enhancement 2.1`:

```

roms
|-- daphne
|    |   (The folder below holds a laserdisc...".daphne"
|    |   tells emulationstation to add this to the menu,
|    |   and "dle21" tells daphne to use that game engine)
|    |
|    |-- dle21.daphne     
|    |    |-- dle21.commands  (Optional extra command-
|    |    |                   line params!)
|    |    |-- dle21.txt      (Framefile)
|    |    |-- lair.m2v
|    |    |-- lair.ogg
|    |
|    |                (All roms go into this roms folder)
|    +-- roms
|         +-- dle21.zip

```

Without the additional `.zip` file in the `roms` folder the games will be recognized by Batocera but will not be playable!

## Emulators
### DAPHNE/Hypseus
DAPHNE is the most famous emulator for LaserDisc arcade games. It supports more games than MAME. We use the [Hypseus Singe](https:*github.com/DirtBagXon/hypseus-singe), a fork of the [original DAPHNE emulator](http:*www.daphne-emu.com/).

#### DAPHNE/Hypseus configuration
Standardized features available to all cores of this emulator: `daphne.videomode`, `daphne.ratio`, `daphne.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `daphne.gfxbackend`** | Choose which graphics API library to use. Vulkan may not work on all hardware.\\ => OpenGL `OpenGL`, Vulkan `Vulkan`. |
| **ASPECT RATIO `daphne.daphne_ratio`** | Not all games support stretching, depending on their video files.\\ => Original `original`, Stretch `stretch`, Force 4:3 `force_ratio`. |
| **SCREEN ROTATION `daphne.daphne_rotate`** | \\ => 0 degrees `0`, 90 degrees `90`, 270 degrees `270`. |
| **SMOOTH GAMES (BILINEAR FILTERING) `daphne.bilinear_filter`** | \\ => On `0`, Off `1`. |
| **SCANLINES `daphne.daphne_scanlines`** | Use with the stretch aspect ratio and adjust joystick sensitivity as required.\\ => Off `0`, On `1`. |
| **BLEND SPRITES (SINGE) `daphne.blend_sprites`** | Restore BLENDMODE outline on Singe sprites.\\ => Off `0`, On `1`. |
| **OVERLAY SIZE (SINGE) `daphne.overlay_size`** | \\ => Standard `0`, HD Gun Games `oversize`, Singe 2 Full `full`, Singe 2 Half `half`. |
| **ABSOLUTE MOUSE INPUT `daphne.abs_mouse_input`** | This option is required for some gun games when playing with a mouse.\\ => Off `0`, On `1`. |
| **INVERT AXIS `daphne.invert_axis`** | Invert the vertical joystick axis on flight games.\\ => Off `0`, On `1`. |
| **JOYSTICK TO CURSOR SENSITIVITY `daphne.singe_joystick_range`** | \\ => 5 `5`, 10 `10`, 15 `15`, 20 `20`. |
| **HIDE LIGHT GUN CROSSHAIRS `daphne.singe_crosshair`** | Hide crosshairs in supported games e.g. ActionMax.\\ => Off `0`, On `1`. |
| **SDL TEXTURE ACCESS STREAMING `daphne.daphne_texturestream`** | Can improve video performance. Do not use with ActionMax games or scanlines.\\ => Off `0`, On `1`. |
| **CUSTOM CONTROLLER `daphne.daphne_joy`** | Use controller settings manually defined in custom.ini.\\ => Off `0`, On `1`. |

## (Optional) Command line parameters
In `roms/daphne/<game>.daphne/<game>.commands`, extra command line parameters can be define. This is not required. For example, for Dragon's Lair in `roms/daphne/lair.daphne/lair.commands`:

```

-nocrc -noissues -nolog -noserversend -latency 950 -x 640 -y 480 -bank 1 00110111 -bank 0 10011000

```

## Controls
Here are the default Daphne's controls shown on a [Batocera Retropad](:configure_a_controller):

| Gamepad | Arcade |
| SELECT | Input Coin |
| START | START Player 1 |
| A | Action Button |
| X | DAPHNE Overlay |
| D-pad | Stick |

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).