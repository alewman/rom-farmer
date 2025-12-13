# Sega NAOMI

**Source:** https://wiki.batocera.org/systems:naomi  
**Last fetched:** 2025-12-06 16:19:23

---

# Sega NAOMI
The Sega NAOMI (stands for "New Arcade Operation Machine Idea") is a arcade developed by Sega. It was released in 1998. Designed to be the successor to the [Model 3](systems:model3), it uses similar architecture to that of the [Dreamcast](systems:dreamcast). Because of this, emulation of NAOMI games is usually best done with a Dreamcast emulator (modifications have already been made to allow for this in Flycast, for instance). Features arcade games like Crazy Taxi, Dead or Alive 2 and Samba de Amigo.

Although "NAOMI" can refer to multiple different types of boards released by Sega during this time period, Batocera specifically refers to just the original NAOMI board released in 1998 when mentioning "NAOMI" (at least for now).

Due to the similarity between NAOMI and the Dreamcast, most games were also ported to the Dreamcast, and a few even getting ported to other consoles of the generation. It may be easier to attempt to emulate those than their arcade counterparts.

For those interested in the hardware aspect, [here's a cool article about it on Sega Retro](https://segaretro.org/Sega_NAOMI).

This system scrapes metadata for the "naomi" and "arcade" groups and loads the `naomi` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.lst`, `.bin`, `.dat`, `.zip`, `.7z`
- **Folder:** `/userdata/roms/naomi`

| Emulators |
| [libretro: Flycast](#libretro:_flycast) |
| [Flycast](#flycast) |

## BIOS
The BIOS is optional but should be included for best results. For Batocera FIXME and above:
| MD5 checksum | Share file path | Description |
| `eb4099aeb42ef089cfe94f8fe95e51f6` | `bios/dc/naomi.zip` | NAOMI MAME BIOS |

For Batocera FIXME and below:
| MD5 checksum | Share file path | Description |
| `eb4099aeb42ef089cfe94f8fe95e51f6` | `bios/naomi.zip` | NAOMI MAME BIOS |

Some games use extra BIOS files.  They are required when using [libretro: Flycast](#libretro:_flycast), and optional when using [Flycast](#flycast) but should be included for best results.

| MD5 checksum | Share file path | Description |
| | `bios/dc/hod2bios.zip` | The House of the Dead 2 MAME BIOS |
| | `bios/dc/f355dlx.zip` | Ferrari F355 Challenge Deluxe MAME BIOS |
| | `bios/dc/f355bios.zip` | Ferrari F355 Challenge Twin/Deluxe MAME BIOS |
| | `bios/dc/airlbios.zip` | Airline Pilots Deluxe MAME BIOS |

## ROMs
Place your Sega NAOMI ROMs in `/userdata/roms/naomi`. Flycast uses the [MAME ROMset](:arcade#romsets).

[User-friendly compatibility list for Flycast](https://github.com/libretro/flycast/issues/136).

If you're willing to search through code, [here's the list of all the expected ROM hashes](https://github.com/libretro/flycast/blob/master/core/hw/naomi/naomi_roms.h#L243).

Some NAOMI boards use just ZIP ROMs to run, but most others use a ZIP in addition to an image (or [CHD](:disk_image_compression#chd)) file. In order to use ROMs that come with a image, the image must be placed in a subfolder with the same name as the game's ZIP file with the MAME ID as its filename. For example:

```

roms/
└─ naomi/
   ├─ ikaruga/
   │  └─ gdl-0010.chd
   └─ ikaruga.zip

```

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `naomi.videomode`, `naomi.ratio`, `naomi.shaderset`, `naomi.smooth`, `naomi.integerscale`, `naomi.bezel`, `naomi.bezel_stretch`, `naomi.hud`, `naomi.bezel.tattoo`, `naomi.bezel.tattoo_corner`, `naomi.bezel.tattoo_file`, `naomi.bezel.resize_tattoo`, `naomi.ai_service_enabled`, `naomi.ai_target_lang`, `naomi.ai_service_url`, `naomi.ai_service_pause`, `naomi.integerscale`, `naomi.runahead`, `naomi.secondinstance`, `naomi.video_frame_delay_auto`, `naomi.vrr_runloop_enable`, `naomi.video_threaded`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `naomi.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `naomi.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **ALLOW ROTATION `naomi.video_allow_rotate`** | Allow cores to set rotation.\\ => On `true`, Off `false`. |
| **CONTROLLER TO LIGHTGUN `naomi.lightgun_map`** | Map controller inputs to lightgun inputs\\ => On `true`, Off `false`. |

#### libretro: Flycast
A fork of a fork of a fork... this is an identical version of standalone Flycast but inside of a libretro core. Makes use of RetroArch's features.

##### libretro: Flycast configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **SYNCHRONOUS RENDERING `global.reicast_synchronous_rendering`** | When threaded rendering is on (on by default), waits for the GPU to finish rendering the frame before dropping the current one. This can avoid certain emulation issues (flashing screens, glitchy video). Significant performance cost. Recommended "Off" for most games as they don't experience issues (or you have a weak machine), "On" if the game has these particular issues.\\ => Off `disabled`, On `enabled`. |
| **RENDERING RESOLUTION `global.reicast_internal_resolution`** | Enhancement. Increases the rendering resolution. Makes 3D objects clearer. Significant performance cost. Use 640x480 for native. Absurdly high values can degrade image quality (pixels beginning to shimmer).\\ => 640x480 `640x480`, 800x600 `800x600`, 960x720 `960x720`, 1024x768 `1024x768`, 1280x960 `1280x960`, 1440x1080 `1440x1080`, 1600x1200 `1600x1200`, 1920x1440 `1920x1440`, 2560x1920 `2560x1920`, 3200x2400 `3200x2400`, 3840x2880 `3840x2880`, 4480x3360 `4480x3360`, 5120x3840 `5120x3840`, 5760x4320 `5760x4320`, 6400x4800 `6400x4800`, 7040x5280 `7040x5280`, 7680x5760 `7680x5760`. |
| **TEXTURE MIP-MAPPING (BLUR) `global.reicast_mipmapping`** | Enables [mip-mapping](:anti-aliasing#mip-mapping) to smooth out textures on distant 3D objects based on distance and angle. Dreamcast games natively utilized mipmapping to get extra performance out of the hardware, but the extra bluriness from doing this is more apparent on modern, higher fidelity screens. Has a minimal performance cost. `enabled` should be used in conjunction with anisotropic filtering to mitigate bluriness. Some users may prefer the 'sharpness' of `disabled` better.\\ => Off `disabled`, On `enabled`. |
| **ANISOTROPIC FILTERING `global.reicast_anisotropic_filtering`** | Enables [anisotropic filtering](:anti-aliasing#anisotropic_filtering) to enhance perspective textures. Dramatically improves the clarity of textures on distant 3D objects when mip-mapping is turned on, especially at higher internal resolutions. Test Drive: Le Mans is the only Dreamcast game that natively utilizes this. Has a small performance cost. Generally safe to use 16x when mip-mapping is also enabled, leave on "Off" otherwise.\\ => Off `False`, 2x `2`, 4x `4`, 8x `8`, 16x `16`. |
| **TEXTURE UPSCALING (XBRZ) `global.reicast_texupscale`** | Enhancement. Applies [xBRZ upscaling to textures](:anti-aliasing#texture_enhancement) to improve their clarity. Improvements are subjective.\\ => Off `False`, 2x `2x`, 4x `4x`, 6x `6x`. |
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
| Settings specific to naomi ||
| **SCREEN ORIENTATION `naomi.screen_rotation_naomi`** | Rotate screen for some arcade games\\ => Horizontal `horizontal`, Vertical `vertical`. |

All other settings can be configured from RetroArch's **Quick Menu** -> **Options** (`[HOTKEY]` + ).

### Flycast
[Flycast](https:*github.com/flyinghead/flycast) is a fork of [Reicast](https:*reicast.com/) (which itself is a fork of nullDC). A highly compatible and accurate standalone Dreamcast emulator.

Flycast can also be used to run NAOMI arcade games due to being nearly identical hardware. Not all NAOMI games are [compatible](https://github.com/libretro/flycast/issues/136) yet but most of them are.

#### Flycast configuration
Standardized features available to all cores of this emulator: `dreamcast.videomode`, `dreamcast.videomode`, `dreamcast.bezel`, `dreamcast.bezel_stretch`, `dreamcast.hud`, `dreamcast.bezel.tattoo`, `dreamcast.bezel.tattoo_corner`, `dreamcast.bezel.tattoo_file`, `dreamcast.bezel.resize_tattoo`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **SCREEN RATIO `naomi.flycast_ratio`** | Choose which screen ratio you want to use.\\ => Default `False`, Widescreen `True`. |
| **RENDER RESOLUTION `naomi.flycast_render_resolution`** | Choose which internal rendering resolution you want to use.\\ => 320x240 (Half) `240`, 640x480 (Native) `480`, 960x720 (x1.5) `720`, 1280x960 (x2) `960`, 1600x1200 (x2.5) `1200`, 1920x1440 (x3) `1440`, 2560x1920 (x4) `1920`, 2880x2160 (x4.5) `2160`. |
| **GRAPHICS API `naomi.flycast_renderer`** | Choose your graphics renderer.\\ => OpenGL (Default) `0`, Vulkan `4`. |
| **ROTATE SCREEN 90 DEGREES `naomi.flycast_rotate`** | Rotate the screen by 90 degrees.\\ => Normal `False`, Rotate `True`. |

All other configuration must be done via the `flycast-config` in the Applications folder (`[F1]` on the systems screen).

## Controls

How does this even work?

Here are the default Sega Naomi's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### I cannot deactivate "Free Play" in some games
Emulationstation as of v41 (and current v42_beta) has no switch to deactivate “Free Play” on the NAOMI and NAOMI 2 systems. You have to use Retroarch core settings according to the Wiki, see https://wiki.batocera.org/advanced_retroarch_settings.

Sadly, when setting “Free Play” to “OFF” in this Retroarch menu, the setting is *ignored* by most of the games.

To get this setting accepted, you have to access the "System Menu" of the NAOMI game in question and set "COIN/CREDIT SETTING" to "# 1":

  - Enter the Retroarch menu (when in game, Hotkey + South).
  - Go to "Core Options" -> "System"
  - Set "Allow Arcade Service Buttons" to "ON" and "Set NAOMI Games to Free Play" to "OFF"
  - Exit the Retroarch menu using "Restart".
  - When in game, press "L3" to enter the System Menu of the game. "R3" is used to navigate this menu, "L3" to select an entry.
   - Navigate this way to "COIN ASSIGNMENTS"
  - Set "COIN/CREDIT SETTING" to "# 1".
  - Exit the System Menu by selecting "EXIT" twice.
  - Optionally you can now set "Allow Arcade Service Buttons" to "OFF" to prevent accidental entering of the game's system menu.

If "COIN/CREDIT SETTING" is set to "# 1", the game in question will respect the Retroarch setting for "Free Play", even if you set "Free Play" to "ON" in Retroarch again.

### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).