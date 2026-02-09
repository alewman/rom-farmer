# Atari 2600

**Source:** https://wiki.batocera.org/systems:atari2600  
**Last fetched:** 2025-12-06 16:18:40

---

# Atari 2600
The Atari 2600 (originally branded as the Atari VCS) is a second-generation home videogame console developed by Atari. It was released in September, 1977 and retailed for $189.95 USD (adjusted for inflation: $811.23 in 2020).

Before this venture, Atari was more well-known for the [arcade](:arcade) games they made. Wanting to expand their horizons, the company invested in the creation of a efficiently manufactured home console: the Atari VCS. It released with a swell of games ported from the arcade, allowing many people to play these games from the comfort of their home for the first time (albeit, with certain downgrades in graphics/sound in the porting process). It was a huge success, leading to the founding of multiple third-party developers.

Due to a combination of poor management decisions, pressure from competition and crushing development deadlines, the quality of games released on the system started to decline. This culminated in being largely responsible for the [NA videogame crash of '83](https://en.wikipedia.org/wiki/Video_game_crash_of_1983). Infamously, this lead to the burial of hundreds of thousands of unsold Pac-Man and E.T. the Extra-Terrestrial game cartridges somewhere in Alamogordo, New Mexico.

No other console can claim to be as influential as that.

If you'd like to learn more about the Atari 2600's history, Stella's user guide has a [pretty good summary](https://stella-emu.github.io/docs/index.html#History) of it.

This system scrapes metadata for the "atari2600" group and loads the `atari2600` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Cores available:** [libretro: Stella](#libretro:_stella), [libretro: Stella2014](#libretro:_stella2014)
- **Folder:** `/userdata/roms/atari2600`
- **Accepted ROM formats:** `.a26`, `.bin`, `.zip`, `.7z`

## BIOS
No Atari 2600 emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Atari 2600 ROMs in `/userdata/roms/atari2600`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `atari2600.videomode`, `atari2600.ratio`, `atari2600.smooth`, `atari2600.shaders`, `atari2600.pixel_perfect`, `atari2600.decoration`, `atari2600.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `atari2600.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `atari2600.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `atari2600.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: Stella
[Stella](https:*stella-emu.github.io/) is an [open-source](https:*github.com/stella-emu/stella), multi-platform Atari 2600 emulator. This is the [libretro port](https://github.com/libretro/stella-libretro) of that emulator.

Batocera uses the latest version of Stella available when built.

#### libretro: Stella2014
An older version of the libretro Stella core that runs significantly faster at the cost of significantly lower accuracy. Useful for weak SBCs that struggle with certain Atari 2600 games.

## Controls
Here are the default Atari 2600's controls shown on a [Batocera Retropad](:configure_a_controller):

Left and right difficulty switches have 2 positions: `A` for `Advanced` and `B` for `Beginner`. On Space Invaders for example, `A` will give a larger (more vulnerable) player ship.

Libretro's controller mapping:

## Troubleshooting
### I have X problem with Y game
A lot of the time, this is actually a part of the game itself. There was a reason this caused a videogame crash, after all.

But if you're certain it's an issue with the *emulator* or the game is behaving different than it did from the original console, check out the [libretro documentation](https://docs.libretro.com/library/stella/) on it.

You can also check out Stella's [FAQ](https://stella-emu.github.io/faq.html), although most points don't actually apply to the libretro core.

### I don't remember my games being this choppy!
The Atari 2600 was neat in the sense that it didn't actually have a consistent video refresh rate. It was literally up to the dev to keep track of accurate timing to maintain a steady video signal. More advanced devs took advantage of this and manipulated the timings for game-performance or some special on-screen trick.

On a CRT that displays frames as its fed them, this didn't matter all too much. But on modern LCD displays that have fixed refresh rates, this may result in frames being displayed for longer/shorter than they would have on the original console. The effect of this is reduced the higher a refresh rate display you use, but never truly goes away.

If willing, you could set up a real CRT and allow the core to run without a frame limiter, but that's obviously not the ideal nor practical solution. An alternative would be to use a display that supports variable refresh rate and activate that from within RetroArch's settings, allowing RetroArch to display frames whenever it wants.

### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).