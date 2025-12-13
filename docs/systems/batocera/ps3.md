# Sony PlayStation 3

**Source:** https://wiki.batocera.org/systems:ps3  
**Last fetched:** 2025-12-06 16:19:37

---

# Sony PlayStation 3
The PlayStation 3 is a home console developed by Sony. It was released in 2006.

PS3 emulation is only available on x86_64 (i.e. not on Raspberry Pi, Odroid or other SBCs).

This system scrapes metadata for the `ps3` group and loads the `ps3` set from the currently selected theme, if available.

## Quick reference
- **Emulator:** RPCS3
- **Folder:** `/userdata/roms/ps3`
- **Accepted ROM formats:** `.psn` `.squashfs`
- **Accepted folder extensions:** `.ps3`

## BIOS
| MD5 checksum | Share file path | Description |
| `a0b63a3e4ae92ed176d6b9a67ce447f0` | `bios/PS3UPDAT.PUP` | PS3 firmware file |

Sony distributes this firmware on their website for installing onto your PlayStation 3; no link can be provided but it's easy enough to find by using a search engine.

`PS3UPDAT.PUP` is still updated to this day. The MD5 shown here may be for an older firmware, check the **MISSING BIOS** tool to check the MD5 for your current installation of Batocera.

## ROMs

Add other formats.

PlayStation 3 ROMs can come in many formats, disc-based, PSN and FIXME. Installation differs depending on format.

PS3 games have a string of letters and numbers referred to as their title ID. For example: `NPEB01393` is the title ID for a PSN copy of Hatsune Miku: Project DIVA F.

Title IDs that begin with B are disc-based games; title IDs that begin with N are digital PSN games.

### Disc-based game folder
Batocera accepts disc-based PS3 ROMs stored as folders in the following folder structure:

```

roms/ps3/
     └─ Game name.ps3/
        ├─ PS3_GAME/
        │  ├─ LICDIR/
        │  ├─ TROPDIR/ (trophy data)
        │  ├─ USRDIR/ (the main game data)
        │  ├─ ICON0.PNG
        │  ├─ PARAM.SFO
        │  ├─ PIC0.PNG
        │  ├─ PS3LOGO.DAT
        │  └─ (various other metadata files)
        ├─ PS3_UPDATE/ (built-in firmware update, if applicable)
        └─ PS3_DISC.SFB

```

Yes, the PS3 ROM folder name has a `.ps3` extension to it! Yes, you can attach extensions to a folder (they are just a part of the filename after all).

#### SquashFS folder compression
From Batocera **v33** and higher, you can losslessly compress PS3 game folders as SquashFS images and still have RPCS3 read them as if though they weren't compressed at all!

To do so, open up [SSH](:access_the_batocera_via_ssh) and run the following commands on your already installed disc-based game:

```

cd /userdata/roms/ps3
mksquashfs "Game name.ps3" "Game name.squashfs"

```

For example:

```

cd /userdata/roms/ps3
mksquashfs "Little Big Planet.ps3" "Little Big Planet.squashfs"

```

### Digital PSN games
PSN games were originally downloaded from the online store and installed onto the hard-drive. Because they are not disc-based games, some manual action is required:

  - On the system list, press `[F1]` on the keyboard and click on **Applications** in the left sidebar.
  - Open `rpcs3-config`.
  - Click on **File** -> **Install Packages, Raps, Edats**.
  - Navigate to and install the PSN game's PKG file (usually the larger file, this may take a while).
  - Repeat the process for any additional licence/DLC files (RAPs, EDATs and other PKG files).
  - Right click the installed title and select **Copy Info** -> **Copy Name + Serial**.
  - Once that's complete, use `[Alt]` + `[Tab]` to switch focus back to the file explorer (if we quit out of the application, the clipboard is cleared).
  - In the file browser, click on **Share** and navigate to `roms/ps3`.
  - Create a new text file titled after the game's name followed by the `.psn` extension. For instance, `Scott Pilgrim vs. the World.psn` Pasting the clipboard's contents here and erasing the serial number may be faster.
  - Open this as a text document and enter the game's ID code in a single line. For instance, `NPUB30162`. Pasting the clipboard's contents and erasing the name may be faster. `[Ctrl]` + `[S]` to save the file and `[Ctrl]` + `[Q]` to exit.
  - `[Alt]` + `[Tab]` back to `rpcs3-config` and exit out of both the `rpcs3-config` and the file manager by pressing `[Ctrl]` + `[Q]` two additional times.
  - Update your gamelist to show the added PSN game.

The PSN game will be installed to `/userdata/system/configs/rpcs3/dev_hdd0/game/<GAMEID>` and the userdata to `/userdata/system/configs/rpcs3/dev_hdd0/home/00000001/`. This is subject to change in the future.

Here's an example text file (which can be downloaded) that can be placed in `rom/ps3`:

```

NPUB30162

```

For this example text file, the resulting folder structure would look like this:

```

/userdata/
 ├─ roms/ps3/
 │       └─ Scott Pilgrim vs. the World.psn
 └─ system/configs/rpcs3/dev_hdd0/game/NPUB30162/
                                       └─ (the game data)

```

## Emulators
### RPCS3
RPCS3 [(Russian Personal Computer Station 3)](https:*rpcs3.net/blog/2018/01/23/rpcs3-2017-wrap-up-a-stunning-year-of-progress/) is an experimental emulator for the PS3. [Founded in May of 2011 by DH and Hykem,](https:*rpcs3.net/about) its development has been steadily increasing in activity over time. It's pretty much the only PS3 emulator that can consistently run most commercial games.

It requires more resources than older systems, benefiting from a decent CPU and a Vulkan-capable GPU for hardware acceleration. Games won't run correctly if you don't have GPU acceleration, refer to RPCS3's [hardware recommendations on their website](https:*rpcs3.net/quickstart). Here's a cool benchmark table: https:*docs.google.com/spreadsheets/d/1Rpq_2D4Rf3g6O-x2R1fwTSKWvJH7X63kExsVxHnT2Mc/edit#gid=0

With that said, this is still an **experimental** emulator, and most games have issues (even if minor). Consult its [compatibility list](https:*rpcs3.net/compatibility) first before making any reports. If one of the games is marked as "playable" on the compatibility list but you're still having issues with it, consult [RPCS3's wiki](https:*wiki.rpcs3.net/index.php?title=Main_Page) for that specific game.

#### RPCS3 configuration
Standardized features available to all cores of this emulator: `ps3.videomode`, `ps3.powermode`, `ps3.tdp`, `ps3.videomode`, `ps3.bezel`, `ps3.bezel_stretch`, `ps3.hud`, `ps3.hud_corner`, `ps3.bezel.tattoo`, `ps3.bezel.tattoo_corner`, `ps3.bezel.tattoo_file`, `ps3.bezel.resize_tattoo`, `ps3.use_guns`, `ps3.use_wheels`, `ps3.wheel_rotation`, `ps3.wheel_deadzone`, `ps3.wheel_midzone`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **CPU** ||
| **PPU DECODER `ps3.rpcs3_ppudecoder`** | LLVM is fastest, use the Interpreter settings if there are issues.\\ => LLVM Recompiler `Recompiler (LLVM)`, Dynamic Interpreter `Interpreter (dynamic)`, Static Interpreter `Interpreter (static)`. |
| **SPU DECODER `ps3.rpcs3_spudecoder`** | LLVM used by default. Use ASMJIT if game crashes; then Interpreter (fast) if still crashing.\\ => LLVM Recompiler `Recompiler (LLVM)`, ASMJIT Recompiler `Recompiler (ASMJIT)`, Fast Interpreter `Interpreter (fast)`, Precise Interpreter `Interpreter (precise)`. |
| **SPU XFloat Accuracy `ps3.rpcs3_spuxfloataccuracy`** | Can fix bugs in some games. Only relevant for dynamic or LLVM SPU decoder.\\ => Accurate XFloat `accurate`, Approximate XFloat `approximate`, Relaxed XFloat `relaxed`. |
| **PREFERRED SPU THREADS `ps3.rpcs3_sputhreads`** | Limiting to 1 or 2 may fix audio stuttering on weaker CPUs in some games. Leave on automatic if slowdown occurs.\\ => 1 thread `1`, 2 threads `2`, 3 threads `3`, 4 threads `4`, 5 threads `5`, 6 threads `6`. |
| **SPU LOOP DETECTION `ps3.rpcs3_spuloopdetection`** | May provide performance gain on CPUs with low core/thread count at the expense of possible broken timings.\\ => Off (Default) `False`, On `True`. |
| **SPU BLOCK SIZE `ps3.rpcs3_spublocksize`** | Mega and Giga modes may improve performance. Use the Safe mode for maximum compatibility.\\ => Safe (Default) `Safe`, Mega `Mega`, Giga `Giga`. |
| **MAX POWER SAVING CPU-PREEMPTIONS `ps3.rpcs3_maxcpu_preemptcount`** | Helps reduce CPU power consumption by throttling the CPU when not needed. Useful for handhelds.\\ => Off (Default) `0`, Minimum `50`, Moderate `100`, Maximum `150`. |
| **VIDEO** ||
| **ASPECT RATIO `ps3.rpcs3_ratio`** | PS3's internal ratio setting. Some games only support 16/9.\\ => 16:9 (default) `16:9`, 4:3 `4:3`. |
| **ADDITIONAL FRAMELIMIT `ps3.rpcs3_framelimit`** | Most games already have an internal framelimit. Minor performance cost.\\ => Off (faster, unstable) `False`, 20 `20`, 25 `25`, 30 `30`, 35 `35`, 40 `40`, 45 `45`, 50 `50`, 55 `55`, 59.94 `59.94`, 60 `60`. |
| **RENDER RESOLUTION (SCALING) `ps3.rpcs3_resolution_scale`** | Choose your preferred render resolution.\\ => 640x360 `50`, 960x540 `75`, 1280x720 (Default) `100`, 1600x900 `125`, 1920x1080 `150`, 2240x1260 `175`, 2560x1440 `200`, 3200x1800 `225`, 3840x2160 `250`, 4480x2520 `275`, 5120x2880 `300`. |
| **VSYNC `ps3.rpcs3_vsync`** | Can fix screen tearing on unorthodox displays (most LCDs don't need this).\\ => Off (Default) `False`, On `True`. |
| **STRETCH TO DISPLAY AREA `ps3.rpcs3_stretchdisplay`** | Distorts the output to fill the display fully Overrides aspect ratio.\\ => Off `False`, On `True`. |
| **RENDER** ||
| **GRAPHICS API `ps3.rpcs3_gfxbackend`** | Choose which graphics API library to use.\\ => OpenGL `OpenGL`, Vulkan `Vulkan`. |
| **ANISOTROPIC FILTER `ps3.rpcs3_anisotropic`** | Improves clarity of distant textures.\\ => 2x `2`, 4x `4`, 8x `8`, 16x `16`. |
| **ANTI-ALIASING `ps3.rpcs3_aa`** | Enhancement. Smooth out jagged edges on 3D object polygons.\\ => Disabled `Disabled`. |
| **ZCULL ACCURACY `ps3.rpcs3_zcull`** | Can improve performance at the expense of graphics accuracy.\\ => Precise (Slowest)(Default) `Precise`, Approximate (Fast) `Approximate`, Relaxed (Fastest) `Relaxed`. |
| **SHADER QUALITY `ps3.rpcs3_shader`** | Controls precision of generated shaders. Low quality can improved performance.\\ => Ultra `Ultra`, High (Default) `High`, Low `Low`, Automatic `Auto`. |
| **OUTPUT SCALING `ps3.rpcs3_scaling`** | Final image filtering.\\ => Nearest `Nearest`, Bilinear (Default) `Bilinear`, FidelityFX Super Resolution `FidelityFX Super Resolution`. |
| **SHADER MODE `ps3.rpcs3_shadermode`** | Only Async (skip draw) avoids freezing while compiling shaders.\\ => Legacy (single threaded) `Shader Recompiler`, Async (multi threaded)(Default) `Async Shader Recompiler`, Async with Shader Interpreter `Async with Shader Interpreter`, Shader Interpreter only `Shader Interpreter only`. |
| **NUMBER OF SHADER COMPILER THREADS `ps3.rpcs3_num_compilers`** | Only applicable when either Async Shader mode is set.\\ => 1 `1`, 2 `2`, 3 `3`, 4 `4`, 5 `5`, 6 `6`, 7 `7`, 8 `8`, 9 `9`, 10 `10`, 11 `11`, 12 `12`, 13 `13`, 14 `14`, 15 `15`, 16 `16`. |
| **WRITE COLOR BUFFERS `ps3.rpcs3_colorbuffers`** | May fix missing graphics and broken lighting at the cost of performance.\\ => Off (Default) `False`, On `True`. |
| **STRICT RENDERING MODE `ps3.rpcs3_strict`** | Straict API specification. Can resolve rare cases of missing graphics and flickering.\\ => Off (Default) `False`, On `True`. |
| **DISABLE VERTEX CACHE `ps3.rpcs3_vertexcache`** | Disables the vertex cache. Might resolve missing or flickering graphics output but degrade performance.\\ => Off (Default) `False`, On `True`. |
| **MULTITHREADED RSX `ps3.rpcs3_rsx`** | Offloads some RSX operations to a secondary thread. Improves performance in high-core processors.\\ => Off (Default) `False`, On `True`. |
| **ASYNCHRONOUS TEXTURE STREAMING `ps3.rpcs3_async_texture`** | Stream texture to GPU in parrallel. Can improve performance on more powerful GPU's that have spare headroom.\\ => Off (Default) `False`, On (Vulkan Only) `True`. |
| **AUDIO** ||
| **AUDIO FORMAT `ps3.rpcs3_audio_format`** | Choose number of audio channels.\\ => Stereo `Stereo`, Surround 5.1 `Surround 5.1`, Surround 7.1 `Surround 7.1`. |
| **CONVERT TO 16-BIT `ps3.rpcs3_audio_16bit`** | Use 16 bit audio samples for audio drivers that don't support 32bit. Only use if you get no audio.\\ => Off (Default) `False`, On `True`. |
| **ENABLE AUDIO BUFFERING `ps3.rpcs3_audiobuffer`** | Can reduce crackle and stutter but increases audio latency.\\ => Off `False`, On (Default) `True`. |
| **AUDIO BUFFER DURATION `ps3.rpcs3_audiobuffer_duration`** | Duration of audio buffer in milliseconds. Higher numbers may cause audio latency.\\ => 10ms `10`, 20ms `20`, 40ms `40`, 60ms `60`, 80ms `80`, 100ms (Default) `100`, 120ms `120`, 140ms `140`, 160ms `160`, 180ms `180`, 200ms `200`, 220ms `220`, 240ms `240`. |
| **ENABLE TIME STRETCHING `ps3.rpcs3_timestretch`** | Reduces crackle and stutter further, but may cause a very noticeable reduction in audio quality on slower CPUs.\\ => Off (Default) `False`, On `True`. |
| **TIME STRETCHING THRESHOLD `ps3.rpcs3_timestretch_threshold`** | Buffer fill level (in percentage) below which time stretching will start.\\ => Off `0`, 15% `15`, 30% `30`, 45% `45`, 60% `60`, 75% (Default) `75`, 90% `90`, 100% `100`. |
| **GRAPHICAL USER INTERFACE `ps3.rpcs3_gui` (`ps3.gui` in Batocera FIXME and lower)** | Allows Alt+Tab to RPCS3's menu. Useful for manual disc-swapping.\\ => Off `0`, On `1`. |
| **SHOW LIGHT GUN CROSSHAIRS `ps3.rpcs3_crosshairs`** | \\ => Off `False`, On `True`. |
| **CONTROLLERS** ||
| **PS3 CONTROLLER 1 `ps3.rpcs3_controller1`** | Default uses SDL2, otherwise enable controller specific capabilities. Sony DS won't work with clone controllers.\\ => Legacy Evdev `Evdev`, Sony DS `Sony`. |
| **PS3 CONTROLLER 2 `ps3.rpcs3_controller2`** | Default uses SDL2, otherwise enable controller specific capabilities. Sony DS won't work with clone controllers.\\ => Legacy Evdev `Evdev`, Sony DS `Sony`. |
| **PS3 CONTROLLER 3 `ps3.rpcs3_controller3`** | Default uses SDL2, otherwise enable controller specific capabilities. Sony DS won't work with clone controllers.\\ => Legacy Evdev `Evdev`, Sony DS `Sony`. |
| **PS3 CONTROLLER 4 `ps3.rpcs3_controller4`** | Default uses SDL2, otherwise enable controller specific capabilities. Sony DS won't work with clone controllers.\\ => Legacy Evdev `Evdev`, Sony DS `Sony`. |
| **PS3 CONTROLLER 5 `ps3.rpcs3_controller5`** | Default uses SDL2, otherwise enable controller specific capabilities. Sony DS won't work with clone controllers.\\ => Legacy Evdev `Evdev`, Sony DS `Sony`. |
| **PS3 CONTROLLER 6 `ps3.rpcs3_controller6`** | Default uses SDL2, otherwise enable controller specific capabilities. Sony DS won't work with clone controllers.\\ => Legacy Evdev `Evdev`, Sony DS `Sony`. |
| **PS3 CONTROLLER 7 `ps3.rpcs3_controller7`** | Default uses SDL2, otherwise enable controller specific capabilities. Sony DS won't work with clone controllers.\\ => Legacy Evdev `Evdev`, Sony DS `Sony`. |

#### First RPCS3 run
When RPCS3 is run for the first time (just attempt to launch any game from ES), it will ask to install the provided firmware from the BIOS folder (`userdata/bios/PS3UPDAT.PUP`). Do so. This may take a while, grab a cup of tea while you wait. When it's done, simply exit the program (**File** -> **Exit** or `[Ctrl]` + `[Q]`) and launch a game again. This will need to be done for every new firmware released. This action can also be invoked manually by going to **File** -> **Install firmware**.

On the first run of each game, RPCS3 will compile PPU modules. This takes a long time, so grab some tea. In all future launches, wait time is dramatically decreased.

Do not launch games directly from RPCS3's interface. Do so from ES. Otherwise you will not have audio.

It is possible to have RPCS3 compile the PPU for all currently detected games (as opposed to only doing so when the game is launched). In rpcs3-config, go to (FIXME precise instructions) boot menu -> compile PPU cache for firmware and all games.

## Controls
Here are the Sony PlayStation 3's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### I don't know how to set up my PS3 games! They are in a weird format and not a folder.
This is more related to usage of RPCS3, refer to their [quick start guide](https://rpcs3.net/quickstart).

### I have X issue with game Y
For PS3 game specific issues, be sure to check [RPCS3's wiki](https://wiki.rpcs3.net/index.php?title=Main_Page) first.

For further troubleshooting, refer to the [generic support pages](:support).