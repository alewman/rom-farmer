# 3DO Interactive Multiplayer

**Source:** https://wiki.batocera.org/systems:3do  
**Last fetched:** 2025-12-06 16:18:30

---

# 3DO Interactive Multiplayer
The 3DO Interactive Multiplayer is a fifth-generation home video game console released by the [3DO Company](https://en.wikipedia.org/wiki/The_3DO_Company) on October 4, 1993. It retailed for $699.99. It had a RISC CPU ARM60 at 12.5 MHz with 2MB of RAM and 1MB of VRAM. Its hardware was extremely sophisticated for its time, warranting its high price, but this would be a part of the reason for its market failure.

The 3DO company was conceived by Trip Hawkins, Electronic Arts founder. The console itself was not manufactured by the 3DO company itself, but the company created a set of specifications to be followed by other manufacturers, notable examples being Panasonic, Sanyo and Goldstar (later known as LG Electronics).

As time went on, the 3DO's competitors (the [PlayStation](systems:psx) and the [Saturn](systems:saturn)) would surpass it in popularity.

This system scrapes metadata for the `3do` group and loads the `3do` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: opera](#libretro:_opera)
- **Folder:** `/userdata/roms/3do`
- **Accepted ROM formats:** `.iso`, `.chd`, `.cue`

## BIOS
| MD5 checksum | Share file path | Description |
| `f47264dd47fe30f73ab3c010015c155b` | `bios/panafz1.bin` | Panasonic FZ-1 |
| `51f2f43ae2f3508a14d9f56597e2d3ce` | `bios/panafz10.bin` | Panasonic FZ-10 |
| `8639fd5e549bd6238cfee79e3e749114` | `bios/goldstar.bin` | Goldstar GDO-101M |

## ROMs
Place your 3DO ROMs in `/userdata/roms/3do/`. 

The recommended format to save space maintaining full compatiblity is [CHD](:disk_image_compression#chd).

### Multi-disc games
[libretro: Opera](#libretro: Opera) supports multi-disc games, however it does not support loading them from M3U playlists. In past Batocera versions, this required manually renaming the save file to the new disc in order to continue your game.

From Batocera **v34**, simply enable the **NVRAM STORAGE** option from the advanced system settings (`[SELECT]` in the game list) for the multi-disc game to allow it to automatically use the same save file. Do note that this shared storage has the real-world limitations of the 3DO's drive space.

## Emulators
### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: Opera
Opera is an open-source, low-level emulator for the 3DO Game Console. Opera is a fork of 4DO, originally a port of 4DO, itself a fork of FreeDO, to libretro. The fork/rename occurred due to the original 4DO project being dormant and to differentiate the project due to new development and focus.

We use the latest [libretro](https:*github.com/libretro/opera-libretro) core. See the [official documentation](https:*docs.libretro.com/library/opera/) for more information. Its compatibility list is on [the original 4DO wiki](http://wiki.fourdo.com/Compatibility_List).

##### libretro: Opera configuration
Standardized features for this core: `3do.rewind`, `3do.autosave`, `3do.netplay`, `3do.cheevos`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **VIDEO RESOLUTION `global.high_resolution`** | The default internal resolution is 320x240, but the output resolution is 640x480. This feature makes the system behave as if it has a 640x480 framebuffer. Does not affect 2D sprites.\\ => 320x240 `disabled`, 640x480 `enabled`. |
| **CPU OVERCLOCK `global.cpu_overclock`** | The 3DO used a 12.5MHz ARM60 CPU as its central processor. The emulator has implemented a CPU overclocking feature in the Opera core so that you can increase performance up to 2x (good for NFS). [Example video](https://www.youtube.com/watch?v=7bT2ecwKdHQ). Good for demanding games like NFS, but may not have an impact on all games. An overclock of 1.5x is recommended if using overclocking at all.\\ => 1.0x (12.50Mhz) `1.0x (12.50Mhz)`, 1.1x (13.75Mhz) `1.1x (13.75Mhz)`, 1.2x (15.00Mhz) `1.2x (15.00Mhz)`, 1.5x (18.75Mhz) `1.5x (18.75Mhz)`, 1.6x (20.00Mhz) `1.6x (20.00Mhz)`, 1.8x (22.50Mhz) `1.8x (22.50Mhz)`, 2.0x (25.00Mhz) `2.0x (25.00Mhz)`. |
| **ACTIVE INPUT DEVICES FIX `global.active_devices`** | There is a bug in which having more than 1 controller emulated causes the game not to respond to input. This allows working around the issue. Set it to 1 when playing alone, otherwise to the number of connected players/controllers.\\ => 1 `1`, 2 `2`, 3 `3`, 4 `4`, 5 `5`, 6 `6`, 7 `7`, 8 `8`. |
| **ADDITIONAL GAME FIXES `global.game_fixes_opera`** | Several game fixes and time hacks. Leave it to auto or configure it game specific.\\ => Off `disabled`, Alone in the Dark `timing_hack6`, Crash'n Burn `timing_hack1`, Dinopark Tycoon `timing_hack3`, Microcosm `timing_hack5`. |
| **NVRAM STORAGE `global.opera_nvram_storage`** | Enable shared saves for multi-disc games\\ => Shared `shared`, Per Game `per game`. |

## Controls
Here are the default 3DO Interactive Multiplayer's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).