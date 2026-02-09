# Triforce

**Source:** https://wiki.batocera.org/systems:triforce  
**Last fetched:** 2025-12-06 16:19:54

---

# Triforce
The [Triforce](https:*wiki.dolphin-emu.org/index.php?title=Triforce) is a arcade developed by a collaboration between Namco, Sega, Nintendo. Its first games appeared in 2002. Added in Batocera **v34** for only *x86_64//.

The name "Triforce" was used to signify the three separate companies working together to produce the board. Nintendo provided the hardware's motherboard (very similar to the [GameCube](systems:gamecube)), Sega provided one of the formats used to store the game data on (GD-ROMs, the same disc format used by the [Dreamcast](systems:dreamcast)) and all three would help with developing the software.

Since the Triforce system uses much of the same hardware as the GameCube, Dolphin is capable of emulating the system. However, this was only supported by Dolphin's "Triforce" branch, which hasn't been updated in eight years, and likely is never to be integrated into the main branch in the state that it's in. The main Dolphin branch just doesn't support Triforce games as of writing (hence why its wiki says all games are at 1 star compatibility).

Dolphin Triforce's integration into Batocera is still under development, some things won't work as smoothly as they do for regular Dolphin for instance. Notably, most games have severe issues that render them unplayable. Fortunately, these are games that received superior home console ports.

This system scrapes metadata for the "triforce, arcade" group(s) and loads the `triforce` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [dolphin_triforce](#dolphin_triforce)
- **Folder:** `/userdata/roms/triforce`
- **Accepted ROM formats:** `.gcm`, `.iso`, `.gcz`, `.ciso`, `.wbfs`, `.elf`, `.dol`, `.m3u`

## BIOS
No Triforce emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Triforce ROMs in `/userdata/roms/triforce`.

Triforce emulation is... troubled, to say the least. A specific version of Dolphin is needed to be used, and certain games need certain workarounds in order to run. Luckily, Batocera automates that for the compatible games that it *can* run.

### F-Zero AX (GFZE01)
The arcade dump of the game is not currently possible to emulate successfully. However, since [the development of the two games was so closely tied, F-Zero GX contains most of the assets and menus for F-Zero AX](https://tcrf.net/F-Zero_GX/AX_Game_Mode). In other words, you can just use the GameCube's F-Zero GX image with certain flags set to get a broken trial mode of F-Zero AX.

| Acceptable images | MD5 sum |
| `F-Zero GX (USA).iso` | `81293462cf48c6a482c33e25c4097ac0` |

Although this technically works, the game itself is unplayable due to various bugs and glitches, the most hindering one being the camera flying outside of the track during gameplay. In addition, the memory card feature is malfunctional: settings from the current save file can be loaded, but it is impossible to save (and if it could, it would probably corrupt the data). Still, this is the most convenient way to at least see the demo playbacks, warning screens and menus of F-Zero AX.

If you truly want to experience F-Zero AX, it is recommended to do so on the current version of Dolphin (in the `gamecube` folder) using [these Gecko codes](https://tcrf.net/F-Zero_GX/AX_Game_Mode#Version_8).

Fortunately, most of this game's content is actually available in the home console port: F-Zero GX.

Batocera does not support running this game from its Triforce arcade dump. It is possible to set up the home port with certain flags using the regular [Dolphin emulator](systems:gamecube) with the proper [Gecko codes](https://tcrf.net/F-Zero_GX/AX_Game_Mode#Version_8).

### Mario Kart Arcade GP (GGPE01)
| Acceptable images | MD5 sum |
| `Mario Kart Arcade GP (USA).iso` | `4367f5ff113399f5c749d8336f371d7f` |

This game requires a savestate to be loaded in order to boot up. It is possible to manually download `GGPE01.s01` on another computer from https://drive.google.com/drive/folders/1skMJtfBgysmkneFWfsML75Aew60XEcOP and place it into your `/userdata/system/configs/dolphin-triforce/StateSaves` folder.

Boot up the game, and press `[HOTKEY]` + `[North]` (or `[F1]` on keyboard) to load the state. If desired, hold `[Shift]` and press the other `F` keys to use different slots (such as `[Shift]` + `[F2]`) in order to create new save states without overwriting the original one.

It is impossible to "insert" an existing Mario card, this functionality does not exist in the emulator. Selecting it will force the clock to fully countdown until you are automatically moved to the next screen. It is, however, still possible to create a new card, though obviously it will not create the physical item.

It is recommended to "buy" a new Mario card, to allow the game to "record" progression and unlock rewards. Without this, the game will not unlock new items as you play. However, since we can't actually use the physical magnetic strip card, it is impossible to use its native save system. Instead, save states must be used to maintain progression.

### Mario Kart Arcade GP 2 (GGPE02)
| Acceptable images | MD5 sum |
| `Mario Kart Arcade GP 2 (USA).iso` | `976b91bcb09fea5b1343f6658d07fcf9` |

It is impossible to use or buy Mario cards in this version of the game.

This game works as expected out of the box, excluding Mario card usage. Press Z to add a credit.

### Virtua Striker 2002 (GVSJ8P)
| Acceptable images | MD5 sum |
| ` Virtua Striker 2002 (Export).iso` | `eec44d152ccd630d68f5df85293e06b3` |

This game requires a savestate to be loaded in order to boot up. It is possible to manually download `GVSJ8P.s01` on another computer from https://drive.google.com/drive/folders/1skMJtfBgysmkneFWfsML75Aew60XEcOP and place it into your `/userdata/system/configs/dolphin-triforce/StateSaves` folder.

Boot up the game, and press `[HOTKEY]` + `[North]` (or `[F1]` on keyboard) to load the state. If desired, hold `[Shift]` and press the other `F` keys to use different slots (such as `[Shift]` + `[F2]`) in order to create new save states without overwriting the original one.

Although this game loads in fine, the only controls that work are Z (the credit button) and Start. The game itself is unplayable. Still, this is the most convenient way to at least see the introduction videos, warning screens and menus of Virtua Striker 2002.

### Virtua Striker 4

Todo: instructions

| Acceptable images | MD5 sum |
| | |

### Virtua Striker 4:Ver. 2006

Todo: instructions

| Acceptable images | MD5 sum |
| | |

### Incompatible games
The following Triforce games cannot be emulated at all:

- Gekitō Pro Yakyū
- All The Key of Avalon games

## Emulators
### Dolphin Triforce
#### Dolphin Triforce configuration
Standardized features available to all cores of this emulator: `triforce.videomode`, `triforce.decoration`, `triforce.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **RENDERING RESOLUTION `triforce.internal_resolution`** | Enhancement. Increase the rendering resolution. Makes 3D objects clearer.\\ => 1x native (640x528) `1`, 2x 720p (1280x1056) `2`, 3x 1080p (1920x1584) `3`, 4x 1440p (2560x2112) `4`, 5x (3200x2640) `5`, 6x 4K (3840x3168) `6`, 7x (4480x3696) `7`, 8x 5K (5120x4224) `8`. |
| **ASPECT RATIO `triforce.dolphin_aspect_ratio`** | The final output image, unrelated to the Wii's emulated NAND setting.\\ => Force 16:9 `1`, Force 4:3 `2`, Stretch to window `3`. |
| **UBERSHADERS `triforce.ubershaders`** | Improve performance with Ubershaders. Ubershaders take advantage of your GPU to avoid in-game stutters as it generates shaders for the first time; this can happen when a certain special effect shows on the screen or a new model is rendered. Hybrid ubershaders are preferred, it will use the GPU accelerated ubershader if available to avoid stutter, otherwise it will fall back to traditional shader generation. Exclusive ubershaders will only use ubershaders, only activate this option if you have an extremely powerful GPU. Normally there is no downside to activating ubershaders, however it does increase the minimum requirements out of your GPU to run. On especially weak hardware, such as SBCs, ubershaders are disabled by default. They can still be manually turned on, but you may encounter more stutter if on an SBC. Skip draw is a hack that opts to take a different approach altogether: don't display the object in game if its shader hasn't compiled yet. Obviously, this can result in visual glitches, but may be the best option performance-wise if your hardware is extremely weak.; asynchronous is preferred, synchronous is more compatible.\\ => No Ubershaders `no_ubershader`, Exclusive Ubershaders `exclusive_ubershader`, Hybrid Ubershaders `hybrid_ubershader`, Skip Drawing `skip_draw`. |
| **PRE-CACHE SHADERS `triforce.wait_for_shaders`** | Compile shaders on next launch of game (one time). Reduces micro-freezes.\\ => Off (default) `0`, On `1`. |
| **PERFORMANCE HACKS `triforce.perf_hacks`** | Increase emulator performance, at the cost of accuracy/stability. Settings set to "True" with this option: Defer EFB copies to RAM `DeferEFBCopies`, Scaled EFB Copy `EFBScaledCopy`, EFB Copies `EFBToTextureEnable`, Skip Presenting Duplicate Frames `SkipDuplicateXFBs`, XFB copies `XFBToTextureEnable`, Force Texture Filtering `ForceFiltering`, Arbitrary Mipmap Detection `ArbitraryMipmapDetection`, Disable Copy Filter `DisableCopyFilter`, Force 24-Bit Color `ForceTrueColor`. Settings set to "False" with this option: Bounding Box `BBoxEnable`, Ignore Format Changes `EFBEmulateFormatChanges`.\\ => Off `0`, On `1`. |
| **USE PAD PROFILES `triforce.use_pad_profiles`** | Search for custom configured joystick profiles.\\ => Off `0`, On `1`. |
| **ANISOTROPIC FILTERING `triforce.anisotropic_filtering`** | Improves clarity of distant textures.\\ => Off `0`, 2x `1`, 4x `2`, 8x `3`, 16x `4`. |
| **DUAL CORE MODE `triforce.dual_core`** | Usually not much faster than single core mode. Decreases stability.\\ => Off `0`, On `1`. |
| **GPU SYNC `triforce.gpu_sync`** | Speed hack for dual core mode to fix some glitches.\\ => Off `0`, On `1`. |
| **ANTI-ALIASING `triforce.antialiasing`** | Enhancement. Smooth out jagged edges on 3D object polygons.\\ => Off `0`, 2x `2`, 4x `4`, 8x `8`. |
| **ANTI-ALIASING MODE `triforce.use_ssaa`** | Toggle MSAA/SSAA. Depends on anti-aliasing being enabled.\\ => MSAA (default) `0`, SSAA `1`. |
| **LOAD CUSTOM TEXTURES `triforce.hires_textures`** | \\ => Off `0`, On `1`. |
| **WIDESCREEN HACK (GLITCHY) `triforce.widescreen_hack`** | Enhancement. Only works with a 16/9 ratio and bezels disabled.\\ => Off `0`, On `1`. |
| **MEMORY MANAGEMENT UNIT `triforce.enable_mmu`** | Required by some games.\\ => Off `0`, On `1`. |
| **VSYNC `triforce.vsync`** | Fix screen tearing. CPU heavy.\\ => Off `0`, On `1`. |
| **RUMBLE `triforce.rumble`** | \\ => Off `0`, On `1`. |

Other settings can be configured from `dolphin-triforce-config` in the Applications menu (`[F1]` on the system list).

## Controls
Triforce games typically have the GameCube's Z button (defaults to `[SELECT]`) bound to the "extra credit" button, but some may opt to use the `[START]` button instead.

The GameCube's Y button is usually set to resetting the game. This button is unbound by default, but it is possible to set this manually, so just keep that in mind if creating your own mapping.

Dolphin Triforce's mapping can be configured [just like Dolphin's regular controller mapping](:remapping_controls_per_emulator#gamecube) using its config application.

Here are the default Triforce's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### I lost the game INI files/cheats/save states and need them back!
This is for if you've made modifications to or have otherwise broken the files in `system/configs/dolphin-triforce/GameSettings` and `system/configs/dolphin-triforce/StateSaves`, rendering the game unable to launch correctly.

Simply delete the files and Batocera will regenerate them next time a Triforce game is launched.

### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).