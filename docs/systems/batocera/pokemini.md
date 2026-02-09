# Nintendo Pokémon Mini

**Source:** https://wiki.batocera.org/systems:pokemini  
**Last fetched:** 2025-12-06 16:19:35

---

# Nintendo Pokémon Mini
The Pokémon Mini is a handheld game console designed and manufactured by Nintendo and themed around the Pokémon media franchise. Released during the sixth generation of consoles, it is the smallest game system with interchangeable cartridges ever produced by Nintendo, weighing just under two and a half ounces (70 grams) and featuring a monochrome LCD of impressive 96×64 pixels. It was first released in North America on November 16, 2001. The systems were released in three colors: Wooper Blue, Chikorita Green, and Smoochum Purple. Over the course of its short life, ten games were released for the system, five of which were Japan-exclusive. Only four games were ever released in North America.

Features of the Pokémon mini include an internal real-time clock, an infrared port used to facilitate multiplayer gaming, a reed switch to detect shakes and a motor used to implement force feedback. It runs on a Seiko S1C88 8-bit CPU clocked at 4 MHz and 4 kB of memory, powered by a single AAA battery, with 60 hours of autonomy.

At this point in time, it's much more a collectable piece of Pokémon merchandise than it is a video game console.

This system scrapes metadata for the "pokemini" group and loads the `pokemini` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: pokemini](#libretro:_pokemini)
- **Folder:** `/userdata/roms/pokemini`
- **Accepted ROM formats:** `.min`, `.zip`, `.7z`

## BIOS
No Pokemon-Mini emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Pokemon-Mini ROMs in `/userdata/roms/pokemini`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `pokemini.videomode`, `pokemini.ratio`, `pokemini.smooth`, `pokemini.shaders`, `pokemini.pixel_perfect`, `pokemini.decoration`, `pokemini.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `pokemini.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `pokemini.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `pokemini.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: pokemini
Batocera uses the standalone port [PokeMini](https:*github.com/libretro/PokeMini) PokeMini based on the [Portable Pokémon Mini Emulator](https:*sourceforge.net/projects/pokemini/).

##### libretro: pokemini configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **LCD FILTER `global.pokemini_lcdfilter`** | Produces a clean LCD effect\\ => Off `none`, On `dotmatrix`. |
| **LCD GHOSTING EFFECTS `global.pokemini_lcdmode`** | Simulate the LCD ghosting effect\\ => Off `3shades`, On `analog`. |

## Controls
Here are the default Pokemon-Mini's controls shown on a [Batocera Retropad](:configure_a_controller):

The default button mapping to the Pokémon Mini is 1-to-1 to the [Nintendo Game Boy](systems:gb).

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).