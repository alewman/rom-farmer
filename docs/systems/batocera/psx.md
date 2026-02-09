# Sony PlayStation

**Source:** https://wiki.batocera.org/systems:psx  
**Last fetched:** 2025-12-06 16:19:39

---

# Sony PlayStation
The [PlayStation](wp>PlayStation_(console)) (frequently referred to in shorthand as the "PS1", "PSOne" or its codename: "PSX" (not to be confused with [the actual PSX](wp>PSX_(digital_video_recorder)))) is a fifth generation console released by [Sony Computer Entertainment](wp>Sony_Computer_Entertainment) on December 3, 1994 in Japan and September 9, 1995 in the US. It was retailed for $299.99. It had a R3000 CPU (which was used by NASA for a space craft to take pictures of Mars because of its reliability) at 33.8688 MHz with 2MB of RAM and 1MB of VRAM. It used a proprietary MDEC video compression unit, which is integrated into the CPU, allowing for playback of full motion video at a higher quality than other consoles of its generation. It also had a superior digital-to-analog converter than most CD players at the time.

It was a commercial success, partly due to Sony encouraging third-party developers with affordable dev-kits, being relatively easy to program for (compared to others at the time) and because its CD-based media was cheaper than the competition.

Although most PlayStation games would run at a near 240p resolution, some were capable of running at 480i. [Here's a link to a list on the shmups system11 forum.](https://shmups.system11.org/viewtopic.php?f=6&t=54382)

--> In case that list ever gets lost to the annals of the internet...#

austin532

Joined: 12 Mar 2014
Posts: 842
Location: Arizona, US 	
	
Post subject: List of PS1 games that natively run in 480i
Post Posted: Tue Jul 07, 2015 2:20 am 

Alright, here is an ever growing list of PS1 games that natively run in 480i.

I also have a list of PS2 games that run in 240p which can be found here. https://shmups.system11.org/viewtopic.php?f=6&t=55420

- All Star Boxing
- Arcade Hits: Shienryu
- Atari Anniversary Edition Redux (7 of the 12 games support 480i in High resolution mode)
- Bloody Roar II
- Boxing
- Bubsy 3D
- Bugi
- Clock Tower II: The Struggle Within
- Clock Tower: Ghost Head
- Dead or Alive
- Devil Dice
- Dragon Quest Characters: Torneko no Daibouken 2: Fushigi no Dungeon
- Dynasty Warriors
- Ehrgeiz
- Formula 1 (High Res and Wide Screen modes)
- Gekioh Shooting King
- Geki-Oh Shooting King: Shienryu
- iS Internal Section
- Kensei: The Sacred Fist
- Kickboxing
- Kickboxing Knockout
- Rapid Racer
- Ridge Racer Turbo
- Sangoku Musou
- Simple 1500 Series Vol. 32: The Boxing
- Simple 1500 Series Vol. 64: The Kickboxing
- Tekken 3
- Tobal No.1
- Tobal 2
- Torneko: The Last Hope
- Turbo Prop Racing
- Xevious 3D/G+ (Xevious, Super Xevious, and Xevious Arragement displays 480i in Normal Screen Modes)
- XI [sai]
_________________
Framemeister 240p scanline settings: https://shmups.system11.org/viewtopic.php?f=6&t=33450&start=9600

Last edited by austin532 on Fri Jun 02, 2017 2:25 am, edited 7 times in total.

<--

This system scrapes metadata for the `psx` group and loads the `psx` set from the currently selected theme, if available.

### Quick reference
- **Folder:** `roms/psx/`
- **BIOS required?** Optional, some games require one.

| Emulators | Accepted ROM formats | BIOS files | Configuration via |
| [DuckStation](#duckstation) | `.cue` `.img` `.mdf` `.pbp` `.toc` `.cbn` `.m3u` `.ccd` `.chd` `.iso`  | `psxonpsp660.bin` `scph101.bin` `scph1001.bin` `scph5500.bin` `scph5501.bin` `scph5502.bin` `scph7001.bin` | EmulationStation and duckstation-config  |
| [libretro: PCSX ReARMed](#libretro:_pcsx_rearmed) | `.bin` `.cue` `.img` `.mdf` `.pbp` `.toc` `.cbn` `.m3u` `.ccd` `.chd` | `psxonpsp660.bin` `scph101.bin` `scph1001.bin` `scph5501.bin` `scph7001.bin` | EmulationStation and RetroArch |
| [libretro: SwanStation](#libretro:_swanstation) | `.cue` `.img` `.mdf` `.pbp` `.toc` `.cbn` `.m3u` `.ccd` `.chd` `.iso` | `psxonpsp660.bin` `scph101.bin` `scph1001.bin` `scph5500.bin` `scph5501.bin` `scph5502.bin` `scph7001.bin` | EmulationStation and RetroArch |
| [libretro: DuckStation](#libretro:_duckstation) | `.cue` `.img` `.mdf` `.pbp` `.toc` `.cbn` `.m3u` `.ccd` `.chd` `.iso` | `psxonpsp660.bin` `scph101.bin` `scph1001.bin` `scph5500.bin` `scph5501.bin` `scph5502.bin` `scph7001.bin` | EmulationStation and RetroArch |
| [libretro: Mednafen_PSX](#libretro:_mednafen_psx) | `.cue` `.pbp` `.toc` `.m3u` `.ccd` `.chd` | `psxonpsp660.bin` `scph5500.bin` `scph5501.bin` `scph5502.bin` | EmulationStation and RetroArch |

## BIOS
The BIOS files aren't strictly required for emulation, but can dramatically improve compatibility and accuracy. As a replacement for any of the first 3 BIOS files mentioned above, it is also possible
to use the PSXONPSP660.bin BIOS. This BIOS comes from the PSP, is region-free and can sometimes offer better performance. Their md5 checksums and expected paths are as follows:

| MD5 checksum | Share file path | Description |
| `c53ca5908936d412331790f4426c6c33` | `bios/psxonpsp660.bin` | Extracted from a PSP |
| `6e3735ff4c7dc899ee98981385f6f3d0` | `bios/scph101.bin` | Version 4.4 03/24/00 |
| `dc2b9bf8da62ec93e868cfd29f0d067d` | `bios/scph1001.bin` | Version 2.0 05/07/95 |
| `8dd7d5296a650fac7319bce665a6a53c` | `bios/scph5500.bin` | PS1 JP BIOS |
| `490f666e1afb15b7362b406ed1cea246` | `bios/scph5501.bin` | Version 3.0 11/18/96 PS1 US BIOS |
| `32736f17079d0b2b7024407c39bd3050` | `bios/scph5502.bin` | PS1 EU BIOS |
| `1e68c231d0896b7eadcad1d7d8e76129` | `bios/scph7001.bin` | Version 4.1 12/16/97 |

## ROMs
PlayStation ROMs typically come in the modern `.cue`/`.bin` format. The `.cue` sheets contain the metadata of where the 'data tracks' on the disc are physically located, and the `.bin` files are the actual data. They must retain the same filename (the `.cue` file is just a text file that points to the `.bin` file) and be in the same directory to function together. When loading PSX ROMs, be sure to select the `.cue` file, not the `.bin` file. Some games may work (with glitches) with just the `.bin` file loaded, but most don't. Refer to [CD image formats](:cd_image_formats) for more info.

Older PlayStation ROMs may have been ripped in `.iso` image format (which may also use the `.img` extension), which is a direct representation of the data on the disc. Some emulators are incompatible with this format. This format typically only allows loading the first `.bin` file, and no others. In order to properly use the ROM like this, get the `.iso`/`.img` file and [pair it with its CUE sheet](:cd_image_formats#cue_sbi_gdi_sheet_recovery). There are tools that can do this automatically for you.

`.pbp` is a proprietary format made by Sony to store PlayStation games (even multi-disc ones) in a compressed format for their PS1-on-PSP downloadable content games. There are tools to convert to and from this format. Using this format is **not** recommended as it can cause issues with certain games.

The `.cue` and `.bin` files are combined when compressed into a [CHD](:disk_image_compression#chd) file, so only the `.chd` file needs to be present and loaded. This is the recommended format.

Place your Sony PlayStation ROMs in `/userdata/roms/psx/`.

### Playing PAL copy-protected games
PAL copy protected games need a SBI subchannel file next to the `.bin`/`.cue`/`.chd` files in order to get past the copy-protection. For example:

```

Game (Europe).bin
Game (Europe).cue
Game (Europe).sbi

```

For proper PAL game compatibility, DuckStation should be set to show the BIOS animation, PCSX-ReARMED should be set to skip the BIOS animation (unless using a real BIOS) and Mednafen should be set to skip the BIOS animation (unless using a real BIOS).

### Multi-disc games
To automatically load the next disc of a game, you can use a `.m3u` playlist file. To make one, simply create a text file with the same filename as your intended game name (it could be anything, really). Within that text file, write the names of the `.cue` sheets or `.chd` files for your game discs. For instance, if your game's .cue sheets were structured like

```

roms/
└─ psx/
   ├─ Final Fantasy VII (Disc 1).cue
   ├─ Final Fantasy VII (Disc 1).bin
   ├─ Final Fantasy VII (Disc 2).cue
   ├─ Final Fantasy VII (Disc 2).bin
   ├─ Final Fantasy VII (Disc 3).cue
   └─ Final Fantasy VII (Disc 3).bin

```

you would put the following as text into the `Final Fantasy VII.m3u` text file:

```

Final Fantasy VII (Disc 1).cue
Final Fantasy VII (Disc 2).cue
Final Fantasy VII (Disc 3).cue

```

Save the text file with the file extension `.m3u` and place it in the `roms/psx/` folder along with the game's discs. When you get to the end of that disc, the next disc will be automatically loaded. If this fails, you can utilize Retroarch's 'Disc Control' menu in the Quick Menu ( `[HOTKEY]` +  in-game) to eject a disc and insert another (Swap Disc is for legacy purposes and should not be used). Refer to [multi-disc games](:cd_image_formats#multi-disc_games) for more info.

## Emulators
### DuckStation
[DuckStation](https://github.com/stenzek/duckstation) is focused on playability, speed, and long-term maintainability. The goal of the emulator is to be as accurate as possible while maintaining performance on a broad range of devices. "Hack" options are discouraged, and the default configuration should support all playable games with only some of the enhancements having compatibility issues. 64-bit CPUs are required for recompiler support for maximum performance.

Batocera uses the latest standalone version of Duckstation. Performs well on lower end x86_64 systems.

#### DuckStation configuration
Standardized features available to all cores of this emulator: `psx.videomode`, `psx.ratio`

| ES setting name `batocera.conf key` | Description => ES option `key value` |
| **REWIND `psx.duckstation_rewind`** | Creates savestates at set intervals to rewind back to. System requirements at native: (RAM%%|%%VRAM).\\ => Off `false`, Per 0.05s, 5s total (550MB%%|%%100MB) `5`, Per 0.1s, 10s total (1100MB%%|%%200MB) `10`, Per 1s, 15s total (165MB%%|%%30MB) `15`, Per 1s, 30s total (330MB%%|%%60MB) `30`, Per 1s, 60s total (660MB%%|%%120MB) `60`, Per 1s, 90s total (990MB%%|%%180MB) `90`, Per 1s, 120s total (1320MB%%|%%240MB) `120`. |
| **GRAPHICS API `psx.gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `OpenGL`, Vulkan `Vulkan`. |
| **CPU EXECUTION MODE `psx.duckstation_executionmode`** | Interpreter is the most accurate, but is the slowest.\\ => Recompiler (Fastest) `Recompiler`, Cached Interpreter (Faster) `CachedInterpreter`, Interpreter (Slowest) `Interpreter`. |
| **THREADED PRESENTATION `psx.duckstation_threadedpresentation`** | Improve performance if VSync is disabled and using Vulkan. Presents frames on a background thread when fast-forward or V-sync is disabled. Considerably improves performance if using Vulkan. If using V-sync, only improves fast-forward.\\ => Off `0`, On `1`. |
| **VSYNC `psx.duckstation_vsync`** | Turns on V-sync to avoid screen tearing. Introduces a negligible amount of input delay. Significant performance cost. Only should be disabled if experiencing slowdown.\\ => Off `0`, On `1`. |
| **FRAMESKIP `psx.duckstation_frameskip`** | Skip frames to improve performance, at the cost of choppy motion. Can cause motion sickness if enabled, only use if the game is unplayable without it.\\ => Off `0`, On `1`. |
| **SHOW BIOS BOOTLOGO `psx.duckstation_PatchFastBoot`** | Enhancement. Skips the BIOS boot animation. Some games require the animation to function correctly, most can skip it fine. Duckstation uses the official BIOS, some games look for this specific animation before booting so turn it on for those games.\\ => Off `1`, On `0`. |
| **RENDERING RESOLUTION `psx.duckstation_resolution_scale`** | Enhancement. Multiplies the internal rendering resolution. Improves the clarity of 3D objects. Extreme performance cost. Do note that some games would run at their own unique but similar resolutions. Therefore, the listed resolutions may not be 100% accurate.\\ => 1x(native) `1`, 2x `2`, 3x/720p `3`, 4x `4`, 5x/1080p `5`, 6x/1440p `6`, 7x `7`, 8x `8`, 9x/4K `9`, 10x `10`, 11x `11`, 12x `12`, 13x `13`, 14x `14`, 15x `15`, 16x `16`. |
| **ANTI-ALIASING (MSAA/SSAA) `psx.duckstation_antialiasing`** | Enhancement. Applies [MSAA](:anti-aliasing#multi-sample_anti-aliasing) or [SSAA](:anti-aliasing#super-sampling_anti-aliasing) to smooth out jagged edges on 3D object polygons. Most noticeable at lower resolutions. Does not affect textures. The sharp edges of polygons are usually masked by the blurry video output of the PSX, but digital displays may feature them more prominently. This can alleviate that. The PSX does not have any native anti-aliasing. Enabling this can cause rendering errors. Cheaper than multiplying the rendering resolution, but not by much.\\ => Off `1`, 2x MSAA `2`, 4x MSAA `4`, 8x MSAA `8`, 16x MSAA `16`, 32x MSAA `32`, 2x SSAA `2-ssaa`, 4x SSAA `4-ssaa`, 8x SSAA `8-ssaa`, 16x SSAA `16-ssaa`, 32x SSAA `32-ssaa`. |
| **TEXTURE FILTERING `psx.duckstation_texture_filtering`** | Enhancement. Applies [texture filtering](:anti-aliasing#texture_enhancement) to all textures. Minimal performance cost. `Nearest` for an authentic experience, `Bilinear` for a "neutral" improvement (think N64), `xBR`/`Jinc2` for smart upscaling (subjective improvement). Edge blending refers to the transparent edges, can make some objects look nicer while other objects look glitchier.\\ => Nearest-Neighbor `Nearest`, Bilinear `Bilinear`, Bilinear (no edge blending) `BilinearBinAlpha`, JINC2 `Jinc2`, JINC2 (no edge blending) `Jinc2BinAlpha`, xBR `xBR`, xBR (no edge blending) `xBRBinAlpha`. |
| **CROP MODE `psx.duckstation_CropMode`** | Zooms in the display to hide black borders. Not all PSX games have the same sized black borders.\\ => Off `None`, Only Overscan Area `Overscan`, All Borders `Borders`. |
| **WIDESCREEN HACK `psx.duckstation_widescreen_hack`** | Enhancement. Widescreen hack. Very glitchy. Only works when using a 16:9 video mode **and** with bezels (decorations) disabled. Recommended to use game patches where possible instead. Some games natively support 16:9 in their in-game options.\\ => Off `0`, On `1`. |
| **CONSOLE REGION `psx.duckstation_region`** | Changes the region of the emulated console. Region-locking is disabled so setting this isn't necessary, but some games will run at weird framerates if using out-of-region consoles. Duckstation will detect and switch to the right region unless specified otherwise.\\ => PAL `PAL`, NTSC-U/C `NTSC-U`, NTSC-J `NTSC-J`. |
| **FORCE NTSC TIMINGS ON PAL `psx.duckstation_60hz`** | Hack. Forces 50Hz PAL games to run at 60Hz. Has issues with most PAL games that tie framerate to logic, but certain PAL games (ones that use a variable FPS) should be fine.\\ => Off `0`, On `1`. |
| **CUSTOM TEXTURES `psx.duckstation_custom_textures`** | Enhancement. Uses the custom texture pack for the game, if any. `0` for off, `normal` to load from disk as needed, `preload` to load textures into RAM first (increases boot time). Safe to leave on if no texture pack is present.\\ => Off `0`, Normal `normal`, Preload `preload`. |
| **RUMBLE `psx.duckstation_rumble`** | Activates rumble on supported controllers. Requires the Dualshock controller, Namco GunCon or NeGcon and a compatible game.\\ => Off `0`, On `1`. |
| **JOYSTICK TO DPAD `psx.duckstation_digitalmode`** | Activates Joystick to D-pad, allowing the Joystick to function as a virtual D-pad. Useful for games that only support the digital controller.\\ => Off `0`, On `1`. |
| **MULTITAP `psx.duckstation_multitap`** | Enables multitap for the specified port(s). Not all games utilized it and may have issues with it on. Generally safe to leave on for port 2, though.\\ => Off `Disabled`, Port 1 `Port1Only`, Port 2 `Port2Only`, Port 1+2 `BothPorts`. |
| **CONTROLLER 1 TYPE `psx.duckstation_Controller1`** | Refer to [Controls.](systems:psx#controls)\\ => None `None`, Digital Controller `DigitalController`, Analog Controller (DualShock) `AnalogController`, Analog Joystick `AnalogJoystick`, Namco GunCon (Rumble) `NamcoGunCon`, PlayStation Mouse `PlayStationMouse`, NeGcon (Rumble) `NeGcon`. |
| **CONTROLLER 2 TYPE `psx.duckstation_Controller2`** | Same as above but for port 2. |

Other configuration settings must be configured from within DuckStation's standalone emu-config (`[F1]` on the systems list -> **Applications**).

DuckStation's Quick Menu can be opened up with `[HOTKEY]` + .

### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: PCSX ReARMed
[PCSX ReARMed](https://github.com/libretro/pcsx_rearmed) is an optimized PCSX fork for ARM based systems like the Raspberry Pi, but also works on x86.

##### libretro: PCSX ReARMed configuration
Standardized features for this core: `psx.autosave`, `psx.use_guns`, `psx.cheevos`

| ES setting name `batocera.conf key` | Description => ES option `key value` |
| **SHOW BIOS BOOTLOGO `psx.show_bios_bootlogo`** | Shows the BIOS boot animation when starting the game. In PCSX ReARMed, this can cause some games to break when turned on. PCSX uses an emulated BIOS by default, running *this* emulated BIOSs' animation can cause some games to malfunction. Games that require the proper BIOS animation require an official BIOS present.\\ => Off `disabled`, On `enabled`. |
| **FRAMESKIP `psx.frameskip_pcsx`** | Skip frames to improve performance. Can cause motion sickness if set to high values. Can cause motion sickness if set high. Only use if the game is unplayable without it.\\ => Off `0`, 1 `1`, 2 `2`, 3 `3`. |
| **ENHANCED RESOLUTION (SLOWER) `psx.neon_enhancement`** | (32-bit only) Enhancement. Doubles the internal rendering resolution. Extreme performance cost. "On (Speed hack)" is not recommended as it can cause glitches.\\ => Off `disabled`, On `enabled`, On (Speed hack) `enabled_with_speedhack`. |
| **MULTITAP `psx.pcsx_rearmed_multitap`** | Enables multitap on the selected port. Values: `disabled`, `port1`, `port2` or `port12` for both ports. Most games don't utilize multitap, but is generally safe to leave in port2.\\ => Off `disabled`, Port1 `port 1 only`, Port2 `port 2 only`, Port1+2 `both`. |
| **ADDITIONAL GAME FIXES `psx.game_fixes_pcsx`** | Enables a per-game fix.\\ => Off `disabled`, Capcom VS games Expand Screen Width `Capcom_fighting`, Chrono Chross Odd/Even Bit Hack `Chrono_Chross`, Dark Forces Flat Tex Triangles Fix `Dark_Forces`, Diablo Music Fix `Diablo_Music_Fix`, Lunar Ignore Brightness Color Fix `Lunar`, InuYasha Sengoku Battle Fix `InuYasha_Sengoku`, Pandemonium 2 Lazy Screen Update Fix `Pandemonium`, Parasite Eve 2/Vandal Hearts 1&2 Fix `Parasite_Eve`. |
| **CONTROLLER 1 TYPE `psx.controller1_pcsx`** | Refer to [Controls](systems:psx#controls).\\ => Digital Controller `1`, Analog Controller `261`, DualShock Controller `517`, Namco GunCon `260`, NeGcon `773`, PlayStation Mouse `258`. |
| **CONTROLLER 2 TYPE `psx.controller2_pcsx`** | Same as above but for port 2.\\ => Digital Controller `1`, Analog Controller `261`, DualShock Controller `517`, Namco GunCon `260`, NeGcon `773`, PlayStation Mouse `258`. |

Other configuration settings must be configured from RetroArch's Quick Menu (Hotkey+).

#### libretro: SwanStation
[SwanStation](https://github.com/kivutar/swanstation#libretro-core) is a port of an older version of DuckStation to a libretro core. This version does not receive the same upstream patches that DuckStation currently does, so as time goes on the feature set between this and DuckStation will diverge further.

SwanStation shares its configuration with [Duckstation](systems:psx#duckstation), but omits `threaded_presentation`, `vsync`, `frameskip`, `region`, `custom_textures`, `rumble`, `digital_mode` and `multitap`.

##### libretro: SwanStation configuration
Standardized features for this core: `psx.autosave`, `psx.cheevos`

| ES setting name `batocera.conf key` | Description => ES option `key value` |
| **SHOW BIOS BOOTLOGO `psx.duckstation_PatchFastBoot`** | Enhancement. Skips the BIOS boot animation. Some games require the animation to function correctly, most can skip it fine. SwanStation uses the official BIOS, some games look for this specific animation before booting so turn it on for those games.\\ => Off `true`, On `false`. |
| **USE SOFTWARE RENDERING `psx.gpu_software`** | More accurate emulation, but slower.\\ => Off `False`, On `True`. |
| **RENDERING RESOLUTION `psx.duckstation_resolution_scale`** | Enhancement. Multiplies the internal rendering resolution. Improves the clarity of 3D objects. Extreme performance cost. Do note that some games would run at their own unique but similar resolutions. Therefore, the listed resolutions may not be 100% accurate.\\ => 1x (native) `1`, 2x `2`, 3x (720p) `3`, 4x `4`, 5x (1080p) `5`, 6x (1440p) `6`, 7x `7`, 8x `8`, 9x `9`. |
| **ANTI-ALIASING (MSAA/SSAA) `psx.duckstation_antialiasing`** | Enhancement. Applies [MSAA](:anti-aliasing#multi-sample_anti-aliasing) or [SSAA](:anti-aliasing#super-sampling_anti-aliasing) to smooth out jagged edges on 3D object polygons. Most noticeable at lower resolutions. Does not affect textures. The sharp edges of polygons are usually masked by the blurry video output of the PSX, but digital displays may feature them more prominently. This can alleviate that. The PSX does not have any native anti-aliasing. Enabling this can cause rendering errors. Cheaper than multiplying the rendering resolution, but not by much.\\ => Off `1`, 2x MSAA `2`, 4x MSAA `4`, 8x MSAA `8`, 16x MSAA `16`, 32x MSAA `32`, 2x SSAA `2-ssaa`, 4x SSAA `4-ssaa`, 8x SSAA `8-ssaa`, 16x SSAA `16-ssaa`, 32x SSAA `32-ssaa`. |
| **TEXTURE FILTERING `psx.duckstation_texture_filtering`** | Enhancement. Applies [texture filtering](:anti-aliasing#texture_enhancement) to all textures. Minimal performance cost. `Nearest` for an authentic experience, `Bilinear` for a "neutral" improvement (think N64), `xBR`/`Jinc2` for smart upscaling (subjective improvement). Edge blending refers to the transparent edges, can make some objects look nicer while other objects look glitchier.\\ => Nearest `Nearest`, Bilinear `Bilinear`, JINC2 `JINC2`, xBR `xBR`. |
| **WIDESCREEN HACK `psx.duckstation_widescreen_hack`** | Enhancement. Widescreen hack. Very glitchy. Only works when using a 16:9 video mode **and** with bezels (decorations) disabled. Recommended to use game patches where possible instead. Some games natively support 16:9 in their in-game options.\\ => Off `false`, On `true`. |
| **CROP MODE `psx.duckstation_CropMode`** | Zooms in the display to hide black borders. Not all PSX games have the same sized black borders.\\ => Off `None`, Only Overscan Area `Overscan`, All Borders `Borders`. |
| **CONTROLLER 1 TYPE `psx.duckstation_Controller1`** | Refer to [Controls.](systems:psx#controls)\\ => None `None`, Digital Controller `DigitalController`, Analog Controller (DualShock) `AnalogController`, Namco GunCon `NamcoGunCon`, PlayStation Mouse `PlayStationMouse`, NeGcon `NeGcon`. |
| **CONTROLLER 2 TYPE `psx.duckstation_Controller2`** | Same as above but for port 2.\\ => None `None`, Digital Controller `DigitalController`, Analog Controller (DualShock) `AnalogController`, Namco GunCon `NamcoGunCon`, PlayStation Mouse `PlayStationMouse`, NeGcon `NeGcon`. |

In older Batocera versions, these settings can only be adjusted with RetroArch's Quick Menu (`[HOTKEY]` + ).

#### libretro: Duckstation

This libretro core has been abandoned and thus removed from Batocera **v34** onwards. Use one of the alternatives, or just [the regular standalone version](#duckstation).

A port of DuckStation as a libretro core. Is mostly the same as [DuckStation standalone](#duckstation) but conforms to the limitations of being a libretro core.

--> Old libretro: DuckStation configuration (for older Batocera versions which still had it)#

Standardized features for this core: `psx.autosave`, `psx.cheevos`

| ES setting name `batocera.conf key` | Description => ES option `key value` |
| **SHOW BIOS BOOTLOGO `psx.duckstation_PatchFastBoot`** | Enhancement. Skips the BIOS boot animation. Some games require the animation to function correctly, most can skip it fine. Duckstation uses the official BIOS, some games look for this specific animation before booting so turn it on for those games.\\ => Off `true`, On `false`. |
| **USE SOFTWARE RENDERING `psx.gpu_software`** | More accurate emulation, but slower.\\ => Off `False`, On `True`. |
| **RENDERING RESOLUTION `psx.duckstation_resolution_scale`** | Enhancement. Multiplies the internal rendering resolution. Improves the clarity of 3D objects. Do note that some games would run at their own unique but similar resolutions. Therefore, the listed resolutions may not be 100% accurate. Extreme performance cost.\\ => 1x (native) `1`, 2x `2`, 3x (720p) `3`, 4x `4`, 5x (1080p) `5`, 6x (1440p) `6`, 7x `7`, 8x `8`, 9x `9`. |
| **ANTI-ALIASING (MSAA/SSAA) `psx.duckstation_antialiasing`** | Enhancement. Applies [MSAA](:anti-aliasing#multi-sample_anti-aliasing) or [SSAA](:anti-aliasing#super-sampling_anti-aliasing) to smooth out jagged edges on 3D object polygons. Most noticeable at lower resolutions. Does not affect textures. The sharp edges of polygons are usually masked by the blurry video output of the PSX, but digital displays may feature them more prominently. This can alleviate that. The PSX does not have any native anti-aliasing. Enabling this can cause rendering errors. Cheaper than multiplying the rendering resolution, but not by much.\\ => Off `1`, 2x MSAA `2`, 4x MSAA `4`, 8x MSAA `8`, 16x MSAA `16`, 32x MSAA `32`, 2x SSAA `2-ssaa`, 4x SSAA `4-ssaa`, 8x SSAA `8-ssaa`, 16x SSAA `16-ssaa`, 32x SSAA `32-ssaa`. |
| **TEXTURE FILTERING `psx.duckstation_texture_filtering`** | Enhancement. Applies [texture filtering](:anti-aliasing#texture_enhancement) to all textures. Minimal performance cost. `Nearest` for an authentic experience, `Bilinear` for a "neutral" improvement (think N64), `xBR`/`Jinc2` for smart upscaling (subjective improvement).\\ => Nearest `Nearest`, Bilinear `Bilinear`, JINC2 `JINC2`, xBR `xBR`. |
| **WIDESCREEN HACK `psx.duckstation_widescreen_hack`** | Enhancement. Widescreen hack. Very glitchy. Only works when using a 16:9 video mode **and** with bezels (decorations) disabled. Recommended to use game patches where possible instead. Some games natively support 16:9 in their in-game options.\\ => Off `false`, On `true`. |
| **CROP MODE `psx.duckstation_CropMode`** | Zooms in the display to hide black borders. Not all PSX games have the same sized black borders.\\ => Off `None`, Only Overscan Area `Overscan`, All Borders `Borders`. |
| **CONTROLLER 1 TYPE `psx.duckstation_Controller1`** | Refer to [Controls.](systems:psx#controls)\\ => None `None`, Digital Controller `1`, Analog Controller (DualShock) `5`, Analog Stick `517`, Namco GunCon `260`, PlayStation Mouse `258`, NeGcon `773`. |
| **CONTROLLER 2 TYPE `psx.duckstation_Controller2`** | Same as above but for port 2.\\ => None `None`, Digital Controller `1`, Analog Controller (DualShock) `5`, Analog Stick `517`, Namco GunCon `260`, PlayStation Mouse `258`, NeGcon `773`. |

<--

#### libretro: Mednafen_PSX
[Beetle PSX](https://github.com/libretro/beetle-psx-libretro) is a standalone fork of Mednafen PSX core to the libretro API. Offers a lot of options to enhance graphics and geometry. Highly recommended for x86_64 systems with a decent GPU.

##### libretro: Mednafen_PSX configuration
Standardized features for this core: `psx.autosave`, `psx.cheevos`

| ES setting name `batocera.conf key` | Description => ES option `key value` |
| **SHOW BIOS BOOTLOGO `psx.beetle_psx_skip_bios`** | Enhancement. Skip the BIOS animation when starting content. Can be enabled but some games may have issues, notably [copy protected PAL games](systems:psx#playing_pal_copy_protected_games).\\ => Off `enabled`, On `disabled`. |
| **OVERCLOCKING (CPU HEAVY) `psx.beetle_psx_cpu_freq_scale`** | Enhancement. Enable overclocking (or underclocking) of the emulated PSX's CPU. The default frequency of the MIPS R3000A-compatible 32-bit RISC CPU is 33.8688 MHz; running at higher frequencies can eliminate slowdown and improve frame rates in certain games at the expense of increased performance requirements. Overclocking can lead to audio and video desynchronization on certain games, underclocking can improve performance on weak devices.\\ => 50% `50%`, 60% `60%`, 70% `70%`, 80% `80%`, 90% `90%`, 100%(native) `100%(native)`, 110% `110%`, 120% `120%`, 130% `130%`, 140% `140%`, 150% `150%`, 160% `160%`, 170% `170%`, 180% `180%`, 190% `190%`, 200% `200%`, 250% `250%`, 300% `300%`, 350% `350%`, 4000% `400%`, 450% `450%`, 500% `500%`, 550% `550%`, 600% `600%`, 650% `650%`, 700% `700%`, 750% `750%`. |
| **RENDERING RESOLUTION `psx.beetle_psx_internal_resolution`** | Enhancement. [Increases the rendering resolution for 3D geometry.](:anti-aliasing#psx_3d_enhancement) 2D elements are generally unaffected by this setting from the core's perspective. Significant performance cost. Do note that some games would run at their own unique but similar resolutions. Therefore, the listed resolutions may not be 100% accurate. Although not exact, set to 4x for 1080p resolution.\\ => 1x(native) `1x(native)`, 2x `2x`, 4x `4x`, 8x `8x`, 16x `16x`. |
| **WIDESCREEN HACK (GLITCHY) `psx.beetle_psx_widescreen_hack`** | Enhancement. Forces content to be rendered with an aspect ratio of 16:9. Produces best results with fully 3D games. Can cause graphical glitches or alignment/stretching issues in games that mix 3D and 2D elements. Recommended to use game patches instead. Some games natively support 16:9 in their in-game options.\\ => Off `disabled`, On `enabled`. |
| **FRAME DUPING (SPEED UP) `psx.beetle_psx_frame_duping`** | Enhancement. When enabled, provides a small performance increase by redrawing/reusing the last rendered frame (instead of presenting a new one) if the content of the current frame is unchanged based on the internal fps heuristic. Enabling may cause inaccurate behavior or lost animation frames.\\ => Off `disabled`, On `enabled`. |
| **CPU DYNAREC (SPEED UP) `psx.beetle_psx_cpu_dynarec`** | Dynamically recompile CPU instructions to native instructions. Much faster than interpreter, but CPU timing is less accurate, and may have bugs. Extreme performance cost if disabled. Only enable if on a weak device.\\ => Disabled (Beatle Interpreter) `disabled`, Max Performance `execute`, Cycle Timing Check `execute_once`, Lightrec Interpreter `run_interpreter`. |
| **DYNAREC CODE INVALIDATION `psx.beetle_psx_dynarec_invalidate`** | Switches between full invalidation mode and DMA only mode. DMA only mode is slightly faster, however some games require full invalidation to run correctly. This option has no effect when `beetle_psx_cpu_dynarec` is not enabled. Only use `dma` on weak devices.\\ => Full `full`, DMA Only (Slightly Faster) `dma`. |
| **MULTITAP `psx.multitap_mednafen`** | Enables/disables multitap functionality and allows up to 8 players. Not all games utilized it and may have issues with it on. Generally safe to leave on for port 2, though.\\ => Off `disabled`, Port 1 `port1`, Port 2 `port2`, Port 1+2 `port12`. |
| **CONTROLLER 1 TYPE `psx.beetle_psx_Controller1`** | Refer to [Controls.](systems:psx#controls)\\ => Digital Controller `1`, Analog Controller `261`, DualShock Controller `517`, Analog Joystick (Flystick) `773`, Namco GunCon `260`, NeGcon `1029`, PlayStation Mouse `258`. |
| **CONTROLLER 2 TYPE `psx.beetle_psx_Controller2`** | Use DualShock type for games with Rumble mode\\ => Digital Controller `1`, Analog Controller `261`, DualShock Controller `517`, Analog Joystick (Flystick) `773`, Namco GunCon `260`, NeGcon `1029`, PlayStation Mouse `258`. |

Other configuration settings must be configured from RetroArch's **Quick Menu** ( `[HOTKEY]` + ).

## Controls

The PlayStation had many types of controllers throughout its life, starting with the digital controller which only had a D-pad, face buttons and shoulder buttons, then the Analog controller which added two joysticks to the center and finally the DualShock which added vibration. A game needs to explicitly support a controller to function with it, most supported at least the digital controller. The Analog and Dualshock controller had an "Analog" button to switch between being its native self or a virtual digital controller so it could function with older games; this is generally not emulated yet so the best recommendation is to stick with digital controllers unless you know your game explicitly supports a later one. By default, Batocera will enable Joystick to D-pad so that the joystick will function as a virtual D-pad.

The PlayStation also had alternative controllers such as the dance mat (same as the digital controller) or the [analog joystick](wp>PlayStation_Analog_Joystick) (same as the analog controller). Other controllers such as the [Namco GunCon](wp>GunCon), the [neGcon](wp>NeGcon) or the [PlayStation Mouse](wp>PlayStation_Mouse) would use their own interface, requiring the game to specifically support it.

The default button mapping to the PSX controller is as follows: