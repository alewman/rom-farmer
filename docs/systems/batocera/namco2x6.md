# Namco System 246/256

**Source:** https://wiki.batocera.org/systems:namco2x6  
**Last fetched:** 2025-12-06 16:19:22

---

This article needs some TLC. Read at your own risk.

# Namco System 246/256
The Namco System 246/256 is an arcade developed by Sony / Namco. It was released in 2000.

This system scrapes metadata for the "namco, sega, arcade" group(s) and loads the `namco2x6` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [play](#play)
- **Folder:** `/userdata/roms/namco2x6`
- **Accepted ROM formats:** `.zip`

## BIOS
No Namco System 246/256 emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Namco System 246/256 ROMs in `/userdata/roms/namco2x6`.

The Play! emulator provides `work in progress` support for Namco 246 & 256 systems.

Currently you will need a high performance system to be able to emulate supported games.

We recommend using the OpenGL API for now.

This rom directory should include a zip file based on the arcade id and a supporting folder with associated .chd file.

i.e. Tekken 4 -
  tekken4.zip
  |
  tekken4
  |
  ---tef1dvd0.chd

## Emulators
### play
#### play configuration
Standardized features available to all cores of this emulator: `namco2x6.videomode`, `namco2x6.padtokeyboard`, `namco2x6.powermode`, `namco2x6.tdp`, `namco2x6.videomode`, `namco2x6.bezel`, `namco2x6.bezel_stretch`, `namco2x6.hud`, `namco2x6.hud_corner`, `namco2x6.bezel.tattoo`, `namco2x6.bezel.tattoo_corner`, `namco2x6.bezel.tattoo_file`, `namco2x6.bezel.resize_tattoo`, `namco2x6.use_wheels`, `namco2x6.wheel_rotation`, `namco2x6.wheel_deadzone`, `namco2x6.wheel_midzone`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `namco2x6.play_api`** | Choose which graphics API library to use.\\ => OpenGL (Default) `0`, Vulkan `1`. |
| **OPENGL RENDERING RESOLUTION `namco2x6.play_scale`** | Enhancement. Increase the rendering resolution. Makes 3D objects clearer.\\ => 1x (~480) `1`, 2x (~960) `2`, 4x (~1920p) `4`, 8x (~4320p / 8k) `8`, 16x (~7680p / 16k) `16`. |
| **PRESENTATION MODE `namco2x6.play_mode`** | \\ => Fill Screen `0`, Fit Screen `1`, Original Size `2`. |
| **ENABLE WIDESCREEN `namco2x6.play_widescreen`** | Enable widescreen support.\\ => Disabled `false`, Enabled `true`. |
| **VSYNC `namco2x6.play_vsync`** | Fix screen tearing.\\ => Disabled `false`, Enabled `true`. |
| **SMOOTH GAMES (BILINEAR FILTERING) `namco2x6.play_filter`** | Only applicable when using OpenGL.\\ => Disabled `false`, Enabled `true`. |
| **LANGUAGE `namco2x6.play_language`** | Change the game's language.\\ => Japanese `0`, English `1`, French `2`, Spanish `3`, German `4`, Italian `5`, Dutch `6`, Portuguese `7`, Russian `8`, Korean `9`, Traditional Chinese `10`, Simplified Chinese `11`. |

## Controls
Here are the default Namco System 246/256's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).