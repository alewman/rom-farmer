# Nintendo 3DS

**Source:** https://wiki.batocera.org/systems:3ds  
**Last fetched:** 2025-12-06 16:18:30

---

# Nintendo 3DS
The [Nintendo 3DS](wp>Nintendo_3DS) is a portable developed by Nintendo. It was released in March, 2011 for $249 USD. The original model featured a dual-core ARM11 MPCore at 268 MHz and a single-core ARM9 CPU, with 128MB of RAM.

It was known for its gimmicky display; an autostereoscopic panel that would allow users to perceive 3D images without the need of any special glasses, as long as you were looking at the device straight-on. You could kind of think of it like those special edition cards that switched image based on what angle you looked at them from, but only for your left and right eyes. The function could be turned off via a slider on the right side of the screen, requiring games to support both 3D and 2D modes (some games would even alter performance settings based on this, such as increased framerates). Later models opted to use a regular 2D display instead. Nintendo advised for young children not to use the 3DS's stereoscopic mode (though it is speculated that said advisories were more for liability reasons in case of a health-related lawsuit and not so much any serious concern).

The later releases of the console that prepended the "New" word to its name use a more powerful 804 MHz quad-core ARM11 CPU and 256MB of RAM. It also featured additional shoulder buttons (ZL/ZR) and a C-stick, however no game *required* these controls to function. Not all games, especially older ones, even support these extra controls. These additional controls could be retroactively added to an original model via the use of the [Circle Pad Pro accessory](wp>Nintendo_3DS#Circle_Pad_Pro).

This system scrapes metadata for the "3ds" group and loads the `3ds` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.3ds`, `.3dsx`, `.cxi`, `.axf`, `.elf`
- **Folder:** `/userdata/roms/3ds`

| Emulators |
| [Citra](#citra) |
| [libretro: Citra](#libretro:_citra) |

## BIOS
No Nintendo 3DS emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Nintendo 3DS ROMs in `/userdata/roms/3ds`.

3DS ROMs are fairly complicated, due to both the dumping methods employed, the way the console reads or installs the software and the requirement for decryption/keys for encrypted titles.

There are two overarching types of 3DS ROMs, most alternative formats are derived from these:
- **NCSD-type** Literally just the data extracted from the cart. These typically come in the `.cci` (a.k.a. `.3ds`) format.
- **NCCH-type** The installation packages that the 3DS uses to install software onto its internal NAND storage. These typically come in the `.cia` and `.cxi` formats. Digital games were often distributed only as CIAs.

Converting a CIA image to 3DS format (and vice-versa) is possible without loss of content. This is outside of the scope of Batocera's support channels/this wiki, Google is your friend.

### Encryption
To add to the confusion, either of these formats can be encrypted or decrypted, with no clear indication of what it is based on its extension. Batocera recommends working with decrypted ROMs only, however it is possible to configure Citra to [use AES keys](https://citra-emu.org/wiki/aes-keys/) to read encrypted ROMs. The AES keys file is read from `/userdata/saves/3ds/citra-emu/sysdata/`.

Extracting the files from a real 3DS is outside of the scope of Batocera's support channels/this wiki. Refer to [Citra's FAQ](https://citra-emu.org/wiki/faq/) for more info.

## Emulators
### Citra
The "big" open-source 3DS emulator. Technically still experimental software, it's capable of running a large portion of the 3DS library at acceptable speeds.

Citra currently can't emulate any of the 3DS's online features aside from LAN multiplayer. Batocera does not support the automatic configuration of LAN multiplayer, you're on your own if you want to achieve this.

#### Citra configuration
Standardized features available to all cores of this emulator: `3ds.videomode`, `3ds.ratio`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **SCREEN LAYOUT `3ds.citra_screen_layout`** | Allows you to arrange the DS screens\\ => top/bottom `4-false`, bottom/top `4-true`, left/right `3-false`, right/left `3-true`, top only `1-false`, bottom only `1-true`, hybrid top ratio 4 `2-false`, hybrid bottom ratio 4 `2-true`. |
| **VIDEO RESOLUTION `3ds.citra_resolution_factor`** | Improve the fidelity of 3D models (does not affect 2D sprites)\\ => Native (400x240) `1`, 2x (800x480) `2`, 3x (1200x720) `3`, 4x (1600x960) `4`, 5x (2000x1200) `5`, 6x (2400x1440) `6`, 7x (2800x1680) `7`, 8x (3200x1920) `8`, 9x (3600x2160) `9`, 10x (4000x2400) `10`. |
| **VSYNC `3ds.use_vsync_new`** | Fix the heavy screen tearing in games (CPU heavy)\\ => Off `0`, On `1`. |
| **FRAME LIMIT `3ds.citra_use_frame_limit`** | Off will help some games, others will run too fast\\ => Off `0`, On `1`. |
| **DISK SHADER CACHE `3ds.citra_use_disk_shader_cache`** | Reduce stutter that happens when building shader\\ => Off `0`, On `1`. |
| **CUSTOM TEXTURES `3ds.citra_custom_textures`** | Use HD Texture Pack (preloading is impossible from ES)\\ => Off `0`, On `1-normal`. |
| **IS NEW 3DS `3ds.citra_is_new_3ds`** | The New 3DS has a faster processor, ZL/ZR buttons and C-Stick\\ => Off `0`, On `1`. |

### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

Standardized features available to all libretro cores: `3ds.videomode`, `3ds.ratio`, `3ds.smooth`, `3ds.shaders`, `3ds.pixel_perfect`, `3ds.decoration`, `3ds.game_translation`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS BACKEND `3ds.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `opengl`, Vulkan `vulkan`. |
| **AUDIO LATENCY `3ds.audio_latency`** | Audio latency in milliseconds, turn it up if you hear crackles\\ => 256 `256`, 192 `192`, 128 `128`, 64 `64`, 32 `32`, 16 `16`, 8 `8`. |
| **THREADED VIDEO `3ds.video_threaded`** | Improves performance at the cost of latency and more video stuttering. Use only if full speed cannot be obtained otherwise.\\ => On `true`, Off `false`. |

#### libretro: Citra

FIXME

##### libretro: Citra configuration
## Controls
Here are the default Nintendo 3DS's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### "Could not Determine System Mode" or "Failed to Decrypt"
Citra does not officially support booting [encrypted](#encryption) games, but can [use AES keys](https://citra-emu.org/wiki/aes-keys/) to read them correctly. It is usually easier to just use decrypted backups.

Extracting the files from a real 3DS is outside of the scope of Batocera's support channels/this wiki. Refer to [Citra's FAQ](https://citra-emu.org/wiki/faq/) for more info.

### I'm having (X) issue with (Y) game
Refer to the entirety of [Citra's FAQ page](https://citra-emu.org/wiki/faq/) first.

If you've already done so, and you're sure that the issue is not related to Batocera itself, refer to [Citra's help section](https://citra-emu.org/help/) on their website.

### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).