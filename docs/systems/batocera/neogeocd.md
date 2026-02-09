# NEO•GEO CD

**Source:** https://wiki.batocera.org/systems:neogeocd  
**Last fetched:** 2025-12-06 16:19:25

---

# NEO•GEO CD
The NEO•GEO CD is a home console developed by SNK, designed to allow gamers to play their favorite arcade games from the comfort of their own home. It was released in 1994 and retailed for $399 USD. Its internals are similar to the cartridge-based [NEO•GEO AES](systems:neogeo), though the CD has a lot more RAM.

This system scrapes metadata for the "neogeocd" group and loads the `neogeocd` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Cores available:** [libretro: neocd](#libretro:_neocd), [libretro: fbneo](#libretro:_fbneo)
- **Folder:** `/userdata/roms/neogeocd`
- **Accepted ROM formats:** `.cue`, `.iso`, `.chd`

## BIOS
To function NeoCD need a BIOS from a Front Loading, Top Loading or CDZ machine. The BIOS files should be installed in the `/userdata/bios/neocd` folder. You need at least one from the following table. If several BIOSes are available, it will be possible to choose which to run in the advanced system settings.

### Batocera v34 and higher
| MD5 checksum                         | Share file path               | Description       |
| `8834880c33164ccbe6476b559f3e37de` | `bios/neocd/neocd_f.rom`    |                   |
| `043d76d5f0ef836500700c34faef774d` | `bios/neocd/neocd_sf.rom`   |                   |
| `de3cf45d227ad44645b22aa83b49f450` | `bios/neocd/neocd_t.rom`    |                   |
| `f6325a33c6d63ea4b9162a3fa8c32727` | `bios/neocd/neocd_st.rom`   |                   |
| `11526d58d4c524daef7d5d677dc6b004` | `bios/neocd/neocd_z.rom`    | CDZ               |
| `971ee8a36fb72da57aed01758f0a37f5` | `bios/neocd/neocd_sz.rom`   |                   |
| `5c2366f25ff92d71788468ca492ebeca` | `bios/neocd/front-sp1.bin`  |                   |
| `122aee210324c72e8a11116e6ef9c0d0` | `bios/neocd/top-sp1.bin`    |                   |
| `f39572af7584cb5b3f70ae8cc848aba2` | `bios/neocd/neocd.bin`      | CDZ MAME          |
| `08ca8b2dba6662e8024f9e789711c6fc` | `bios/neocd/uni-bioscd.rom` | CDZ Universal 3.3 |

### Batocera v33 and lower
| MD5 checksum                         | Share file path     | Description             |
| `c733b4b7bd30fa849874d96c591c8639` | `bios/neocdz.zip` | Neo Geo CDZ System BIOS |

## ROMs
Place your Neo-Geo CD ROMs in `/userdata/roms/neogeocd`.

It's recommended to use the latest MAME romset at the time of Batocera's last stable release.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `neogeocd.videomode`, `neogeocd.ratio`, `neogeocd.smooth`, `neogeocd.shaders`, `neogeocd.pixel_perfect`, `neogeocd.decoration`, `neogeocd.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `neogeocd.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `neogeocd.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `neogeocd.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: neocd
[Libretro NeoCD](https://github.com/libretro/neocd_libretro) is a contemporary NEO•GEO CD emulator. To quote its readme:

> NeoCD-Libretro is a complete rewrite of NeoCD from scratch in modern C++11. It is designed with accuracy and portability in mind rather than being all about speed like the the older versions.

##### libretro: neocd configuration
| ES setting name `batocera.conf_key`                  | Description => ES option `key_value`                                                                           |
| Settings that apply to all systems this core supports                                                                                                                    ||
| **CONSOLE REGION `global.neocd_region`**             | Change language of some games\\ => Japan `Japan`, USA `USA`, Europe `Europe`.                              |
| **BIOS SELECT `global.neocd_bios`**                  | CD Universe Bios not include cheats\\ => CDZ `CDZ`, CDZ (MAME) `CDZ (MAME)`, Universe 3.3 `Universe 3.3`.  |
| **PER-GAME SAVES `global.neocd_per_content_saves`**  | Use one save file per-game\\ => Off `False`, On `True`.                                                      |

#### libretro: fbneo

FBNeo can run a lot of things, can't it? Description needed.

##### libretro: fbneo configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **CPU CLOCK `global.fbneo-cpu-speed-adjust`** | Can fix native system slowdowns in some games\\ => 30% `30%`, 40% `40%`, 50% `50%`, 60% `60%`, 70% `70%`, 80% `80%`, 90% `90%`, 100% `100%`, 110% `110%`, 120% `120%`, 130% `130%`, 140% `140%`, 150% `150%`, 160% `160%`, 170% `170%`, 180% `180%`, 190% `190%`, 200% `200%`. |
| **FRAMESKIP `global.fbneo-frameskip`** | Skip frames to improve performance (smoothness)\\ => No skipping `0`, Skip rendering of 1 frames out of 2 `1`, Skip rendering of 2 frames out of 3 `2`, Skip rendering of 3 frames out of 4 `3`, Skip rendering of 4 frames out of 5 `4`. |
| **CROSSHAIR (LIGHTGUN) `global.fbneo-lightgun-hide-crosshair`** | Show crosshair if playing with a lightgun device\\ => Off `enabled`, On `disabled`. |
| Settings specific to neogeo ||
| **NEOGEO MODE `neogeo.fbneo-neogeo-mode-switch`** | Load appropriate Bios depending on your choice\\ => Console AES World `AES Asia`, Console AES Japan `AES Japan`, Arcade MVS Europe `MVS Asia/Europe`, Arcade MVS USA `MVS USA`, Arcade MVS Japan `MVS Japan`, Arcade Universe BIOS (Cheats) `Universe BIOS`. |
| **MEMORY CARD MODE `neogeo.fbneo-memcard-mode`** | Change the behavior for the memory card\\ => Off `disabled`, Shared `shared`, Per-game `per-game`. |

## Controls
The controller for the NEO•GEO CD had an interesting "D-pad" which was a small disc floating above a circular perimeter, with micro-switch activation allowing for precise control of inputs; a necessity for the fighting games featured on the console. It's truly something that needs to be physically felt to be understood.

Here are the default NEO•GEO CD's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).