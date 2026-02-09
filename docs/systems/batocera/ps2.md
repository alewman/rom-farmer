# Sony PlayStation 2

**Source:** https://wiki.batocera.org/systems:ps2  
**Last fetched:** 2025-12-06 16:19:36

---

# Sony PlayStation 2
The PlayStation 2 (PS2) is a sixth-generation console released by [Sony Computer Entertainment](wp>Sony_Computer_Entertainment) on October 26, 2000 and it was retailed for $299.99. It has the Emotion Engine CPU at 300 MHz with 32MB of RDRAM system memory and 4MB of eDRAM (VRAM). Its GPU is a custom Graphics Synthesizer, which runs at 150 MHz.

The PS2 became the highest selling console of all time with over 160 million units sold.

This system scrapes metadata for the "ps2" group and loads the `ps2` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.iso`, `.mdf`, `.nrg`, `.bin`, `.img`, `.dump`, `.gz`, `.cso`, `.chd`

| Emulators |
| [PCSX2](#pcsx2) |
| [libretro: PCSX2](#libretro_pcsx2) |
| [libretro: play](#libretro_play) |
| [play](#play) |

## BIOS
### Batocera 39 and later
We simplified the BIOS requirements with Batocera 39. From now on, you need to put your BIOS files in `/userdata/bios/ps2/` (they used to be in `/userdata/bios/` in previous Batocera versions).

We strongly recommend using the latest (REDUMP) BIOS for better emulation and depending on your region:
- USA: `ps2-0230a-20080220.bin`
- EUR: `ps2-0230e-20080220.bin` or `ps2-0250e-20100415.bin`
- JAP: `ps2-0230j-20080220.bin`

Regarding PS2 emulation:

- The USA BIOS can play NTSC and PAL games (European games will have a glitch on the PlayStation logo)
- The EUR BIOS can only play PAL games
- The JAP BIOS can only play NTSC games

You can also use a "region-free" EMU-BIOS PS2 `ps3_ps2_emu_bios.bin` available in the PS3 firmware, but warning: Fast Boot mode (or skip bios logo) must be enabled.

As the USA-region BIOS can run every game, only this one will be checked by Batocera 39:

| MD5 checksum | Share file path | Description |
|`21038400dc633070a78ad53090c53017` | `bios/ps2/ps2-0230a-20080220.bin` | PS2 firmware binary |

### Batocera 38 and older
For older versions of Batocera (38 and older), the following BIOS files are checked:

| MD5 checksum | Share file path | Description |
| `28922c703cc7d2cf856f177f2985b3a9` | `bios/SCPH30004R.bin` | PS2 firmware binary |
| `3faf7c064a4984f53e2ef5e80ed543bc` | `bios/SCPH30004R.MEC` | PS2 common and regional settings (optional, can be created by PCSX2) |
| `d5ce2c7d119f563ce04bc04dbc3a323e` | `bios/scph39001.bin` | PS2 firmware binary |
| `3faf7c064a4984f53e2ef5e80ed543bc` | `bios/scph39001.MEC` | PS2 common and regional settings (optional, can be created by PCSX2) |
| `9a9e8ed7668e6adfc8f7766c08ab9cd0` | `bios/EROM.BIN` | EROM firmware binary |
| `44552702b05697a14ccbe2ca22ee7139` | `bios/rom1.bin` | ROM1 is an additional part of the BIOS that contains some extra stuff like ID's for DVD Player version etc. |
| `b406d05922dac2eaf3c2e68157b1b468` | `bios/ROM2.BIN` | Extra information only required for certain Chinese PS2's |

The 7#### series of PlayStation 2 BIOes are known to have issues with running certain games. This is true on the console itself.

PCSX2 will automatically try to use them if they are present. Simply do not include them in your bios folder to avoid this. Only use the BIOSes listed above.

## ROMs
Place your Sony PlayStation 2 ROMs in `/userdata/roms/ps2`.

The recommended format to save space maintaining full compatiblity (starting Batocera **v31**) is [CHD](:disk_image_compression#chd).

## PS2 video modes
The PlayStation 2 was in the middle of an awkward phase of TV standards. Not only were displays transforming from the 4:3 aspect ratio to the 16:9 aspect ratio, but they were also going from interlaced to progressive. And this was also before video signals became standardized, like with HDMI. Thus, various PS2 games have varying degrees for supported video modes.

Fortunately, since we are using a high-level emulator, we don't need to worry about whether a game supports progressive scan or not. By virtue of emulation, all games are rendered as progressive scan anyway. If a game offers the option to use it though, there's no harm in activating it.

*In addition to this*, the PS2's BIOS itself supports setting the aspect ratio to 4:3 or 16:9, and games can read this setting to determine what aspect ratio to display. However, the majority of games actually ignore this setting and offer the option in the game itself, if at all. But for the games that do support asking the BIOS for the aspect ratio, the only way to switch their aspect ratios to 16:9 is via the following:

  - With a controller plugged in, launch and close any PS2 game. This will configure the controller so that we can navigate the BIOS without issues later.
  - While in the PS2 game list, press `[Select]` and go to **ADVANCED SYSTEM SETTINGS**. Set **GAME ASPECT RATIO** to "16:9".\\ 
This can also be set on a per-game basis by holding down  while hovering over the game and going to **ADVANCED GAME OPTIONS**.

  - Back out to the system list, then press `[F1]` on the keyboard to access the file manager.
  - Navigate to **Applications** on the left sidebar, then open `pcsx2-config`.
  - In the menu at the top of the screen, click **CDVD** and select "No disc".\\ 
  - Then click **System** and select "Boot BIOS".\\ 
  - Using the controller, go to **System Configuration**.\\ 
  - Press D-pad down to go to **Screen Size**.\\ 
  - Press  and then set the screen size to the aspect ratio of your display (most of the time, this will be 16:9).\\ 
  - Back out with  to ensure it saves, and exit the emulator with `[Ctrl]` + `[Q]`, `[Alt]` + `[Tab]` and `[Alt]` + `[F4]`.

Certain games only offer the ability to set the screen's aspect ratio in their in-game options. A comprehensive list can be found at the [everybodywiki's list of PS2 games with alternative video modes page](https://en.everybodywiki.com/List_of_PlayStation_2_games_with_alternative_display_modes). This includes notes about special conditions about their activation. Do not worry about progressive scan, 480p, 1080i or 240p mode.

For the remaining games that do not support 16:9 aspect ratio (or their offering is inferior as they use the "crop" method, zooming in the image), setting **WIDESCREEN PATCHES** in the **ADVANCED SYSTEM SETTINGS** can force the game to render in widescreen. This is known to cause graphical glitches, notably stretched 2D elements like FMVs and geometry popping in.

For games which support both 50 Hz and 60 Hz, they will either ask to set the appropriate mode on boot or have it available in its options menu. Most modern displays will be running at 60 Hz, so choose that whenever offered. NTSC games will run in 60 Hz by default.

## Emulators
### PCSX2
[PCSX2](https://pcsx2.net) is a free and open-source PlayStation 2 emulator for Windows, Linux, and macOS that supports a wide range of PlayStation 2 video games with a high level of compatibility and functionality. Although PCSX2 can closely mirror the original gameplay experience on the PlayStation 2, PCSX2 supports a number of improvements over gameplay on a traditional PlayStation 2, such as the ability to use custom resolutions up to 8192×8192, anti-aliasing, and texture filtering. 

Batocera is shipping the latest PCSX2 Linux standalone binary. Check out the up-to-date [official compatibility](https://pcsx2.net/compatibility-list.html) list for more information. 

#### PCSX2 configuration
Standardized features available to all cores of this emulator: `ps2.videomode`, `ps2.ratio`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `ps2.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `12`, Software `13`. |
| **SHOW BIOS BOOTLOGO `ps2.fullboot`** | Show BIOS animation when starting content. Off allows more games to boot successfully and without issues, however some games (such as those that don't feature language selection screens) require this animation to play out.\\ => Off `0`, On `1`. |
| **VIDEO RESOLUTION `ps2.internal_resolution`** | Enhancement. Increase the rendering resolution. Makes 3D objects clearer. Lower this setting for [GPU intensive games](https://forums.pcsx2.net/Thread-LIST-The-Most-GPU-Intensive-Games).\\ => 1x 640x480 `1`, 2x 720p `2`, 3x 1080p `3`, 4x 1440p 2K `4`, 5x 1620p 3K `5`, 6x 2160p 4K `6`, 7x 2880p 5K `7`. |
| **ANISOTROPIC FILTERING `ps2.anisotropic_filtering`** | Enhance the quality of distant perspective textures.\\ => Off `0`, 2x `2`, 4x `4`, 8x `8`, 16x `16`. |
| **SKIPDRAW HACK `ps2.skipdraw`** | Skips drawing some surfaces altogether, based on how likely they are to cause issues. Specify how many surfaces should get skipped after the first problematic one is found. Try lower values first like 1-3 then use higher ones (the highest the number the higher the chance of broken/missing graphics and effects). This hack may cause random speedups as well! This option may help with removing ghost images or other post-processing effect rendered incorrectly.\\ => Off `0`, 1 `1`, 2 `2`, 3 `3`, 4 `4`, 5 `5`. |
| **ALIGN SPRITE (HACK) `ps2.align_sprite`** | Fix for removing vertical black lines in several games such as Tekken or Soul Calibur.\\ => Off `0`, On `1`. |
| **VSYNC `ps2.vsync`** | Fix the heavy screen tearing in games (CPU heavy)\\ => Off `0`, On `1`. |
| **MICRO VU SPEED HACKS `ps2.micro_vu`** | Good speedup and high compatibility; recommended but may cause issues\\ => mVU Flag Hack: May cause bad graphics [Recommended] `vuFlagHack`, MTVU: May cause hanging [Recommended on 3+ cores] `vuThread`, Instant VU1: May cause some graphical errors `vu1Instant`, mVU Flag Hack + MTVU `vuFlagHack,vuThread`, mVU Flag Hack + Instant VU1 `vuFlagHack,vu1Instant`. |
| **GAMES CHEATS `ps2.EmuCore_EnableCheats`** | For cheating in games with Action Replay\\ => Off `disabled`, On `enabled`. |
| **WIDESCREEN PATCHES `ps2.EmuCore_EnableWideScreenPatches`** | You must use a 16/9 RATIO and disable BEZEL\\ => Off `disabled`, On `enabled`. |
| **AUTOMATIC GAMEFIXES `ps2.EmuCore_EnablePatches`** | Selectively use specific tested fixes for games.\\ => Off `disabled`, On `enabled`. |
| **MANUAL GAMEFIXES `ps2.EmuCore_ManualPatches`** | These can cause compatibility or performance issues\\ => Off `disabled`, VU Add hack - Fixes Tri-Ace games boot crash `VuAddSubHack`, FPU Compare hack - For Digimon Rumble Arena 2 `FpuCompareHack`, FPU Multiply hack - For Tales of Destiny `FpuMulHack`, FPU Negative Div hack - For Gundam Games `FpuNegDivHack`, VU XGkick hack - For Eremental Gerad `XgKickHack`, FFX videos fix - Fixes bad graphics overlay `IPUWaitHack`, EE timing hack - Try if all else fails `EETimingHack`, Skip MPEG hack - Skips videos/FMVs that freezes `SkipMPEGHack`, OPH Flag hack - Try if game freeze on same frame `OPHFlagHack`, Handle DMAC writes when it busy `DMABusyHack`, Simulate VIF1 FIFO read - Fix slow loading `VIFFIFOHack`, Delay VIF1 Stalls - For SOCOM2 n Spy Hunter `VIF1StallHack`, Enable the GIF FIFO - Wallace and Gromit, Dj Hero `GIFFIFOHack`, Preload TLB hack to avoid tlb miss on Goemon `GoemonTlbHack`, VU I bit hack - Scarface The World is Yours `ScarfaceIbit`, VU I bit hack - Crash Tag Team Racing `CrashTagTeamRacingIbit`, VU0 Kickstart to avoid sync problems with VU1 `VU0KickstartHack`. |
| **MULTITAP `ps2.multitap`** | Allows 5 or 8 maximum player support in games\\ => Off `disabled`, Port1 `port1`, Port2 `port2`, Port1+2 `port12`. |

To configure other settings for PCSX2, open its standalone configuration application `pcsx2-config` from the Applications menu (press `[F1]` on the system list).

### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `ps2.videomode`, `ps2.ratio`, `ps2.smooth`, `ps2.shaders`, `ps2.pixel_perfect`, `ps2.decoration`, `ps2.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `ps2.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `ps2.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `ps2.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: PCSX2
##### libretro: PCSX2 configuration
#### libretro: play
##### libretro: play configuration
### play
#### play configuration
Standardized features available to all cores of this emulator: `ps2.videomode`

## Texture packs
Texture packs replace the textures in a game with other (usually higher resolution) textures. (FIXME which emulators available support this? Just PCSX2?)

Texture packs go into the PCSX2 config folder appropriate to the game: `system/configs/PCSX2/textures/<GameCode>`. For example if replacing the texture in the game God of War, they would go into the `system/configs/PCSX2/textures/SCUS-97399` folder. (FIXME how do we find out the GameCode?)

(FIXME aren't there options that need to be enabled?)

## Controls
Here are the default Sony PlayStation 2's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting

A lot of the special configuration for troubleshooting is done via `pcsx2-config` which you can reach via the [Batocera applications menu](:emulationstation_overview#file_manager_and_applications_menu).

### Performance
PS2 emulation with PCSX2 requires a relatively decent CPU with a good GPU for hardware acceleration. It will only work on x86/x86_64 machines. Even if your Batocera system does emulate [Wii U](systems:wiiu) or even [PS3](systems:psx) games fine it may struggle with PCSX2 emulation in terms of graphic improvements or resolution upscaling. You can find some [PC performance measurements and recommendations on this page](:choose_a_desktop_computer).

If you still have trouble try to keep the original resolution and default emulation settings. Some games need high-end, possibly [overclocked CPUs](https:*forums.pcsx2.net/Thread-LIST-The-Most-CPU-Intensive-Games) or [powerful GPUs](https:*forums.pcsx2.net/Thread-LIST-The-Most-GPU-Intensive-Games), whereas some games run even on [weak processors](https://forums.pcsx2.net/Thread-LIST-Games-that-don-t-need-a-strong-CPU-to-emulate).

The [PCSX2 Wiki](https://wiki.pcsx2.net) offers tons of well documented guides and optimizations for specific games - just use the search function on that wiki to find your desired game guide.
 

With that said, what if you're experiencing unusually low performance on hardware that should otherwise be running it at full speed? Sometimes the configuration file gets corrupted and resets to using "all defaults" according to PCSX2, which is to say *not good*. You can reset your configuration by doing the following:

  - Open up the file manager by pressing `[F1]` on the system list.\\  
  - Click **Applications** in the top of the sidebar on the left.\\ 
  - Double-click **pcsx2-config** to open up the PCSX2 configuration tool.\\  
  - Navigate to **Config** -> **General Settings** 
On older versions, this is **Emulator settings...**
\\  
  - Slide the preset at the bottom of the window to the right until it says "3 - Balanced". On older, single/dual-core machines you may want to slide this back to the default of "2 - Safe".\\ 
  - Press **Apply**. Quit PCSX2 with `[Ctrl]`+`[Q]` or by using the **File** menu.
  - Test out your game. :-)

### Intermittent warped audio
Due to how the synchronizing function of the audio plugin works, even when running games on a computer that is capable of going way above 100% speed in a stable fashion, random bits of time-stretched audio can be heard occasionally or even frequently.

A good workaround is to set the audio syncing method to *Async Mix* via `pcsx2-config`. This can cause A/V sync issues with certain games and is **not recommended with rhythm games**. Do not set it to None as it basically does the same thing as Async Mix but has more issues.

### Specific game does not boot/graphical issues
Be aware that some games relies on BIOS to get start-up parameters and thus may not work correctly with disabling the BIOS start animation. Therefore you should enable the boot animation in the first step for problematic games with **SHOW BIOS BOOTLOGO** `ps2.fullboot=1`.

Also ensure that automatic gamefixes are enabled in Batocera. If you still have problems take a look at the official [PCSX2 Wiki](https://wiki.pcsx2.net) and use the search function on that wiki to find information for the affected game.

### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).