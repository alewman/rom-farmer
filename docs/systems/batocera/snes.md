# Super Nintendo Entertainment System

**Source:** https://wiki.batocera.org/systems:snes  
**Last fetched:** 2025-12-06 16:19:47

---

# Super Nintendo Entertainment System
The Super Nintendo Entertainment System (SNES), known as the Super Famicom in Japan, is a 16-bit fourth-generation home video-game console released by Nintendo on November 21, 1990 in Japan. Just like with the [NES](systems:nes), it was redesigned as the SNES and released one year later in August 23, 1991 in the US, retailing for $199.99. The redesign wasn't as drastic as as the original NES vs. Famicom, though the SNES version got a unique purple/pink color scheme for its controller's buttons, compared to the Super Famicom's red-yellow-blue-green color scheme. The PAL region uses the Super Famicom's console case and controller color scheme.

Batocera typically uses the Super Famicom's controller button layout when referring to generic controllers (A B X Y, Red Yellow Blue Green), however some may refer to them by their compass directions (East South North West,     respectively) to avoid [ambiguity with some other consoles](:configure_a_controller).

Emulation for the SNES is extensive and very mature. Batocera features two (three if you count the weak-hardware optimized PocketSNES) hand-picked emulators and some of their forks.

This system scrapes metadata for the `snes` group(s) and loads the `snes` set from the currently selected theme, if available.

Grouped with the snes group of systems.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Cores available:** [libretro: pocketsnes](#libretro:_pocketsnes), [libretro: snes9x_next](#libretro:_snes9x_next), [libretro: snes9x](#libretro:_snes9x), [libretro: bsnes](#libretro:_bsnes), [libretro: bsnes_hd](#libretro:_bsnes_hd)
- **Folder:** `/userdata/roms/snes`
- **Accepted ROM formats:** `.smc`, `.fig`, `.sfc`, `.gd3`, `.gd7`, `.dx2`, `.bsx`, `.swc`, `.zip`, `.7z`

## BIOS
No SNES emulator in Batocera needs the BIOS to run.

## ROMs
Place your SNES ROMs in `/userdata/roms/snes`. ROMs can be compressed into `zip` or `7z` files.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `snes.videomode`, `snes.ratio`, `snes.smooth`, `snes.shaders`, `snes.pixel_perfect`, `snes.decoration`, `snes.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator |
| **GRAPHICS BACKEND `snes.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `snes.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `snes.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: bsnes
bsnes was originally a SNES emulator started on October 14th, 2004, known for being more accurate to the hardware than other emulators at the time. Eventually the project started including emulation of so many other systems that the bsnes name started to become misleading, renaming the project to higan in 2012. Higan was forked in 2018 to revive the SNES-focused bsnes emulator from the project, more in line with how it was back in 2004. This standalone implementation has been 'libretro-ized' to work with RetroArch.

##### libretro: bsnes configuration
All core related settings must be configured in RetroArch's Quick Menu (Hotkey+). This may change in the future.

#### libretro: bsnes_hd
A fork of the 2018 bsnes that adds various enhancements including HD Mode 7 (F-Zero tracks rendered in 4k! Doesn't upscale the textures themselves, just increases the viewport resolution), Widescreen support (best with the aforementioned HD Mode 7, but can also work with traditional 2D games) and others.

##### libretro: bsnes_hd configuration
All core related settings must be configured in RetroArch's Quick Menu (Hotkey+). This may change in the future.

#### libretro: snes9x
Snes9x is a mature SNES emulator that evolved from being a speed-focused Win95 standalone to one of the most accurate and performant current SNES emulators available. This is the libretro port of it.

##### libretro: snes9x configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports |
| **REDUCE SPRITE FLICKERING (HACK, UNSTABLE) `snes.reduce_sprite_flicker`** | Enhancement. The SNES has a limit of 32 sprites per line, flickering between them if that limit is exceeded. This setting removes that limit. No games particularly used this quirk, and thus enabling it is usually safe (albeit less authentic). Some games will crash with this enabled.\\ => Off `disabled`, On `enabled`. |
| **REDUCE SLOWDOWN (HACK, UNSTABLE) `snes.reduce_slowdown`** | Enhancement. Overclocks the SNES's CPU to improve console-accurate lag. Very experimental. `light` for shorter loading times, `compatible` for improving game slowdown and `max` for demanding titles (Gradius 3, Super R-Type). Changing this can cause games to randomly crash!\\ => Off `disabled`, light `light`, compatible `compatible`, max `max`. |
| **SUPER-FX OVERCLOCKING `snes.overclock_superfx`** | Enhancement. Overclocks the SuperFX chip to improve console lag. Settings under 100% can improve performance on weak devices. Very experimental. Changing this can cause timing errors.\\ => 50% `50%`, 60% `60%`, 70% `70%`, 80% `80%`, 90% `90%`, 100% `100%`, 150% `150%`, 200% `200%`, 250% `250%`, 300% `300%`, 350% `350%`, 400% `400%`, 450% `450%`, 500% `500%`. |
| **HI-RES BLENDING `snes.hires_blend`** | Selects blending mode. Some games manipulated the blurriness of the interlaced analogue signal to create transparency effects (eg. Kirby's Dream Land, Jurassic Park). `merge` merges the colors of the pixels to create a cleaner looking transparency effect (though it technically means the transparent object is moved half a pixel, it's not really noticeable), `blur` uses bilinear filtering to achieve the same effect (but is more noticeable). Shaders can also simulate a similar effect.\\ => Off `disabled`, Merge `merge`, Blur `blur`. |
| **CONTROLLER 1 TYPE `snes.controller1_snes9x`** | Select what controller is connected to port 1.\\ => SNES Gamepad `1`, SNES Mouse `2`. |
| **CONTROLLER 2 TYPE `snes.controller2_snes9x`** | Same as above in addition to SNES Multitap, SuperScope, Konami Justifier or M.A.C.S. Rifle.\\ => SNES Gamepad `1`, SNES Mouse `2`, SNES Multitap `257`, Super Scope `260`, Konami Justifier `516`, M.A.C.S. Rifle `1028`. |
| **CONTROLLER 3 TYPE `snes.controller3_snes9x`** | The Justifier had a special pass-through port which allowed daisy-chaining an additional controller. This was intended to allow up to two players for just the Konami Justifier lightgun games, but can also be used to attach another ordinary SNES Gamepad.\\ => SNES Gamepad `1`, Konami Justifier (P2) `772`. |

Other settings must be configured in RetroArch's Quick Menu (Hotkey+).

#### libretro: snes9x_next
A fork of Snes9x that includes some extra speed hacks to run full speed on weaker hardware, as well as including an overclocking option to increase FPS in games like Star Fox. This is the libretro port of it.

##### libretro: snes9x_next configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports |
| **REDUCE SPRITE FLICKERING (HACK, UNSTABLE) `snes.reduce_sprite_flicker`** | Enhancement. The SNES has a limit of 32 sprites per line, flickering between them if that limit is exceeded. This setting removes that limit. No games particularly used this quirk, and thus enabling it is usually safe (albeit less authentic). Some games will crash with this enabled.\\ => Off `disabled`, On `enabled`. |
| **REDUCE SLOWDOWN (HACK, UNSTABLE) `snes.reduce_slowdown`** | Enhancement. Overclocks the SNES's CPU to improve console-accurate lag. Very experimental. `light` for shorter loading times, `compatible` for improving game slowdown and `max` for demanding titles (Gradius 3, Super R-Type). Changing this can cause games to randomly crash!\\ => Off `disabled`, light `light`, compatible `compatible`, max `max`. |
| **SUPER-FX OVERCLOCKING `snes.overclock_superfx`** | Enhancement. Overclocks the SuperFX chip to improve console lag. Settings under 100% can improve performance on weak devices. Very experimental. Changing this can cause timing errors.\\ => 50% `50%`, 60% `60%`, 70% `70%`, 80% `80%`, 90% `90%`, 100% `100%`, 150% `150%`, 200% `200%`, 250% `250%`, 300% `300%`, 350% `350%`, 400% `400%`, 450% `450%`, 500% `500%`. |
| **CONTROLLER 1 TYPE `snes.controller1_snes9x`** | Select what controller is connected to port 1.\\ => SNES Gamepad `1`, SNES Mouse `2`. |
| **CONTROLLER 2 TYPE `snes.controller2_snes9x`** | Same as above in addition to SNES Multitap, SuperScope, Konami Justifier(s) or M.A.C.S. Rifle.\\ => SNES Gamepad `1`, SNES Mouse `2`, SNES Multitap `257`, Super Scope `260`, Konami Justifier `516`, Dual Konami Justifiers `772`. |

Other settings must be configured in RetroArch's Quick Menu (Hotkey+).

#### libretro: pocketsnes
Also known as Snes9x 2002, Pocket SNES is a lightweight but inaccurate libretro core available only on weaker systems. Notable for the standalone version running (albeit poorly) on the [GBA](systems:gba) of all things. You can run this emulator in the GBA emulators!

##### libretro: pocketsnes configuration
FIXME

## SNES MSU-1
SNES MSU-1 has its own page: [systems:snes-msu1](systems:snes-msu1)

## Satellaview
Satellaview has its own page: [systems:satellaview](systems:satellaview)

## Controls
Here are the Super Nintendo Entertainment System's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).