# EasyRPG

**Source:** https://wiki.batocera.org/systems:easyrpg  
**Last fetched:** 2025-12-06 16:18:54

---

# EasyRPG
EasyRPG is a free, open source engine to create RPG games, aiming to be also compatible with all RPG Maker 2000 and RPG Maker 2003 games.

RPG Maker 2000/2003 games tend to have mechanics and visuals similar to 16-bit JRPGs, though custom scripts can be made by the creators to modify how the game feels and looks.

For more information about EasyRPG itself, check out its [website](https://easyrpg.org/).

This system scrapes metadata for the "easyrpg" group(s) and loads the `easyrpg` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.easyrpg`, `.squashfs`, `.zip`
- **Folder:** `/userdata/roms/easyrpg`

| Emulators |
| [EasyRPG](#easyrpg) |
| [libretro: EasyRPG](#libretro:_easyrpg) |

## BIOS
No EasyRPG emulator in Batocera needs a BIOS file to run.

## Game files
Place your EasyRPG game files in `/userdata/roms/easyrpg`.

The EasyRPG engine supports RPG Maker 2000 and 2003 games, you have to put the game's entire folder inside, and add `.easyrpg` to its name the game folder is the one containing the `RPG_RT.ldb` file.

The games must be put inside `/userdata/roms/easyrpg` and respect some rules:

- The folder of the game's name must end with `.easyrpg`
- The folder of the game has to be an RPG Maker 2000, 2003, or EasyRPG game folder correctly structured((Sometimes, games will be distributed in a slightly different way, in which case, you will need to adapt it)).
  - The structure of RPG Maker 2000/2003 or EasyRPG games is mostly the same: a main folder, which will be called `game.easyrpg`, and inside it several sub-folders (including Title, Music, System, …), as well as a few `Map000x.lmu` files, an `RPG_RT.ldb` and `RPG_RT.lmt` (other files can also be there, typically an `RPG_RT.ini` and a `RPG_RT.exe` (This `.exe` file can be used to gather some data by EasyRPG, however it won't be executed)).

New to Batocera **v33**: ZIP file support!

### Advanced structure information
When opening a game folder, we see a similar structure from one game to another : 
- Several folders
  - **Backdrop** : containing the background images used during standard battles
  - **Battle** : containing battle animations
  - **CharSet** : containing overworld animations
  - **ChipSet** : containing the tilemaps used in the overworld
  - **FaceSet** : containing the images of the characters' faces
  - **GameOver** : containing the picture used as the Game Over screen
  - **Music** : containing the music files, in .mid (midi) format
  - **Panorama** : containing the background images used in the overworld
  - **Picture** : containing several pictures used by the game
  - **Sound** : containing the sound effects, in .wav format
  - **System** : containing the assets used to display the various menus and dialog boxes
  - **Title** : containing the image used at the title screen
- Several map files (Map000x.lmu)
- An executable `RPG_RT,exe`
- An `RPG_RT.ini` text file
- An `RPG_RT.ldb` file with an `RPG_RT.lmt` file
- Occasionally, Save files (`Save01.lsd` et `Save15.lsd`) can also be found here (by default on other systems, easyRPG will save the game in the game folder).

This structure can be slightly different from one game to another, however the `RPG_RT.ldb` and `RPG_RT.lmt` must be directly inside the `.easyrpg` folder.

Some games are distributed in a slightly different way (for exemple, VGPerson's translations will often have a folder containing two executables `StartFullscreen.exe` and `StartWindowed.exe`, as well as several folders including a `Data` one, this Data folder contains the structure we talked about before, which means it is the actual game folder).

### Game specific formats
Sometimes, games will have strange extensions to their filenames, while their format isn't directly exploitable, they can technically be converted to more common formats.

- `.lmu`, `.lmt`, `.ldb` and `.lsd`: can be converted to `.xml` files
- `.xyz`: can be converted to `.png`

Source: [the Tools page of EasyRPG](https://easyrpg.org/tools/)

## Emulators
### EasyRPG
#### EasyRPG configuration
Standardized features available to all cores of this emulator: `easyrpg.videomode`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **TEST PLAY `easyrpg.testplay`** | Enable the debug menu and the walk-through-walls button\\ => Off `0`, On `1`. |
| **GAME REGION (ENCODING) `easyrpg.encoding`** | Needed by some games to use special characters\\ => Autodetect (Recommended) `autodetect`, European (Western) `1252`, European (Cent/East) [W-1250] `1250`, Japanese [Shift-JIS] `932`, Cyrillic [Windows-1251] `1251`, Korean `949`, Chinese (Simplified) `936`, Chinese (Traditional) [Big5] `950`, Greek `1253`, Turkish `1254`, Baltic `1257`. |

### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `easyrpg.videomode`, `easyrpg.ratio`, `easyrpg.smooth`, `easyrpg.shaders`, `easyrpg.pixel_perfect`, `easyrpg.decoration`, `easyrpg.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `easyrpg.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `easyrpg.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `easyrpg.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: easyrpg
##### libretro: easyrpg configuration
## Test-play mode
One of the advanced game settings in EasyRPG is the Test-play mode, it basically lets the player access the debug features present in RPG Maker 2000 and 2003, originally meant to test the game more easily, those include a Walk through walls key that also disable random encounters when held down, a way to access a save menu anywhere, and a debug menu that is quite powerful, those can be used for example to cheat.

 The `Save` option opens the save menu, while the `Load` options opens the load menu, they cannot be accessed during a standard battle.

The `Switches` options let's you modify the state of various booleans used in the game, while the `Variables` menu is used to alter the values of number variables.

The entry between `Variables` and `Items` is used to set the amount of money you have, its name depends on how the game calls it internally.

The `Items` option lets you adjust your inventory fully.

The `Battle` menu can trigger a battle, assuming the game uses the basic battle system, otherwise you might encounter some issues trying to use it((Touhou mother, for exemple, uses a completely custom battle system, which isn't compatible with this option)).

`Map` is used to teleport anywhere in the game, assuming you know how the game refers to the maps internally((Sometimes, using it without knowing how the game is done might trigger some events out of order)).

`Full Heal` will heal the entire party.

`Call Event` can be used to trigger various events occurring in game.

## Controls
EasyRPG only uses a few controls, they are as follow : 

- **A** : Accept/Talk (may be referred as `Enter` in the games)
- **B** : Go back/Open Menu (may be referred as `Escape` in the games)
- **L** : Shift (may be referred as `Shift` in the games, some games use it for various purposes at times; in `Test-play` it is also used to skip the text "typewriting" effect)
- **D-Pad/Left stick** : Move
- **R** : Walk through walls + Disable random encounters (Only used in `Test-play` mode)

The following hotkey combos work as well in the standalone version : 

- **Hotkey+Start** : Quit the game
- **Hotkey+A** : Restart the game (must be held down 2 seconds)
- **Hotkey+L** : Take a screenshot
- **Hotkey+Dpad right** : Fast-Forward
- **Hotkey+B** : Open debug menu (Only used in `Test-play` mode((The debug menu can also be accessed in the pause menu when `Test-play` is enabled)))
- **Hotkey+Y** : Open save menu (Only used in `Test-play` mode)

Here are the default EasyRPG's controls shown on a [Batocera Retropad](:configure_a_controller):

## Known Issues
### Encoding and filenames
Some games may have special characters in their filenames, or use special characters in-game, when this happens, it may be unable to find said files or display said characters if you didn't adjust the advanced game setting **Encoding**

Sometimes unzipping the game wrongly can also result in special characters in filenames being incorrect [as explained here](https://wiki.easyrpg.org/unzip-games), when it happens, the asset won't be loaded properly and a warning message will be displayed on top of EasyRPG, The best way is to unzip the game correctly (by using a program able to do so, like unar) and precise the required encoding afterwards.

The page [about EasyRPG's special features](https://wiki.easyrpg.org/user/player/special-features) lists the encoding settings and their purposes:

<csv>
"Option name","Description"
"Auto","Uses the RPG_RT.ini file information (works for most games by default since they don't use special characters often)"
"Western European","English games or games from most western Europe and America countries"
"Windows-1251","Cyrillic games (full Cyrillic support for Russian and other languages)"
"Windows-1250","Central European games (mostly Latin Extended A glyphs)"
"Shift-JIS","Japanese games (with Hiragana, Katakana or Kanji)"
"Big5","Traditional Chinese games (Taiwan, Hong Kong)"
</csv>

You can alternatively edit the RPG_RT.ini file to put the encoding as an EasyRPG parameter, so for exemple, in that file:

```

[RPG_RT]
GameTitle=Ib
MapEditMode=2
MapEditZoom=0
KnownVersion=281479271809025

[EasyRPG]
Encoding=1252

```

The [EasyRPG] part and all that is below has been manually added to let EasyRPG know how to launch the game.

Will force the 1252 encoding for the game if the option is not set in Batocera, which corresponds to Western European: 
- **Western European** : 1252
- **Windows-1251** : 1251
- **Windows-1250** : 1250
- **Shift-JIS** : 932
- **Big5** : 950

### Compatibility
There are a few known compatibility issues with EasyRPG at the time.

- Videos files cannot be played inside EasyRPG, multiple games are reliant on this (**Ib** for example)

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).