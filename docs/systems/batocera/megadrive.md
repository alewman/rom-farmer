# Sega Mega Drive/Genesis

**Source:** https://wiki.batocera.org/systems:megadrive  
**Last fetched:** 2025-12-06 16:19:14

---

# Sega Mega Drive/Genesis
The Sega Mega Drive, known as the Sega Genesis in the US, is a 16-bit fourth-generation console released by Sega in Japan on October 29, 1988 and in the US on August 14, 1989. It retailed for $189.99.

The design of the console differs between regions, newer EmulationStation themes may have an option in their theme configuration to select which one to show in the system menu, but many older ones may just have two 'region variations' to download which have different images, the Megadrive/Genesis just being one of the consoles changed.

The Mega Drive/Genesis is backwards compatible with the Master System.

This system scrapes metadata for the "genesis" and "megadrive" groups and loads the `megadrive` set from the currently selected theme, if available.

Grouped with the "megadrive" group of systems.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Cores available:** [libretro: GenesisPlusGX](#libretro:_genesisplusgx), [libretro: GenesisPlusGX-wide](#libretro:_genesisplusgx-wide), [libretro: picodrive](#libretro:_picodrive), [libretro: blastem](#libretro:_blastem)
- **Folder:** `/userdata/roms/megadrive`
- **Accepted ROM formats:** `.bin`, `.gen`, `.md`, `.sg`, `.smd`, `.zip`, `.7z`

## BIOS
Mega Drive/Genesis emulators do not require the BIOS files to run.

## ROMs
Place your Sega Mega Drive/Genesis ROMs in `/userdata/roms/megadrive`.

`.md`, `.bin`, `.gen`, `.sg`, `.smd`, `.gg` and `.sms` are cartridge-based ROMs. `.iso`, `.cue` + `.bin` and `.chd` are disc-based images and should be used with the [CD](systems:segacd) system instead.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all cores of this emulator: `megadrive.videomode`, `megadrive.ratio`, `megadrive.smooth`, `megadrive.shaders`, `megadrive.pixel_perfect`, `megadrive.decoration`, `megadrive.game_translation`

| ES setting name `batocera.conf key` | Description >> ES option `key value` |
| Settings that apply to all cores of this emulator |
| **GRAPHICS BACKEND `megadrive.gfxbackend`** | Choose your graphics rendering.\\ >> OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `megadrive.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles.\\ >> 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `megadrive.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: GenesisPlusGX
A good all-around emulator. It can run Sega Genesis/Mega Drive, Sega Master System, Sega/Mega CD and Game Gear games, but lacks 32X and Pico support. It is also the only emulator to support Lock-On technology, but can only be activated in RetroArch's Quick Menu (`[HOTKEY]` + ). After resetting the game, Lock-On will be activated. By default, Batocera will reset this setting after exiting the game. This can be changed on a per-game basis by using RetroArch's Overrides. There are patches available for ROMs that set the flag to boot into their Lock-On ROMs instead, so this is not strictly required to play those games.

##### libretro: GenesisPlusGX configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **REDUCE SPRITE FLICKERING `global.gpgx_no_sprite_limit`** | The Megadrive/Genesis can only draw ~80 sprites per horizontal line at a time, and any more will be mitigated by rapidly flickering between them each frame. This setting removes that limitation. Some games rely on the limit to mask certain sprites, but is generally not noticeable when removed.\\ => Off `disabled`, On `enabled`. |
| Settings specific to megadrive ||
| **NTSC FILTER `megadrive.gpgx_blargg_filter_md`** | GenesisPlusGX has the Blarg NTSC filter built-in as a feature, unrelated to the shader selected within Batocera. This applies only to Megadrive/Genesis games. Batocera's or RetroArch's preset shaders can be used instead.\\ => Off `False`, Composite (color bleeding + artifacts) `composite`, SVideo (color bleeding only) `svideo`, RGB (crisp image) `rgb`. |
| **SHOW LIGHTGUN CROSSHAIR `megadrive.gun_cursor_md`** | Shows crosshairs for Menacer and Justifiers devices. This applies only to Megadrive/Genesis games.\\ => Off `disabled`, On `enabled`. |
| **CONTROLLER 1 TYPE `megadrive.controller1_md`** | The Megadrive/Genesis has many types of peripherals, notably a 6-button controller that some games require to be fully functional and a few lightguns. This is also where you would set your multi-tap on, if required.\\ => Joypad Auto `1`, Joypad 3 Button `257`, Joypad 6 Button `513`, Joypad 3 Button + 4-WayPlay `1025`, Joypad 6 Button + 4-WayPlay `1281`, Joypad 3 Button + Teamplayer `1537`, Joypad 6 Button + Teamplayer `1793`, [Mouse](https://www.youtube.com/watch?v=47PikGHpHkg) `2`. |
| **CONTROLLER 2 TYPE `megadrive.controller2_md`** | Same as above but also has the Menacer Light Gun and Konami Justifiers available.\\ => Joypad Auto `1`, Joypad 3 Button `257`, Joypad 6 Button `513`, Joypad 3 Button + 4-WayPlay `1025`, Joypad 6 Button + 4-WayPlay `1281`, Joypad 3 Button + Teamplayer `1537`, Joypad 6 Button + Teamplayer `1793`, Mouse `2`, Menacer Light Gun `516`, Konami Justifiers `772`. |
| Settings specific to mastersystem ||
| **NTSC FILTER `mastersystem.gpgx_blargg_filter_ms`** | GenesisPlusGX has the Blarg NTSC filter built-in as a feature, unrelated to the shader selected within Batocera. This applies only to Master System games. Batocera's or RetroArch's preset shaders can be used instead.\\ => Off `False`, Composite (color bleeding + artifacts) `composite`, SVideo (color bleeding only) `svideo`, RGB (crisp image) `rgb`. |
| **FM CHIP (YM2413) `mastersystem.ym2413`** | Enhanced sound output support for compatible games.\\ => Autodetect `automatic`, Off `disabled`, On (forced) `enabled`. |
| **SHOW LIGHTGUN CROSSHAIR `mastersystem.gun_cursor_ms`** | Shows crosshairs for Menacer and Justifiers devices. This applies only to Master System games.\\ => Off `disabled`, On `enabled`. |
| **CONTROLLER 1 TYPE `mastersystem.controller1_ms`** | Select 2 button controller, Lightgun or Multitap.\\ => Joypad 2 Button `769`, Joypad 2 Button + Master Tap `2049`, Light Phaser `260`, Paddle Control `261`. |
| **CONTROLLER 2 TYPE `mastersystem.controller2_ms`** | Select 2 button controller, Lightgun or Multitap.\\ => Joypad 2 Button `769`, Joypad 2 Button + Master Tap `2049`, Light Phaser `260`, Paddle Control `261`. |
| Settings specific to gamegear ||
| **LCD GHOSTING FILTER `gamegear.lcd_filter`** | Simulate LCD ghosting effects.\\ => Off `disabled`, On `enabled`. |
| **EXTENDED SCREEN `gamegear.gg_extra`** | Extend the game screen area like on a Master System.\\ => Off `disabled`, On `enabled`. |

#### libretro: GenesisPlusGX-wide
A patched version of regular [GenesisPlusGX](#libretro:_genesisplusgx) that allows for widescreen video out. It is a bit buggier than the regular version but works fine in most games. Expect visual glitches when using this. The functions of this patch are slowly being integrated into the main build itself, but they are still separate (correct as of v31). Does not support Sega/Mega CD.

This core has no core-specific options adjustable from within Batocera. It will ignore the settings that libretro/genesisplusgx ordinarily uses. That being said, you can still change most of its configuration within RetroArch's **Quick Menu** -> **Options** ( `[HOTKEY]` + ). To enable the widescreen hack, change "Extra columns to draw in H40 for widescreen" to a higher value. 10 works well for 16:9 screens. This may need to be adjusted on a per-game basis.

#### libretro: Picodrive
A lighter emulator which although not as accurate as GenesisPlusGX, can be run on much weaker hardware. This should be the default for devices such as the Raspberry Pi Zero and other sub-1GHz CPUs. Currently the only cross-architecture option for 32X and Pico games.

##### libretro: Picodrive configuration
| ES setting name `batocera.conf key` | Description >> ES option `key value` |
| Settings that apply to all systems this core supports |
| **REDUCE SPRITE FLICKERING `gamegear.picodrive_sprlim`** | The Megadrive can only draw ~80 sprites per horizontal line at a time, and any more will be mitigated by rapidly flickering between them each frame. This setting removes that limitation. Some games rely on the limit to mask certain sprites, but is generally not noticeable when removed.\\ >> Off `disabled`, On `enabled`. |
| **CROP OVERSCAN `gamegear.picodrive_cropoverscan`** | Crops out video edge hidden under bezel of analog TV.\\ >> Off `disabled`, On `enabled`. |
| **CONTROLLER 1 TYPE `gamegear.picodrive_controller1`** | Select 3 or 6 button controller.\\ >> Joypad 3 Button `3 button pad`, Joypad 6 Button `6 button pad`. |
| **CONTROLLER 2 TYPE `gamegear.picodrive_controller2`** | Same as above, but for port 2.\\ >> Joypad 3 Button `3 button pad`, Joypad 6 Button `6 button pad`. |

### libretro: blastem
An emulator aiming to be cycle-accurate while still having modest system requirements. Very high compatibility.

This core has no core-specific options available (correct as of v31).

## Region
The Mega Drive/Genesis is special in that it was *technically* region-free, but the design of the cartridge prevented them from being inserted into consoles from other regions. If you could manage to insert them, however, the console would run the game mostly fine.

NA/JP games were typically coded first and are designed to run at 60Hz natively, whereas PAL games would run at 50Hz. Sometimes the game was simply slowed down by ~17% to match that frame-rate (inadvertently lowering the pitch of the music/sound effects) eg. Sonic 1, other games had additional logic to detect their region and adjust the music playback speed accordingly but otherwise slowed the gameplay down eg. Sonic 2, and a few games would alter both aspects to make NA/JP/PAL all play identically. Some ROMs use a universal (world) version that would rely on the console to detect its region, others have separate versions per region (US, JP, PAL, etc.) that may malfunction if played on a console of a different region.

In order to play a PAL game at 50Hz, first configure Batocera's video mode to be one of the '50Hz' modes eg. 1920x1080 50Hz (1920x1080). This can be done in the game's advanced options on a per-game basis or in a custom collection within EmulationStation. Then, when in-game, the core region must be set to 'pal' in RetroArch's Quick Menu (Hotkey+) > Options > Region. This can be saved via Quick Menu > Overrides > Save Game Overrides. Restart the game to apply.

It seems that Hz control is not available in the x86 builds through this menu. x86 users will have to use [xrandr](:display_issues#display_issues_when_xrandr_is_your_friend) instead to define their custom resolutions.

## Controls
Here are the Sega Mega Drive/Genesis' controls shown on a [Batocera Retropad](:configure_a_controller):

Mapping for all other compatible controllers:

## Troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).