# MAME

**Source:** https://wiki.batocera.org/systems:mame  
**Last fetched:** 2025-12-06 16:19:13

---

# MAME
[MAME](https:*www.mamedev.org/), the Multiple Arcade Machine Emulator, is a multi-purpose emulation framework which facilitates the emulation of vintage hardware and software. Originally targeting vintage arcade machines, MAME has since absorbed the sister-project [MESS](http:*mess.redump.net/start) (Multi Emulator Super System) to support a wide variety of vintage computers, video game consoles and calculators as well.

It was first released in 1997. In Italy!

MAME focuses on accuracy, even if it's at the cost of performance. If on low-end hardware, consider using older (more innaccurate) versions of MAME, or specialized emulators for such games instead.

MAME games scrapes metadata for the "arcade" group(s) and loads the `mame` set from the currently selected theme, if available.

MAME doesn't use an individual "core" for each system like RetroArch does, instead the ROM itself usually contains the necessary information to accurately emulate it, thus making it specific to the version of MAME it was made for. It is highly recommended to read the [generic arcade guide](:arcade) first to get familiar with arcade machine emulation.

### Quick reference
- **Accepted ROM formats:** `.zip`, `.7z`
- **Folder:** `/userdata/roms/mame`

| Emulators | Sample path | Artwork path |
| [libretro: imame4all](#libretro:_imame4all) | FIXME | FIXME |
| [libretro: mame078plus](#libretro:_mame078plus) | `/userdata/bios/mame2003plus/samples` | `/userdata/bios/mame2003plus/artwork` |
| [libretro: mame0139](#libretro:_mame0139) | `/userdata/bios/mame2010/samples` | `/userdata/bios/mame2010/artwork` |
| [libretro: mame](#libretro:_mame) | `/userdata/bios/mame/samples` | `/userdata/bios/mame/artwork` |
| [mame](#mame1) | `/userdata/bios/mame/samples` | `/userdata/bios/mame/artwork` |

## BIOS
Based on the [romset type](:arcade#romsets) used, either none is required, ones are required for each game you need to play, or a single BIOS file is needed for a group of games.

### Samples
Some arcade game machines featured additional storage that allowed for uncompressed audio to be utilized. These are referred to as "samples". Some machines had a backup synthesized track if the samples weren't present, others had none.

For MAME2003plus (mame078plus), if your game has the appropriate samples, place them in `/userdata/bios/mame2003/samples` folder. Samples can be for one specific game, or be applicable to multiple versions of the game.

## ROMs
Place your MAME ROMs in `/userdata/roms/mame`. If you'd like to, you could put ROMs intended for different versions of MAME into subfolders in this folder. For instance, you could put MAME2003-plus ROMs into the `/userdata/roms/mame/mame2003plus`. The latest versions of which ROMset to use can be found on [the arcade guide](:arcade#romsets).

Each romset is specific to the version of MAME being used:
- 0.37b5 ROMset for the [libretro: imame4all](#libretro:_imame4all) version
- 0.78plus ROMset for the [libretro: mame078plus](#libretro:_mame078plus) version
- 0.139 ROMset for the [libretro: mame0139](#libretro:_mame0139) version
- [Latest ROMset](:arcade#romsets) at the release of stable for the [libretro: mame](#libretro:_mame)/[mame](#mame1) versions

For MESS supported systems, each system has its own folder to use. Putting games designed for the MESS system inside of the `mame/` folder will not work.

## Emulators
### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: imame4all
iMame4All is an old version of MAME that's fairly easy to run, even on hardware as weak as the RPi Zero. Many games, especially newer ones, have known issues with this version. Supports the least number of games.

The ROMset for this version may be referred to as "0.37b5".

##### libretro: imame4all configuration
#### libretro: mame078plus
Not to be confused with the regular [MAME2003](https://docs.libretro.com/library/mame_2003/).

Internally using the name "mame078plus", [MAME2003plus](https://docs.libretro.com/library/mame2003_plus/) is an old version of MAME that became the "golden standard" for a while. A mixture of being easy to run while supporting the most hardware. Many ROMs, especially newer systems, have known issues with this version.

The "plus" version has had recent developments that don't break compatibility backported from newer versions of MAME. For this reason, regular MAME2003 ROMs may not work in this version.

The ROMset for this version may be referred to as "078plus".

##### libretro: mame078plus configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **CONTROL MAPPING `global.mame2003-plus_analog`** | Choose from Analog or Digital controller\\ => Analog `analog`, Digital `digital`. |
| **FRAMESKIP `global.mame2003-plus_frameskip`** | Skip frames to improve performance (smoothness)\\ => Off `0`, 1 `1`, 2 `2`, 3 `3`, 4 `4`, 5 `5`. |
| **INPUT INTERFACE `global.mame2003-plus_input_interface`** | Use input directly sends by keyboard to the core\\ => Retropad `retropad`, Keyboard `keyboard`, Simultaneous `simultaneous`. |
| **TATE MODE `global.mame2003-plus_tate_mode`** | Rotating display to vertical mode rendering\\ => Off `disabled`, On `enabled`. |
| **NEOGEO MODE `global.mame2003-plus_neogeo_bios`** | Manually specify your choice of Neo Geo BIOS\\ => Console AES World `asia-aes`, Arcade MVS Europe `euro`, Arcade MVS USA `us`, Arcade MVS Japan `japan`, Arcade Universe BIOS 4.0 (Cheats) `unibios40`, Arcade Universe BIOS 3.3 (Cheats) `unibios33`. |

Additional options can be accessed via RetroArch's Quick Menu (`[HOTKEY]` +  while in-game). Its dip switch settings can be accessed by pushing in `[L3]` in-game, navigate with the D-pad and accept with the  button. Push in `[L3]` again to exit the menu.

#### libretro: mame0139
Internally using the name "mame0139", [MAME 2010](https://docs.libretro.com/library/mame_2010/) is an old version of MAME that's a halfway point of being fast while still having a large library. It should not be used on the weaker SBCs such as Raspberry Pi. **This core was removed in v41.**

The ROMset for this version may be referred to as "0.139".

##### libretro: mame0139 configuration
There is no configuration for this core under ES. All of its options can be altered via RetroArch's Quick Menu (`[HOTKEY]` +  while in-game). Its dip switch settings can be accessed by pushing in `[R3]` in-game, navigate with the D-pad and accept with the  button. Push in `[R3]` again to exit the menu.

`[R2]` by default is assigned to the virtual turbo button. It is not used by games.

#### libretro: mame
The latest version of MAME at the time of stable's release. Check out the [table on the arcade guide](:arcade#arcade_emulation_on_batocera) for the current version.

##### libretro: mame configuration
| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **CPU OVERCLOCK `global.mame_cpu_overclock`** | Minimize in-game slowdowns of some games\\ => default `default`, 30 `30`, 35 `35`, 40 `40`, 45 `45`, 50 `50`, 55 `55`, 60 `60`, 65 `65`, 70 `70`, 75 `75`, 80 `80`, 85 `85`, 90 `90`, 95 `95`, 100 `100`, 105 `105`, 110 `110`, 115 `115`, 120 `120`, 125 `125`, 130 `130`, 135 `135`, 140 `140`, 145 `145`, 150 `150`. |
| **VIDEO RESOLUTION `global.mame_altres`** | Increase the video resolution\\ => 640x480 `640x480`, 800x600 `800x600`, 960x720 `960x720`, 1024x768 `1024x768`, 1280x720 `1280x720`, 1600x800 `1600x800`, 1920x1080 `1920x1080`, 2560x1440 `2560x1440`, 3840x2160 `3840x2160`. |

Additional options can be accessed via RetroArch's Quick Menu (`[HOTKEY]` +  while in-game). Its dip switch settings can be accessed by pushing in `[L3]` + `[R3]` in-game, navigate with the D-pad and accept with the  button. Push in `[L3]` + `[R3]` again to exit the menu.

For Batocera v(FIXME) and higher, further adjustments can be made to the `/userdata/bios/mame/ini/mame.ini` file, or the game-specific adjustments in `/userdata/bios/mame/ini/GAMENAME.ini`.

For Batocera v(FIXME) and lower, further adjustments can be made to the `/userdata/bios/mame.ini` file.

##### libretro: mame custom parameters
For Batocera v42 and higher, you can customize the the parameters passed to libretro: mame. This is particularly useful when you emulate computer systems, such as Apple IIe, and want to load two disk images instead of booting from disk 1, and pause the game to load disk 2. To do so, create a `.cmd` file with the same name beside your first ROM file, and put customized parameters in it.

For example, the directory `/userdata/roms/apple2/Some Game (1985)/` has these files:

- `Some Game (disk 1).dsk`
- `Some Game (disk 2).dsk`
- `Some Game (disk 1).dsk.cmd`

And the content of `Some Game (disk 1).dsk.cmd` is:

```

apple2ee -gameio joy -flop1 "/userdata/roms/apple2/Some Game (1985)/Some Game (disk 1).dsk" -flop2 "/userdata/roms/apple2/Some Game (1985)/Some Game (disk 2).dsk" -rompath "/userdata/bios/" -ui_active -cfg_directory "/userdata/saves/mame/cfg/apple2ee" -inipath "/userdata/saves/mame/mame/ini"

```

When you launch disk 1 from the Apple IIe menu, Batocera will see that you have a `.cmd` file and use its parameters. In this example, disk 2 will be automatically loaded into floppy 2.

### MAME
[As above!](#mame)

If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http:*mess.redump.net/start).

Be sure to remember to update the ROMset when updating Batocera, as this version is bumped every stable version.

#### MAME configuration
Standardized features available to all MAME systems: `mame.videomode`, `mame.decoration`, `mame.padtokeyboard`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `mame.video`** | Choose your graphics rendering\\ => BGFX `bgfx`, Accel `accel`, OpenGL `opengl`. |
| **BGFX BACKEND `mame.bgfxbackend`** | Choose your graphics API\\ => MAME Detect `automatic`, OpenGL `opengl`, OpenGL ES `gles`, Vulkan `vulkan`. |
| **BGFX VIDEO FILTER `mame.bgfxshaders`** | Apply a particular visual effect\\ => Off `None`, Bilinear `default`, CRT Geom `crt-geom`, CRT Geom Deluxe `crt-geom-deluxe`, Super Eagle `eagle`, HLSL `hlsl`, HQ2X `hq2x`, HQ3X `hq3x`, HQ4X `hq4x`. |
| **CRT SWITCHRES `mame.switchres`** | CRT monitor SwitchRes support\\ => Off `0`, On `1`. |
| **TATE MODE `mame.rotation`** | Rotating display to vertical mode rendering\\ => Off `None`, Rotate 90 `autoror`, Rotate 270 `autorol`. |
| **ALT DPAD MODE `mame.altdpad`** | If the D-Pad does not work properly\\ => Off (Default) `0`, DS3 Orientation `1`, X360 Orientation `2`. |

MAME offers a **[Menu](https://docs.mamedev.org/usingmame/ui.html)** in-game (push in `[L3]` + `[R3]` or press `[HOTKEY]` + ). This can be used to [manually adjust inputs](:arcade#mame_remap_configuration_files) or [ game settings](:arcade#configuration_menu_dip_switches_service_mode_systemgame_configuration_diagnostic_input). Alternatively, all of MAME's options can be edited by opening the `/userdata/system/configs/mame/mame.ini` file (you may need to create this file if it's not already present).

##### mame custom parameters
For Batocera v(FIXME) and higher, you can customize the the parameters passed to mame. This is particularly useful when you emulate computer systems, such as Apple IIe, and want to load two disk images instead of booting from disk 1, and pause the game to load disk 2. To do so, create a `.mamecmd` file with the same name beside your first ROM file, and put customized parameters in it.

For example, the directory `/userdata/roms/apple2/Some Game (1985)/` has these files:

- `Some Game (disk 1).dsk`
- `Some Game (disk 2).dsk`
- `Some Game (disk 1).dsk.mamecmd`

--> Example contents of "Some Game (disk 1).dsk.mamecmd" #
```

/usr/bin/mame/mame
-skip_gameinfo
-rompath
/userdata/roms/apple2/Some Game (1985);/userdata/bios/mame;/userdata/bios;/userdata/roms/mame
-bgfx_path
/usr/bin/mame/bgfx/
-fontpath
/usr/bin/mame/
-languagepath
/usr/bin/mame/language/
-pluginspath
/usr/bin/mame/plugins/;/userdata/saves/mame/plugins
-samplepath
/userdata/bios/mame/samples
-artpath
/var/run/mame_artwork/;/usr/bin/mame/artwork/;/userdata/bios/mame/artwork;/userdata/decorations
-cheat
-cheatpath
/userdata/cheats/mame
-verbose
-nvram_directory
/userdata/saves/mame/nvram
-cfg_directory
/userdata/system/configs/mame/apple2ee
-input_directory
/userdata/saves/mame/input
-state_directory
/userdata/saves/mame/state
-snapshot_directory
/userdata/screenshots
-diff_directory
/userdata/saves/mame/diff
-comment_directory
/userdata/saves/mame/comments
-homepath
/userdata/saves/mame/plugins
-ctrlrpath
/userdata/system/configs/mame/ctrlr
-inipath
/userdata/system/configs/mame;/userdata/system/configs/mame/ini
-crosshairpath
/userdata/bios/mame/artwork/crosshairs
-video
auto
-resolution
1024x768
-ui_active
-plugins
-plugin
hiscore
-dial_device
mouse
-trackball_device
mouse
-paddle_device
mouse
-positional_device
mouse
-mouse_device
mouse
-ui_mouse
-lightgun_device
mouse
-adstick_device
mouse
apple2ee
-gameio
joy
-flop1
/userdata/roms/apple2/Some Game (1985)/Some Game (disc 1).dsk
-flop2
/userdata/roms/apple2/Some Game (1985)/Some Game (disc 2).dsk

```
<--

When you launch disk 1 from the Apple IIe menu, Batocera will see that you have a `.mamecmd` file and use its parameters. Because of these final lines in the example,
```

-flop1
/userdata/roms/apple2/Some Game (1985)/Some Game (disc 1).dsk
-flop2
/userdata/roms/apple2/Some Game (1985)/Some Game (disc 2).dsk

```
disk 1 will be loaded into floppy 1, and disk 2 will be loaded into floppy 2.

Notice that the format of `Some Game (disk 1).dsk.mamecmd` for native MAME is very different from the custom file for libretro: mame above, in the following ways:

- The file extension must be `.mamecmd`
- Each line fully translates to exactly 1 parameter. There can be spaces within each line; quotation marks are unnecessary. Make sure you don't leave unwanted spaces at the end.
- The parameters MAME needs are very different from libretro: mame. MAME usually requires a lot more information.

## Sega Model 1

This infamous [Model 1 arcade board](https://www.system16.com/hardware.php?id=712) was a dramatic step-up above the competition in regards to 3D polygonal graphics. Thousands of vector-shaded polygons being drawn on-screen at once, with extremely responsive 60 FPS arcade feel (for some games).

Emulation for the Model 1 is sadly not that mature yet (such as slowdown, graphical inaccuracies and random crashes), however if you have a powerful enough machine you should be able to power through it. Model 1's ROMs are best played on [MAME 2010](#libretro:_mame0139) or newer.

There were only seven games (in reality, five with different variations) produced for this arcade board, most likely due to its prohibitive cost of development for each game:

| Game | MAME 2010 Filename | Additional information |
| Netmerc/Tecwar | N/A | On-rails first-person virtual-reality shooter played with a HMD and mounted gun which was never released. Considered the "holy grail" of Sega Model 1. This game cannot be emulated yet by any emulator in Batocera. |
| Star Wars Arcade | `swa.zip` | A tie-in game for the films of the era. Quite impressive for the time. |
| Virtua Fighter | '''' | Infamous 3D fighting game that would go on to get several ports onto home consoles. Renown for its weighty, realistic animations. |
| Virtua Formula | `vformula.zip` | An enhanced edition of Virtua Racer, featuring six player network play and formula one shaped rides. |
| Virtua Racer | `vr.zip` | Circuit racer leaning more towards an arcade experience than the simulation of other 3D racer games of the era. |
| Wing War | `wingwar.zip` | Arcade dogfighting game where two players take turns attacking and defending each other. |
| Wing War R360 | '''' | A special version with a 360 degree rotating cockpit. Extremely rare and expensive. |

## Controls
Here are the default MAME's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
MAME is a very complicated project and issues can crop up easily.

### None of my games are booting!
First check that the version of MAME you're attempting to run it with is the same as the ROMset you got it from. Mismatched versions aren't guaranteed to run, though sometimes if there were no differences made between MAME versions the game can run in both versions (though that's generally an exception, not the rule).

### I have an issue with a specific game
If you're having issues with a specific game, check the [MAMEdev FAQ for that game here.](https:*wiki.mamedev.org/index.php/FAQ:Games) For MESS systems specifically, you might find more information on [MESS's wiki](http:*mess.redump.net/start).

### Poor game performance
Arcade games tend to be more difficult to emulate than regular console games in general by their very nature.

With that said, newer versions of MAME emulate these arcade games more accurately than older versions. This generally means that real-world performance takes a dip as more accuracy to the emulation is added (although in some cases, it can dramatically improve performance, really it's on a game-by-game basis).

If your machine is struggling with running a particular game, try using an older set with its respective version of MAME, it may perform better. Just remember to make that special per-game setting to actually utilize the correct MAME version if deciding to go down this route!

### I can't open the MAME menu!
Sometimes the key needed to be pressed to access the in-game MAME menu is different depending on which version of MAME you are using. Typically, these keys can be:
- Pushing in `[L3]` or `[R3]`
- One of the shoulder buttons/triggers
- `[Tab]` on the keyboard

If you are specifically using a libretro: Mame core, you can manually activate the MAME menu by going to RetroArch's **Quick Menu** (`[HOTKEY]` + ) -> **Options** -> **System** -> **Display MAME Menu**. Once this option is activated, exit out of the Quick Menu and you will be greeted by MAME's menu. Repeat these actions to close the menu.

### I open the MAME menu too often!
Aforementioned issue, you might have the MAME key set to an in-game key as well. Either set it to another key or remap the MAME menu key.

### Further troubleshooting
Most questions are answered in the [generic arcade guide](:arcade).

For further troubleshooting, refer to the [generic support pages](:support).