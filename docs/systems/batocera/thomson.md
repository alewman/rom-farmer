# Thomson - MO/TO (Theodore)

**Source:** https://wiki.batocera.org/systems:thomson  
**Last fetched:** 2025-12-06 16:19:52

---

This article needs some TLC. Read at your own risk.

# Thomson - MO/TO (Theodore)
The Thomson - MO/TO (Theodore) is a computer developed by Thomson. It was released in 1984.

This system scrapes metadata for the "thomson" group(s) and loads the `thomson` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: theodore](#libretro:_theodore)
- **Folder:** `/userdata/roms/thomson`
- **Accepted ROM formats:** `.fd`, `.sap`, `.k7`, `.m7`, `.m5`, `.rom`, `.zip`

## BIOS
No Thomson - MO/TO (Theodore) emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Thomson - MO/TO (Theodore) ROMs in `/userdata/roms/thomson`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `thomson.videomode`, `thomson.videomode`, `thomson.ratio`, `thomson.shaderset`, `thomson.smooth`, `thomson.integerscale`, `thomson.bezel`, `thomson.bezel_stretch`, `thomson.hud`, `thomson.bezel.tattoo`, `thomson.bezel.tattoo_corner`, `thomson.bezel.tattoo_file`, `thomson.bezel.resize_tattoo`, `thomson.ai_service_enabled`, `thomson.ai_target_lang`, `thomson.ai_service_url`, `thomson.ai_service_pause`, `thomson.runahead`, `thomson.secondinstance`, `thomson.video_frame_delay_auto`, `thomson.vrr_runloop_enable`, `thomson.video_threaded`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `thomson.gfxbackend`** | Choose which graphics API library to use. Vulkan may not work for every core.\\ => OpenGL `gl`, GLCore `glcore`, Vulkan `vulkan`. |
| **AUDIO LATENCY `thomson.audio_latency`** | In milliseconds. Can reduce crackling/cutting out.\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **ALLOW ROTATION `thomson.video_allow_rotate`** | Allow cores to set rotation.\\ => On `true`, Off `false`. |
| **CONTROLLER TO LIGHT GUN `thomson.lightgun_map`** | Map controller inputs to light gun inputs.\\ => On `true`, Off `false`. |

#### libretro: theodore
##### libretro: theodore configuration
Standardized features for this core: `thomson.rewind`, `thomson.autosave`, `thomson.netplay`, `thomson.padtokeyboard`

## Controls
Here are the default Thomson - MO/TO (Theodore)'s controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).