# Hypseus Singe

**Source:** https://wiki.batocera.org/systems:singe  
**Last fetched:** 2025-12-06 16:19:47

---

# Hypseus Singe
[SINGE](https:*kangaroopunch.com/view/ShowSoftware?id=7) (or Singe) is the **S**omewhat **I**nteractive **N**ostalgic **G**ame **E**ngine ((As quoted on their website)), a Lua-based scripting system that allows LaserDisc or any pre-recorded video source games to be simulated as a playable game. The [Hypseus fork](https:*github.com/DirtBagXon/hypseus-singe), integrating compatibility with SINGE-based games, refers it simply as Hypseus Singe­.

This system scrapes metadata for the `daphne, arcade` group(s) and loads the `singe` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [SINGE/Hypseus](#singe/hypseus)
- **Folder:** `/userdata/roms/singe/`
- **Accepted ROM formats:** `.daphne` `.squashfs`

## BIOS
No Singe simulator in Batocera needs a BIOS file to run.

## ROMs

Since v40, Singe-based games (**not to be confused with [DAPHNE](systems:daphne)**) must be placed in `/userdata/roms/singe/`. 

If you are on Batocera prior to v40, place your ROMs in `/userdata/roms/daphne/` instead.

Place your Singe ROMs in `/userdata/roms/singe/`. 

Depending on what assets you have, there are two versions of Singe: `Singe 1.x` from 2006 and `Singe 2.x` from 2020.

All Singe assets are available from the [Hypseus Singe data repository](https://github.com/DirtBagXon/hypseus_singe_data/releases).

### Asset version per stable Batocera release
It is important to download the right asset version for your Batocera version. Newer asset version won't work for older versions of Hypseus SINGE.Refer to the following list:

| Batocera version  | Hypseus SINGE version  | Link to asset version                                                                      | Notes                  |
| Batocera v42      | Hypseus SINGE 2.11.5   | [Download link](https://github.com/DirtBagXon/hypseus_singe_data/releases/tag/v2.11.5-1)  |                        |
| Batocera v41      | Hypseus SINGE 2.11.3   | [Download link](https://github.com/DirtBagXon/hypseus_singe_data/releases/tag/v2.11.3-1)  |                        |
| Batocera v40      | Hypseus SINGE 2.11.2   | [Download link](https://github.com/DirtBagXon/hypseus_singe_data/releases/tag/v2.11.2-9)  |                        |
| Batocera v39      | Hypseus SINGE 2.11.1   | [Download link](https://github.com/DirtBagXon/hypseus_singe_data/releases/tag/v2.11.1-3)  |                        |
| Batocera v38      | Hypseus SINGE 2.11.1   | [Download link](https://github.com/DirtBagXon/hypseus_singe_data/releases/tag/v2.11.1-3)  |                        |
| Batocera v37      | Hypseus SINGE 2.10.4   | [Download link](https://github.com/DirtBagXon/hypseus_singe_data/releases/tag/v2.10.4-5)  |                        |
| Batocera v36      | Hypseus SINGE 2.10.2   | [Download link](https://github.com/DirtBagXon/hypseus_singe_data/releases/tag/v2.10.2-1)  |                        |
| Batocera v35      | Hypseus SINGE 2.8.3    | [Download link](https://github.com/DirtBagXon/hypseus_singe_data/releases/tag/v2.10.1-2)  | Singe 1.x assets only  |
| Batocera v34      | Hypseus SINGE 2.8.2    | [Download link](https://github.com/DirtBagXon/hypseus_singe_data/releases/tag/v2.10.1-2)  | Singe 1.x assets only  |
| Batocera v33      | Hypseus SINGE 2.8.0    | [Download link](https://github.com/DirtBagXon/hypseus_singe_data/releases/tag/v2.10.1-2)  | Singe 1.x assets only  |
| Batocera v32      | Hypseus SINGE 2.6.12   | [Download link](https://github.com/DirtBagXon/hypseus_singe_data/releases/tag/v2.10.1-2)  | Singe 1.x assets only  |

### Singe 1.x
Singe 1.x are legacy assets mostly known and used with limited functionnalities.

The file structure consists of a directory with the ending `.daphne` (containing video, audio and text files) in the folder `/roms/`. For example, `freedomfighter`:

```

roms
|-- singe
|    |
|    |-- freedomfighter.daphne (contains all the assets at root level)
|    |    |-- cdrom folder (image and audio ROMs)
|    |    |-- ...
|    |    |-- freedomfighter.singe (LUA-script file)
|    |    |-- freedomfighter.txt (Framefile)
|    |    |-- ...

```

### Singe 2.x

**Many Singe 2 ROMs require `Framework` folder to work.**

It must be downloaded from the [Hypseus Singe data repository](https://github.com/DirtBagXon/hypseus_singe_data/releases).

Singe 2.x are newer assets with some nice new features like animated spirtes and compatibility with HD upscaled games.

To install the newer assets, let's use `Asterix` ROM for example.:

`

As mentionned, we will download and extract `singe2` assets from the Hypseus Singe data repository.

First, navigate to `/00-singe2/` folder. You should find `Asterix` folder there:

Rename the folder `Asterix` to `Asterix.daphne` and copy it into Batocera `/userdata/roms/singe/` along with `Framework` folder. 

Upload `asterix.m2v` and `asterix.ogg` files into `Video` folder of the ROM asset (`/userdata/roms/singe/Asterix.daphne/Video/`):

The file structure consists of a directory with the ending `.daphne` (containing video, audio and text files subdivided by folders) in the folder `/roms/`. For example, `Asterix`:

```

roms
|-- singe
|    |
|    |-- Asterix.daphne     
|    |    |-- Cfg
|    |    |-- Fonts
|    |    |-- Overlay
|    |    |-- Script
|    |    |-- Sounds
|    |    |-- Video (ROM files go into this folder)
|    |    |    |-- asterix.m2v  (image ROM)
|    |    |    |-- asterix.ogg  (audio ROM)
|    |
|    |-- Framework

```

## Simulators
### SINGE/Hypseus
SINGE is the most known simulator for video-based games. We use the [Hypseus Singe](https:*github.com/DirtBagXon/hypseus-singe), a fork of the [original DAPHNE emulator](http:*www.daphne-emu.com/).

#### SINGE/Hypseus configuration
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

## Controls
Here are the default Hypseus singe's controls shown on a [Batocera Retropad](:configure_a_controller):

| Gamepad | Arcade |
| SELECT | Input Coin |
| START | START Player 1 |
| A | Action Button |
| X | Singe Overlay |
| D-pad | Stick |

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).