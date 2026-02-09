# Wii U

**Source:** https://wiki.batocera.org/systems:wiiu  
**Last fetched:** 2025-12-06 16:20:02

---

# Wii U
The Wii U is an eighth-generation console released by Nintendo on November 18, 2012 at $349.99. It has a Tri-Core IBM PowerPC CPU at 1.24 GHz with 2GB of RAM. It has a AMD Radeon GPU. It is the first console by Nintendo to output to high definition (HD) resolutions, such as 720p and 1080p. It includes a tablet-like controller, known as the Wii U GamePad, to provide certain additional gameplay. Notably, it can play all Wii games as well as support the Wii Remote controllers for native Wii U games.

This system scrapes metadata for the "wiiu" group(s) and loads the `wiiu` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [Cemu](#cemu)
- **Folder:** `/userdata/roms/wiiu`
- **Accepted ROM formats:** `.wup`, `.wud`, `.wua`, `.rpx`, `.squashfs` , `.wux`*

*`.wux` removed in v37, but back in v38+
## BIOS
No Wii U emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Nintendo Wii U ROMs in `/userdata/roms/wiiu/`. 

You can use the following ROM formats:
- `wup`: an installer format for titles to be installed on the Wii U console - not recommended.
- `wud`: a single file, which is a direct physical game dump, this format requires an accurate `keys.txt` file.
- `wux`: single-file compressed versions of `.wud` dumps, this format requires an accurate `keys.txt` file.
- `wua`: single-file compressed file, it's a file that contains both base, update and dlcs game content. (Supported since Cemu version 1.27)
- `Loadiine`: a directory structure with multiple files and folders, usually shared as an archive. You must unpack the archive and place the containing folder in the ROMs directory. This format is a decrypted version of `.wud` dumps. Batocera will use the `[game].rpx` binary file in the `/code/` directory structure of the Loadiine unarchived ROM to launch the game.

How to [compress files to .wua](:disk_image_compression#wua) format.
### keys.txt
You need a text file named `keys.txt`. This file needs to go in the `/userdata/bios/cemu/` folder. If you have a pop-up window telling you "Error in keys.txt line XX", it might be because your `keys.txt` file is not correctly located in `/userdata/bios/cemu/`.

This `keys.txt` is a plain text file containing several lines, one for the common Wii U key, plus one for each game you want to support. `#` is used for comments. 

Google is your friend if you want a Wii U `keys.txt` pre-filled with many games. Check out the [Cemu wiki](https://wiki.cemu.info/wiki/Obtaining_Keys_for_Keys.txt) for more information.

### DLCs & Updates
Some games need an update to be playable via Cemu or maybe you want to install available DLCs for a game.

You can install them easily with `cemu-config`. First make sure that you connected an [external drive](:store_games_on_a_second_usb_sata_drive) or a [network share](:store_games_on_a_nas) with the installation files or copied them to the [Batocera share](:add_games_bios).

- select `File` -> `Install game update or DLC`
- select the `meta.xml` in the meta folder of the update or DLC
- wait for the installation process

The installed DLC and game version will be shown in the game list of the `cemu-config` application. The installation files are stored in `/userdata/saves/cemu/drive_c/cemu/usr/<titleid>`. Your original rom file or folder will never be touched.

## Emulators
### Cemu
[Cemu](http:*cemu.info/) is a free and open-source Wii U emulator created in October 2015. Though still under development, it is able to run the majority of commercial games smoothly, 15% of tested titles are perfect and 38% are, at least, playable which sums to 45% of total tested titles, with varying degrees of glitches for the imperfect ones. Check out the up-to-date official [compatibility list](http:*compat.cemu.info) for more information.

#### Cemu configuration
Standardized features available to all cores of this emulator: `wiiu.videomode`

| ES setting name `batocera.conf_key`                       | Description => ES option `key_value`                                                                                                                                    |
| Settings that apply to all cores of this emulator                                                                                                                                                                                      ||
| **GRAPHICS BACKEND `wiiu.gfxbackend`**                    | Choose your graphics rendering\\ => OpenGL `OpenGL`, Vulkan `Vulkan`.                                                                                                 |
| **ASYNC SHADER `wiiu.async`**                             | Speedup shader compilation (Vulkan only)\\ => Off `0`, On `1`.                                                                                                        |
| **RUMBLE `wiiu.rumble`**                                  | To use vibration on games with Rumble mode\\ => Off `0`, On `1`.                                                                                                      |
| **CONTROLLER COMBINATION `wiiu.controller_combination`**  | Use Pro Controller if the game asks for Shake\\ => GamePad + 4 Pro Controller `0`, GamePad + 4 Sideway Wiimote `1`, 5 Pro Controller `2`, 5 Sideway Wiimote `3`.  |
| **AUDIO CHANNELS `cemu_audio_channels`**                  | Choose the audio output type.\\ => Stereo (Default)`1`,Surround`2`                                                                                                    |
| **AUDIO OUTPUT `cemu_audio_config`**                      | Fix screen tearing.\\ => Set in Config - choose if no audio output`false`,Batocera sets first audio device (Default)`true`                                            |
| **VSYNC `cemu_vsync`**                                    | Fix screen tearing.\\ => Off (Default)`0`,Double buffering`1`, Triple buffering`2`                                                                                  |
| **UPSCALE FILTER `cemu_upscale`**                         | Choose upscaling method.\\ => Bilinear (Default)`0`, Bicubic`1`, Hermite`2`, Nearest Neighbour`3`                                                                 |
| **DOWNSCALE FILTER `cemu_downscale`**                     | Choose downscaling method.\\ => Bilinear (Default)`0`, Bicubic`1`, Hermite`2`, Nearest Neighbour`3`                                                               |
| **ASPECT RATIO `cemu_aspect`**                            | Change the output resolution ratio.\\ => Keep Aspect Ration (Default) `0`, Stretch `1`                                                                                |
| **ENABLE MOUSE `cemu_touchpad`**                          | Enable mouse input to simulate touchscreen.\\ => Disabled (Default) `false`, Enabled `true`                                                                           |
| **ENABLE PERFORMANCE OVERLAY `cemu_overlay`**             | Enable Cemu's performance overlay.\\ => Disabled (Default) `false`, Enabled `true`                                                                                    |
| **ENABLE NOTIFICATIONS `cemu_notifications`**             | Enable notifications of cache, controller events etc.\\ => Disabled (Default) `false`, Enabled `true`                                                                 |
| **ENABLE GAMEPAD VIEW `cemu_gamepad`**                    | Enable gamepad view for games that have interaction across two screens. Use Hotkey+R2 to switch screens.\\ => Disabled (Default) `false`, Enabled `true`              |

Cemu offers a lot of custom configuration options. You can set most of them within the `cemu-config` application which you can reach via the [Batocera applications menu](:emulationstation_overview#file_manager_and_applications_menu).

#### Graphic options
Cemu works best with Vulkan drivers if your GPU can support it. 

For most games **Community graphic packs** are available.

Unlike the name suggests these are not only graphic enhancements but also mods and patches that make the game more stable or playable. Most Wii U games run in 720p; the graphic packs allow to run games in 1080p or even in higher resolutions. They are highly recommended.

To download and use the community graphic packs follow these steps in `cemu-config`:
- Right-click a game and select `Edit graphic packs`
- Select `Download latest community graphic packs` *You need to be connected to the internet.*
- Choose and enable the graphic packs / mods / cheats etc. that you want
- Press `[Alt]` + `[F4]` to exit the window

The [Cemu Wiki](https://wiki.cemu.info/wiki/Main_Page) offers tons of well documented guides and optimizations for specific games - just use the search function on that wiki to find your desired game guide.

#### Shader caches
When your game is loaded, check for its ID on the title bar in front of "SaveDir:" and note it down. The directory where transferable shader caches are stored is `\userdata\system\configs\cemu\shaderCache`.

They're generated the first time you play through a game and at that time cause noticeable stuttering. You can download a complete cache from places like [here](https://www.reddit.com/r/Cemucaches/comments/7bv7el/complete_shader_cache_collection_1110c_v2/) and rename them to match your game version's ID to spare yourself most of that unpleasant experience. Just keep in mind that shader caches from versions older than 1.8.0 are incompatible with later versions of Cemu. 

#### Custom per game settings
Some games require custom game profile settings (often to use the `CPU mode "single-core recompiler` instead of auto).

To create customized game profiles follow these steps in `cemu-config`:
- right-click a game and select `Edit game profile`
- change the game settings as needed
- press `ALT+F4` to exit the window

Again the [Cemu Wiki](https://wiki.cemu.info/wiki/Main_Page) offers tons of well documented guides and optimizations for specific games - just use the search function on that wiki to find your desired game guide.

Your changes are stored **temporary** in the folder `/usr/cemu/gameProfiles`.
To save the change **permanently** in the Linux overlay (after reboot) it is currently necessary to enter the command `batocera-save-overlay` via the terminal.
For more information you can also read the topic [Modify the system while it's running](:modify_the_system_while_it_s_running)

## Controls
Here are the default Wii U's controls shown on a [Batocera Retropad](:configure_a_controller):

If you are using a XBOX One Controller the mapping to the Wii U (Pro) Gamepad is really easy. The most buttons are as expected, only the following are different:

| XBOX One Controller | Wii U Gamepad |
| A | B |
| B | A |
| X | Y |
| Y | X |
| XBOX Guide | Home |

Here's a picture of a physical Wii U Pro controller to help illustrate:

### Gamepad view
The Wii U Gamepad offers an integrated touchscreen. You can access the Gamepad view by pressing and holding the `[Tab]` key on your keyboard. Clicking somewhere with the mouse simulates a touch on this screen.

### Gamepad motion control
Some games require the motion control function of the Gamepad (e.g. Splatoon forces you to use motion control in the tutorial if you start the game for the first time)

Cemu emulates motion control via `mouse gesture` + `right mouse button`

### Wiimote support
Since v41, Wiimotes may be used as controllers in Cemu. To do so, pair a Wiimote and make sure the **MODE** in **WIIMOTE GUN SETTINGS** is set to **JOYSTICK** (not **GUN**). Both models Wiimote (RVL-003) and Wiimote incl. MotionPlus (RVL-036) are supported.

Extensions may be used as far as Cemu supports them.
Reported as working in Cemu 2.0-81:
- RVL-003 with Nunchuk or MotionPlus or both
Reported as not working in Cemu 2.0-81 (see [PR #12291](https://github.com/batocera-linux/batocera.linux/pull/12291) for details):
- RVL-003 with Classic Controller (broken button mapping)
- RVL-003 with Classic Controller Pro (not recognized)
- RVL-036 with any extension (unstable connection)

## Troubleshooting
### Migration from v35 to v36
Batocera uses the Windows build of Cemu up to v35 and the Linux build from v36.

The directory layout of these builds is incompatible to each other. It was reported that Cemu in v36 does not properly start with the v35 configuration in place. Thus, the configuration must be moved before Cemu is started for the first time after migration:

- `%%mv /userdata/system/configs/cemu/ /userdata/system/configs/cemu-wine/%%`

If you'd like to keep your existing data, copy it to the new location:

- Save states: `%%cp -a /userdata/saves/cemu/drive_c/cemu/ /userdata/saves/wiiu/%%`
- Graphic packs: `%%cp -a /userdata/system/configs/cemu-wine/graphicPacks/ /userdata/saves/wiiu/graphicPacks/%%`
- Shader cache: `%%cp -a /userdata/system/configs/cemu-wine/shaderCache/ /userdata/system/cache/cemu/shaderCache/%%`

After verifying that everything works as expected, and if you're sure that the old data of v35 is not required anymore, you can remove the files:

- `%%rm -r /userdata/system/configs/cemu-wine/ /userdata/saves/cemu/%%`

If you'd like to go back from v36 to v35 instead, you have to undo the move:

- `%%mv /userdata/system/configs/cemu/ /userdata/system/configs/cemu-linux/%%`
- `%%mv /userdata/system/configs/cemu-wine/ /userdata/system/configs/cemu/%%`

### Migration from v30 to v31
After you make upgrade of Batocera in **v31** you need to move your backups.

- `%%mkdir -p /userdata/saves/cemu/drive_c/cemu%%`
- `%%cp -a /userdata/saves/cemu/sys /userdata/saves/cemu/drive_c/cemu%%`
- `%%cp -a /userdata/saves/cemu/usr /userdata/saves/cemu/drive_c/cemu%%`

### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).