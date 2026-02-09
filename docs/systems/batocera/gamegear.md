# Sega Game Gear

**Source:** https://wiki.batocera.org/systems:gamegear  
**Last fetched:** 2025-12-06 16:19:00

---

# Sega Game Gear
The Sega Game Gear was Sega's response to Nintendo's popular Game Boy portable console. Released in Japan on October 6th, 1990, and then on April 26th of 1991 in North America and Europe. Touting color graphics and an illuminated screen, the Game Gear was poised to surpass the competition on its technical merits alone, but the initial price of $149.99 and the lackluster battery life were as an albatross hung from the Game Gear's proverbial neck.

This system scrapes metadata for the "gamegear" group(s) and loads the `gamegear` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Cores available:** [libretro: GenesisPlusGX](#libretro:_genesisplusgx), [libretro: Picodrive](#libretro:_picodrive)
- **Folder:** `/userdata/roms/gamegear`
- **Accepted ROM formats:** `.bin`, `.gg`, `.zip`, `.7z`

## BIOS
No Sega Game Gear emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Sega Game Gear ROMs in `/userdata/roms/gamegear`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `gamegear.videomode`, `gamegear.ratio`, `gamegear.smooth`, `gamegear.shaders`, `gamegear.pixel_perfect`, `gamegear.decoration`, `gamegear.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `gamegear.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `gamegear.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `gamegear.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: GenesisPlusGX
Genesis Plus GX is an open-source Sega 8/16 bit emulator focused on accuracy and portability. The source code, originally based on Genesis Plus 1.3 by Charles MacDonald, has been heavily modified & enhanced, with respect to initial goals and design, in order to improve the accuracy of emulation, implementing new features and adding support for extra peripherals, cartridge & systems hardware.

Genesis Plus GX has 100% compatibility with Genesis/Mega Drive, Sega/Mega CD, Master System, Game Gear, SG-1000 & Pico released software (including all unlicensed or known pirate dumps), also emulating backwards compatibility modes when available.

##### libretro: GenesisPlusGX configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **REDUCE SPRITE FLICKERING `global.gpgx_no_sprite_limit`** | Reduce sprite flickering when enabled\\ => Off `disabled`, On `enabled`. |
| Settings specific to megadrive ||
| **NTSC FILTER `megadrive.gpgx_blargg_filter_md`** | Enable blargg NTSC video filters\\ => Off `False`, Composite (color bleeding + artifacts) `composite`, SVideo (color bleeding only) `svideo`, RGB (crisp image) `rgb`. |
| **SHOW LIGHTGUN CROSSHAIR `megadrive.gun_cursor_md`** | Shows crosshairs for Menacer and Justifiers devices\\ => Off `disabled`, On `enabled`. |
| **CONTROLLER 1 TYPE `megadrive.controller1_md`** | Select 3 or 6 button controller, mouse or Multitap\\ => Joypad Auto `1`, Joypad 3 Button `257`, Joypad 6 Button `513`, Joypad 3 Button + 4-WayPlay `1025`, Joypad 6 Button + 4-WayPlay `1281`, Joypad 3 Button + Teamplayer `1537`, Joypad 6 Button + Teamplayer `1793`, Mouse `2`. |
| **CONTROLLER 2 TYPE `megadrive.controller2_md`** | Select controller, Multitap, mouse or Gun\\ => Joypad Auto `1`, Joypad 3 Button `257`, Joypad 6 Button `513`, Joypad 3 Button + 4-WayPlay `1025`, Joypad 6 Button + 4-WayPlay `1281`, Joypad 3 Button + Teamplayer `1537`, Joypad 6 Button + Teamplayer `1793`, Mouse `2`, Menacer Light Gun `516`, Konami Justifiers `772`. |
| Settings specific to mastersystem ||
| **NTSC FILTER `mastersystem.gpgx_blargg_filter_ms`** | Enable blargg NTSC video filters\\ => Off `False`, Composite (color bleeding + artifacts) `composite`, SVideo (color bleeding only) `svideo`, RGB (crisp image) `rgb`. |
| **FM CHIP (YM2413) `mastersystem.ym2413`** | Enhanced sound output support for compatible games\\ => Autodetect `automatic`, Off `disabled`, On (forced) `enabled`. |
| **SHOW LIGHTGUN CROSSHAIR `mastersystem.gun_cursor_ms`** | Shows crosshairs for Light Phaser device\\ => Off `disabled`, On `enabled`. |
| **CONTROLLER 1 TYPE `mastersystem.controller1_ms`** | Select 2 button controller, Lightgun or Multitap\\ => Joypad 2 Button `769`, Joypad 2 Button + Master Tap `2049`, Light Phaser `260`, Paddle Control `261`. |
| **CONTROLLER 2 TYPE `mastersystem.controller2_ms`** | Select 2 button controller, Lightgun or Multitap\\ => Joypad 2 Button `769`, Joypad 2 Button + Master Tap `2049`, Light Phaser `260`, Paddle Control `261`. |
| Settings specific to gamegear ||
| **LCD GHOSTING FILTER `gamegear.lcd_filter`** | Simulate LCD ghosting effects\\ => Off `disabled`, On `enabled`. |
| **EXTENDED SCREEN `gamegear.gg_extra`** | Extend the game screen area like on a Master System\\ => Off `disabled`, On `enabled`. |

#### libretro: Picodrive
##### libretro: Picodrive configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **REDUCE SPRITE FLICKERING `global.picodrive_sprlim`** | Reduce sprite flickering when enabled\\ => Off `disabled`, On `enabled`. |
| **CROP OVERSCAN `global.picodrive_cropoverscan`** | Crops out video edge hidden under bezel of analog TV\\ => Off `disabled`, On `enabled`. |
| **CONTROLLER 1 TYPE `global.picodrive_controller1`** | Select 3 or 6 button controller\\ => Joypad 3 Button `3 button pad`, Joypad 6 Button `6 button pad`. |
| **CONTROLLER 2 TYPE `global.picodrive_controller2`** | Select 3 or 6 button controller\\ => Joypad 3 Button `3 button pad`, Joypad 6 Button `6 button pad`. |

## Controls
Here are the default Sega Game Gear's controls shown on a [Batocera Retropad](:configure_a_controller):

The default button mapping to the Game Gear is as following:

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).