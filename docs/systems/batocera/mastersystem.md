# Sega Master System

**Source:** https://wiki.batocera.org/systems:mastersystem  
**Last fetched:** 2025-12-06 16:19:13

---

# Sega Master System
The Sega Master System (a.k.a. Master System II/Gam*Boy/Aladdin Boy/Comboy) is a home videogame console developed by Sega. It was released in 1985 in Japan, and then 1986 in North America. It retailed for $199 USD ($501 in 2021). It had a Zilog Z80A at 4 MHz with 8KB of RAM and 16KB of VRAM. It featured a Yamaha YM2602B VDP GPU.

Originally, it was just a remodelled version of the Sega Mark III, intended to be released outside of Japan (which all the [SG-1000](systems:sg1000) were exclusively released in up until this point).

The Master System II, a cheaper model of the Master System, was released four years later in North America, Australasia and Europe.

It's very likely you've never heard of this system, despite Sega's infamy in the fourth generation. The Mastery System was competing against the NES, shortly after the videogame crash of '86, so it was already on rocky ground. To top that off, Nintendo's licensing policies required platform exclusivity, so many games could *not* be ported to the Master System, even if the developers wanted to. In North America, it couldn't even be compared to the NES's significant market share, however it had great success in other markets including Europe, Brazil, South Korea and Australia. In fact, the PAL library of the Master System is considered more diversified than the others, due to having more backports of later [Genesis/Megadrive](systems:megadrive) games and a longer lifespan in general.

In particular, Brazilian toy and electronics manufacturer [Tectoy](wp>Tectoy) distributed created multiple licensed variants of the Master System beginning in 1989, four years before Nintendo would start distributing the NES in Brazil. Due to its earlier release and cheap manufacturing price, it had great continued success in the region. Tectoy would continue to manufacture the Master System and "plug and play" variants of it in Brazil long after its lifespan, even competing against systems like the PlayStation 4. Technically, it has been the longest "lived" console in all of history, but that may depend on your specifications of what "live" is.

The Master System's hardware design would later be miniaturized and repurposed for the portable [Game Gear](systems:gamegear) system. For this reason, the Game Gear featured many ports of Master System games, however games for the Master System were not directly compatible with the Game Gear (an adapter exists, but with issues). Tectoy would port some games made specifically for the Game Gear back to the Master System for its Brazilian market.

This system scrapes metadata for the "mastersystem" group and loads the `mastersystem` set from the currently selected theme, if available.

### Quick reference
- **Emulators:** [RetroArch](#retroarch) or [CLK](#CLK)
- **Cores available:** [libretro: GenesisPlusGX](#libretro:_genesisplusgx), [libretro: Picodrive](#libretro:_picodrive)
- **Folder:** `/userdata/roms/mastersystem`
- **Accepted ROM formats:** `.bin`, `.sms`, `.zip`, `.7z`

Starting with Batocera 42, you can also use CLK as a Sega Master System emulator.
## BIOS
No Sega Master System emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Sega Master System ROMs in `/userdata/roms/mastersystem`.

## Emulators
Due to the Master System's similarities to the Game Gear, most Master System emulators are also Game Gear emulators. Most Master System emulators were initially designed as Megadrive/Genesis emulators, and so they include all three systems.

### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `mastersystem.videomode`, `mastersystem.ratio`, `mastersystem.smooth`, `mastersystem.shaders`, `mastersystem.pixel_perfect`, `mastersystem.decoration`, `mastersystem.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `mastersystem.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `mastersystem.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `mastersystem.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: GenesisPlusGX
A good all-around emulator. It can run Sega Genesis/Megadrive, Sega Master System, Sega/Mega CD and Game Gear games, but lacks 32X and Pico support. 

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
A lighter emulator which although not as accurate as GenesisPlusGX, can be run on much weaker hardware. This should be the default for devices such as the Raspberry Pi Zero and other sub-1GHz CPUs. Currently the only cross-architecture option for 32X and Pico games.

##### libretro: Picodrive configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **REDUCE SPRITE FLICKERING `global.picodrive_sprlim`** | Reduce sprite flickering when enabled\\ => Off `disabled`, On `enabled`. |
| **CROP OVERSCAN `global.picodrive_cropoverscan`** | Crops out video edge hidden under bezel of analog TV\\ => Off `disabled`, On `enabled`. |
| **CONTROLLER 1 TYPE `global.picodrive_controller1`** | Select 3 or 6 button controller\\ => Joypad 3 Button `3 button pad`, Joypad 6 Button `6 button pad`. |
| **CONTROLLER 2 TYPE `global.picodrive_controller2`** | Select 3 or 6 button controller\\ => Joypad 3 Button `3 button pad`, Joypad 6 Button `6 button pad`. |

##### Known game emulation issues with Picodrive
- **Gauntlet** - The HUD lags behind when the screen is scrolling.
- **Golden Axe Warrior** - The game uses a save system, which doesn't work and results in visual glitches in the save and load menus. It crashes when trying to load a game.
- **Phantasy Star** - The game uses a save system, which doesn't work and results in visual glitches in the save and load menus. It crashes when trying to load a game.
- **Wonder Boy in Monster Land** - Won't get past the title screen.
- **Ys - the vanished Omens** - The game uses a save system, which doesn't work and results in the start of the game being completely unplayable.

### CLK
[CLK aka Clock Signal](https://github.com/TomHarte/CLK) is a multi-system emulator that is focused on low-latency emulation, that can be used for Master System. CLK has been added to Batocera 42.

## Controls
The Master System featured multiple controllers such as the regular rectangular two-button controllers, the Light Phaser (a lightgun) and a paddle controller.

The original controller labelled the `[1]` button as `[START]`, so if a game requests you to press the `[START]` button it's actually referring to `[1]`. Some controllers also used Roman numerals instead (I, II).

Here are the default Sega Master System's controls shown on a [Batocera Retropad](:configure_a_controller):

You might recall that there wasn't a `[PAUSE]` button on the original Master System controller, and you'd be right. The `[PAUSE]` button is in reference to the button on the console itself.

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).