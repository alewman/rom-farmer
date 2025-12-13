# Nintendo Game Boy (2 Players)

**Source:** https://wiki.batocera.org/systems:gb2players  
**Last fetched:** 2025-12-06 16:19:01

---

# Nintendo Game Boy (2 Players)
The link cable for the Game Boy allows two people to play two-player games. The requirement is that both players insert the same Game Pak into their Game Boy, and the Game Pak must feature a two-player mode (the packaging of these games is marked with the appropriate symbol). The link cable is connected to the left side of Game Boy through the sockets especially provided for it.

This system scrapes metadata for the "gb" group(s) and loads the `gb2players` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: TGBDual](#libretro:_tgbdual)
- **Folder:** `/userdata/roms/gb2players`
- **Accepted ROM formats:** `.gb`, `.gb2`, `.gbc2`, `.zip`, `.7z`

## BIOS
No Game Boy (2 players) emulator in Batocera needs a BIOS file to run.

## ROMs

Check the [list of multiplayer Game Boy games](wp>List_of_multiplayer_Game_Boy_games) to find compatible games.

ROMs can ordinarily be put into the `roms/gb2players/` folder. This will use a single ROM for both players in the linked game instances (Player 1's saves are stored in `saves/gb2player`). Player 2 will use a temporary blank save file that is removed when the session ends. Great for PVP games that don't rely on user save files such as Tetris or Ikari no Yousai.

This is the only available way to use GB2Player on Batocera **v31** and lower.

You can copy over your save file from `saves/gb/` to `saves/gb2player/` to continue from where you left off in single player! Alternatively, you can turn on **[SYNC SAVE FILES](#save_syncing)** to do this automatically.

If instead you'd like to use two *different* ROMs, read [the section on it below](#using_two_different_ROMs).

### Using two different ROMs
Alternative title: **POKEMON, YEAH! POKEMON TIME CAPSULE! POKEMON TRADING! POKEMON BATTLING! AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA POKEMON!!!**

In Batocera **v32** and higher, it is possible to use two different ROMs instead.

  - Copy your Game Boy/Game Boy Color ROMs to their respective solo ROM directory, ie. `roms/gb` and `roms/gbc` respectively. For example: ```

roms/
├─ gb/
│  └─ Pokemon Yellow.zip
└─ gbc/
   └─ Pokemon Crystal.zip

```
  - Create a new text file named `<game 1 title> and <game 2 title>.gb2` containing the filenames of the games you intend to link play with prepended with `gb:` or `gbc:` depending on which folder they're stored in. For example: ```

gb:Pokemon Yellow.zip
gbc:Pokemon Crystal.zip

```
Class A (Dual Mode) Game Boy Color games can be played on the Game Boy (obviously without color); these were typically indicated by having a black cartridge to differentiate them from regular Game Boy games. Class B Game Boy Color games can't be played on the original Game Boy. Such games typically feature the disclaimers like "Only for Game Boy Color".

**Libretro/TGB Dual doesn't care**, and will run either game with its appropriate system. Check first before attempting this, Game Boy Color games will default to using the [Game Boy Color mode of the emulator](systems:gbc2players)!

You can check out which games are class A on [Wikipedia's list of Game Boy Color games](wp>List_of_Game_Boy_Color_games).

  - Save this text file to the `roms/gb2player/` directory. For example: ```

roms/
├─ gb/
│  └─ Pokemon Yellow.zip
├─ gbc/
│  └─ Pokemon Crystal.zip
└─ gb2players/
   └─ Pokemon Yellow and Pokemon Crystal.gb2

```
  - Update your game list and now your game will appear in the GB2Player system!

By default, the save files are grabbed from `saves/gb2players/<game name for player 1>.srm` and `saves/gb2players/<game name for player 2>.srm` for the different games respectively. This can be used for a quick and dirty way to say trade Pokemon between generations.

But what if you wanted this to all be *[automated](#save_syncing)*?

### Save syncing
In Batocera **v32** and higher, it is possible to use two different ROMs from their single-player Game Boy and/or Game Boy Color systems with their respective single-player save file locations instead. This utilizes Python scripts to automate the copying/overwriting process between `saves/gb2players/` and `saves/gb` and/or `saves/gbc`.

You should create a backup of your GB2Player save files before attempting this, as they will otherwise be overwritten.

  - Set up your unique ROMs as [detailed above](#using_two_different_roms).
  - On the GB2Player game list, press `[SELECT]` to bring up the system-specific options and navigate to **ADVANCED SYSTEM OPTIONS**.
  - Scroll down to **SYNC SAVE FILES** and set this to "ON".

When launching a game through the GB2Player system, the SRM save files for both the ROMs will be temporarily copied from their respective `saves/gb/` and/or `saves/gbc/` folder(s) to `saves/gb2player/` (overwriting any files currently there). Upon exiting the game, the saves will be copied back from `saves/gb2player` to their respective `saves/gb/` and/or `saves/gbc/` folder(s).

Save states are not copied, only SRM native save files.

There is currently no automated save file syncing via Netplay. You could use an external method to sync up the save files and do this, however.

### Flowchart of save file handling
In case any of that was confusing here's a professional grade flowchart visualizing what happens based on what configuration/source ROMs are used:

If you use a .gb2 playlist that calls the same ROM twice, the file that's ultimately saved will be from Player 2!

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `gb2players.videomode`, `gb2players.ratio`, `gb2players.smooth`, `gb2players.shaders`, `gb2players.pixel_perfect`, `gb2players.decoration`, `gb2players.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `gb2players.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `gb2players.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `gb2players.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: TGBDual =
TGB Dual is an open source (GPLv2) GB/GBC emulator with game link cable support.

We use the latest [Libretro](https:*github.com/libretro/tgbdual-libretro) core. See the [official documentation](https:*docs.libretro.com/library/tgb_dual/) for more information.

##### libretro: TGBDual configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **SYNC SAVE FILES `global.sync_saves`** | Sync 2 player saves with single player versions (default is off)\\ => On `1`, Off `0`. |

## Controls
Here are the default Game Boy (2 players)'s controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).