# Atomiswave

**Source:** https://wiki.batocera.org/systems:atomiswave  
**Last fetched:** 2025-12-06 16:18:43

---

# Atomiswave
The Atomiswave is a arcade developed by the Sammy Corporation. It was released in 2003. It is based on Sega's [Dreamcast](systems:Dreamcast) console, and thus shares a lot of its hardware with it. Because of this, emulation of NAOMI games is usually best done with a Dreamcast emulator (modifications have already been made to allow for this in Flycast, for instance).

The Atomiswave is known for using interchangeable game cartridges for its games, allowing for easy switching between them. In this same vein, the cabinet's control panel could be swapped out as well, allowing for a variety of sticks, lightguns and steering wheel JAMMA peripherals to be used by a single system. This made it a very attractive option for arcades wanting to make the most of their purchase.

With the retirement of the [Neo Geo](systems:neogeo) MVS, SNK chose to use the Atomiswave as its next system to develop games for. However, after the release of Metal Slug 6, SNK moved onto other systems. Sammy itself would develop the majority of titles for its arcade system. In 2004, Sammy would end up merging with Sega.

This system scrapes metadata for the "atomiswave" and "arcade" groups and loads the `atomiswave` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.lst`, `.bin`, `.dat`, `.zip`, `.7z`
- **Folder:** `/userdata/roms/atomiswave`

| Emulators |
| [libretro: Flycast](#libretro:_flycast) |
| [Flycast](#flycast) |

## BIOS
Batocera FIXME and above:

| MD5 checksum | Share file path | Description |
| `0ec5ae5b5a5c4959fa8b43fcf8687f7c` | `bios/dc/awbios.zip` | |

Batocera FIXME and below:

| MD5 checksum | Share file path | Description |
| `0ec5ae5b5a5c4959fa8b43fcf8687f7c` | `bios/awbios.zip` | |

## ROMs
Place your Atomiswave ROMs in `/userdata/roms/atomiswave`.

## Emulators
### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: Flycast
A fork of a fork of a fork... this is an identical version of standalone Flycast but inside of a libretro core, maintained by the same dev as standalone, Flyinghead. Makes use of RetroArch's features.

##### libretro: Flycast configuration
Standardized features for this core: `atomiswave.autosave`, `atomiswave.use_guns`, `atomiswave.cheevos`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **SYNCHRONOUS RENDERING `global.reicast_synchronous_rendering`** | When threaded rendering is on (on by default), waits for the GPU to finish rendering the frame before dropping the current one. This can avoid certain emulation issues (flashing screens, glitchy video). Significant performance cost. Recommended "Off" for most games as they don't experience issues (or you have a weak machine), "On" if the game has these particular issues.\\ => Off `disabled`, On `enabled`. |
| **RENDERING RESOLUTION `global.reicast_internal_resolution`** | Enhancement. Increases the rendering resolution. Makes 3D objects clearer. Significant performance cost. Use 640x480 for native. Absurdly high values can degrade image quality (pixels beginning to shimmer).\\ => 1x (640x480) `640x480`, 1.25x (800x600) `800x600`, 1.5x (960x720) `960x720`, 1.6x (1024x768) `1024x768`, 2x (1280x960) `1280x960`, 2.25x (1440x1080) `1440x1080`, 2.5x (1600x1200) `1600x1200`, 3x (1920x1440) `1920x1440`, 4x (2560x1920) `2560x1920`, 5x (3200x2400) `3200x2400`, 6x (3840x2880) `3840x2880`, 7x (4480x3360) `4480x3360`, 8x (5120x3840) `5120x3840`, 9x (5760x4320) `5760x4320`, 10x (6400x4800) `6400x4800`, 11x (7040x5280) `7040x5280`, 12x (7680x5760) `7680x5760`. |
| **TARGET COLOR FOR PLAYER 1. `global.reicast_lightgun1_crosshair`** | \\ => Red `Red`, Blue `Blue`, Green `Green`, White `White`, Disabled `disabled`. |
| **TARGET COLOR FOR PLAYER 2. `global.reicast_lightgun2_crosshair`** | \\ => Red `Red`, Blue `Blue`, Green `Green`, White `White`, Disabled `disabled`. |
| **TARGET COLOR FOR PLAYER 3. `global.reicast_lightgun3_crosshair`** | \\ => Red `Red`, Blue `Blue`, Green `Green`, White `White`, Disabled `disabled`. |
| **TARGET COLOR FOR PLAYER 4. `global.reicast_lightgun4_crosshair`** | \\ => Red `Red`, Blue `Blue`, Green `Green`, White `White`, Disabled `disabled`. |
| **TEXTURE MIP-MAPPING (BLUR) `global.reicast_mipmapping`** | Enables [mip-mapping](:anti-aliasing#mip-mapping) to smooth out textures on distant 3D objects based on distance and angle. Dreamcast games natively utilized mipmapping to get extra performance out of the hardware, but the extra bluriness from doing this is more apparent on modern, higher fidelity screens. Has a minimal performance cost. `enabled` should be used in conjunction with anisotropic filtering to mitigate bluriness. Some users may prefer the 'sharpness' of `disabled` better.\\ => Off `disabled`, On `enabled`. |
| **ANISOTROPIC FILTERING `global.reicast_anisotropic_filtering`** | Enables [anisotropic filtering](:anti-aliasing#anisotropic_filtering) to enhance perspective textures. Dramatically improves the clarity of textures on distant 3D objects when mip-mapping is turned on, especially at higher internal resolutions. Test Drive: Le Mans is the only Dreamcast game that natively utilizes this. Has a small performance cost. Generally safe to use 16x when mip-mapping is also enabled, leave on "Off" otherwise.\\ => Off `False`, 2x `2`, 4x `4`, 8x `8`, 16x `16`. |
| **TEXTURE UPSCALING (XBRZ) `global.reicast_texupscale`** | Enhancement. Applies [xBRZ upscaling to textures](:anti-aliasing#texture_enhancement) to improve their clarity. Improvements are subjective.\\ => Off `False`, 2x `2x`, 4x `4x`, 6x `6x`. |
| **RENDER TO TEXTURE UPSCALING `global.reicast_render_to_texture_upscaling`** | (FIXME this setting is now missing?) Enhancement. Some 3D games would capture the screen output and render it as a 2D texture (eg. pause menu in Crazy Taxi and Dead or Alive), being unaffected by `reicast_internal_resolution`. This setting multiplies the resolution of that capture. Example [here](:anti-aliasing#dreamcast_render_to_texture_enhancement). "Off" for native, "4x" for close-to 1080p rendering (only useful if also upscaling the internal resolution).\\ => Off `1x`, 2x `2x`, 3x `3x`, 4x `4x`, 8x `8x`. |
| **FRAMESKIP `global.reicast_frame_skipping`** | Skip frames to improve performance, at the cost of choppy motion. Higher values can cause motion sickness if used for extended periods. Should only be turned up on weak hardware and if immune to motion sickness.\\ => Off `disabled`, 1 `1`, 2 `2`, 3 `3`, 4 `4`, 5 `5`, 6 `6`. |
| **FORCE WINDOWS CE MODE `global.reicast_force_wince`** | Some Dreamcast games (marked "Powered by Microsoft Windows CE" on the box, eg. Sega Rally 2) utilized the MMU Windows Compact Edition API on the Dreamcast to run. Batocera should automatically detect this but in case it doesn't you can manually override it here. Significant performance cost.\\ => Off `disabled`, On `enabled`. |
| **WIDESCREEN CHEAT (PRIORITY) `global.reicast_widescreen_cheats`** | Enhancement. Flycast has a database of cheats that can enable widescreen support in certain games, rendering them in [anamorphic widescreen](wp>Anamorphic_widescreen) without changing the internal resolution. Some games also natively support widescreen in their in-game options. A 16/9 ratio must be used and bezels must be disabled.\\ => Off `disabled`, On `enabled`. |
| **WIDESCREEN HACK `global.reicast_widescreen_hack`** | Enhancement. Changes the internal resolution to a widescreen ratio (eg. 640x480 becomes 853x480). Somewhat glitchy. Some games also natively support widescreen in their in-game options. A 16/9 ratio must be used and bezels must be disabled.\\ => Off `disabled`, On `enabled`. |
| **CONTROLLER 1 TYPE `global.controller1_dc`** | Chooses the controller plugged into port 1.\\ => Gamepad `1`, Keyboard `3`, Mouse `2`, Light Gun `4`. |
| **CONTROLLER 2 TYPE `global.controller2_dc`** | Same as above for port 2.\\ => Gamepad `1`, Keyboard `3`, Mouse `2`, Light Gun `4`. |
| **CONTROLLER 3 TYPE `global.controller3_dc`** | Same as above for port 3.\\ => Gamepad `1`, Keyboard `3`, Mouse `2`, Light Gun `4`. |
| **CONTROLLER 4 TYPE `global.controller4_dc`** | Same as above for port 4.\\ => Gamepad `1`, Keyboard `3`, Mouse `2`, Light Gun `4`. |
| Settings specific to atomiswave ||
| **SCREEN ORIENTATION `atomiswave.screen_rotation_atomiswave`** | Rotate screen for some arcade games\\ => Horizontal `horizontal`, Vertical `vertical`. |

All other settings can be configured from RetroArch's **Quick Menu** -> **Options** (`[HOTKEY]` + ).

### Flycast
[Flycast](https:*github.com/flyinghead/flycast) is a fork of [Reicast](https:*reicast.com/) (which itself is a fork of nullDC). A highly compatible and accurate standalone Dreamcast emulator.

Flycast can also be used to run Atomiswave arcade games due to being nearly identical hardware.

#### Flycast configuration
Standardized features available to all cores of this emulator: `atomiswave.videomode`, `atomiswave.videomode`, `atomiswave.bezel`, `atomiswave.bezel_stretch`, `atomiswave.hud`, `atomiswave.hud_corner`, `atomiswave.bezel.tattoo`, `atomiswave.bezel.tattoo_corner`, `atomiswave.bezel.tattoo_file`, `atomiswave.bezel.resize_tattoo`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **SCREEN RATIO `naomi.flycast_ratio`** | Choose which screen ratio you want to use.\\ => Default `False`, Widescreen `True`. |
| **RENDER RESOLUTION `naomi.flycast_render_resolution`** | Choose which internal rendering resolution you want to use.\\ => 0.5x (320x240) `240`, 1x (640x480) `480`, 1.5x (960x720) `720`, 2x (1280x960) `960`, 2.5x (1600x1200) `1200`, 3x (1920x1440) `1440`, 4x (2560x1920) `1920`, 4.5x (2880x2160) `2160`. |
| **GRAPHICS API `naomi.flycast_renderer`** | Choose your graphics renderer.\\ => OpenGL (Default) `0`, Vulkan `4`. |
| **ROTATE SCREEN 90 DEGREES `naomi.flycast_rotate`** | Rotate the screen by 90 degrees.\\ => Normal `False`, Rotate `True`. |
| **ANISOTROPIC FILTERING `atomiswave.flycast_anisotropic`** | Higher values make textures viewed at oblique angles look sharper.\\ => Disbaled (Default) `1`, 2x `2`, 4x `4`, 8x `8`, 16x `16`. |

All other configuration must be done via the `flycast-config` in the Applications folder (`[F1]` on the systems screen).

## Controls

How does this even work?

Here are the default Atomiswave's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).