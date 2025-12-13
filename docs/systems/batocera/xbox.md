# Microsoft Xbox

**Source:** https://wiki.batocera.org/systems:xbox  
**Last fetched:** 2025-12-06 16:20:05

---

# Microsoft Xbox
The Xbox is a sixth-generation console released by Microsoft on November 15, 2001. Known as the DirectXbox during development, it is notable for the specs having similarities to a PC, namely as a result of using familiar components around the x86 architecture. It had a custom Pentium III CPU at 733 MHz with 64 MB of RAM, and a custom Nvidia GPU codenamed NV2A at 233 MHz. The Xbox was often said to be the most powerful console from the sixth generation, and Sega later designed the Chihiro arcade system with the same components. It retailed at $299.99. 

This system scrapes metadata for the "xbox" group(s) and loads the `xbox` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [xemu](#xemu)
- **Folder:** `/userdata/roms/xbox`
- **Accepted ROM formats:** `.iso`, `.squashfs`

## BIOS
The following BIOS files are required:

| MD5 checksum | Share file path | Description |
| `d49c52a4102f6df7bcf8d0617ac475ed` | `bios/mcpx_1.0.bin` | MCPX Boot ROM Image |
| `39cee882148a87f93cb440b99dde3ceb` | `bios/Complex_4627.bin` | Flash ROM Image (BIOS) |

That's all that's required to boot into games.

In addition to these, it is also possible to use the HDD image of the Xbox itself (the Xbox *came with* a HDD which it would store its firmware on, starting a trend that would soon become common) in place of the pre-installed dummy drive.

Fortunately, the original Xbox uses a bog-standard hard-drive that you can just connect to your computer and clone:

  - Unlock your drive
  - Connect it to a computer
  - Use a cloning application like `dd` to clone the entire contents of the drive straight to a file

This file can be used as-is.

[These instructions have been summarized from Xemu's official documentation on it.](https://xemu.app/docs/required-files/)

Alternatively, you can use a dummy [hard-drive image](https://github.com/mborgerson/xemu-hdd-image/releases/latest/download/xbox_hdd.qcow2.zip). Games can still be launched using this, though it may cause an error prompt to appear when the official BIOS attempts to access it due to it being unsigned.

If using a dummy image, you can install a custom dashboard into it such as [NevolutionX](https://github.com/dracc/nevolutionx). This is not necessary but may improve the user experience.

## ROMs
Place your Xbox ROMs in `/userdata/roms/xbox/`.

ISO files must be in the XISO format. It is not directly compatible with the original disc image, only the game partition. It is possible to extract the game partition of an original disc image with [extract-xiso](https:*github.com/XboxDev/extract-xiso) on a [Windows](https:*github.com/XboxDev/extract-xiso/releases) or [Linux](https://sourceforge.net/projects/extract-xiso/files/extract-xiso%20binaries/) PC:

- If using an image dump of the entire disc (usually the case with Redump), run the command ```

extract-xiso -r game-redump.iso

``` to rewrite the filesystem structure of the image. The resulting `game-redump.iso` can immediately be used with xemu, with the original version being renamed to `game-redump.iso.old`.
- If using a folder with just the game's contents (usually the result from an FTP transfer from the original Xbox), run the following: ```

extract-xiso -c game-folder

``` The resulting `game-folder.iso` image can immediately be used with xemu.

For example, if creating the Halo 2 game for use with xemu from a folder containing just the game's extracted files:

```

extract-xiso -c halo-2

```

The following batch script can be used to automate the process. Put this in the same directory as `extract-iso.exe` and the game's ISO:

```

for /r %%i in (*.iso) do extract-xiso.exe -r "%%i"

```

There have been some cases reported where the Linuxversion of extract-iso does not work while the Windows version does. The Windows version can be run in Linux via WINE: `wine extract-xiso.exe -r "game.iso"`

In case the Github link is down, you can also download an older version of it from the author's [Sourceforge page](https://sourceforge.net/projects/extract-xiso/).

There may tools out there aimed at creating images to be burned to smaller capacity DVDs designed for running on hacked Xbox consoles. Use of these tools is not recommended, as it is not compatible with many titles.

More information about this can be found on [xemu's wiki page about disc images](https://xemu.app/docs/disc-images/).

### Squashfs format
If you want to compress the your (x)iso rom file, use Squashfs [https://wiki.batocera.org/disk_image_compression#squashfs](https://wiki.batocera.org/disk_image_compression#squashfs). For example on Linux:

```

mksquashfs "OutRun 2006 - Coast 2 Coast (USA, Europe) (En,Fr,De,Es,It).iso" "OutRun 2006 - Coast 2 Coast (USA, Europe) (En,Fr,De,Es,It).iso.squashfs"

```

The extension has to be `.iso.squashfs`, otherwise you'll get  `file driver requires /var/run/squashfs/<rom> to be a regular file` 

## Emulators
### xemu
[xemu](https://xemu.app) is a free and open-source low-level Xbox emulator continuing much of the work done on XQEMU. It focuses on stability, performance, and ease of use. While still in an early stage it already runs a lot of commercial games. Xemu benefits greatly from having a high CPU core count, having at least four can dramatically improve emulation speed.

We use the latest [xemu](https://github.com/mborgerson/xemu) release.

#### xemu configuration
Standardized features available to all cores of this emulator: `xbox.videomode`, `xbox.videomode`, `xbox.bezel`, `xbox.bezel_stretch`, `xbox.hud`, `xbox.hud_corner`, `xbox.bezel.tattoo`, `xbox.bezel.tattoo_corner`, `xbox.bezel.tattoo_file`, `xbox.bezel.resize_tattoo`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **SCALING MODE `xbox.scaling`** | Choose the scaling mode for the game screen. Set it to stretch if you want to a fullscreen experience, or Widescreen if playing on a 16:9 screen. Will not upscale the resolution.\\ => Original resolution `center`, Scale to best fit `scale`, Stretch to full `stretch`, Stretch to 16:9 `scale_ws169`. |
| **RENDERING RESOLUTION `xbox.render`** | Choose the scaling render multiplier. 640x480 is native.\\ => x1 (640x480) `1`, x2 (1280x960) `2`, x3 (1920x1440) `3`, x4 (2560x1920) `4`, x5 (3200x2400) `5`, x6 (3840x2880) `6`, x7 (4480x3360) `7`, x8 (5120x3840) `8`. |
| **SKIP BOOT BOOTLOGO `xbox.xemu_bootanim`** | Enhancement. Skip the on-boot Xbox animation. Disabling should be safe, if you don't want to see the famous animation.\\ => Show `false`, Skip `true`. |

## Graphical Settings
### Via the Dashboard
By default, the games will display in 480i (interlaced) resolution. But the Xbox was a powerfull console, able to output in 480p, 720p and 1080i, in 4:3 or 16:9 ratios, depending on the game (see [https://en.everybodywiki.com/List_of_Xbox_games_with_alternate_display_modes](https://en.everybodywiki.com/List_of_Xbox_games_with_alternate_display_modes) for a list of supported modes). The vast majority of games support at least 480p.

This has to be enabled via the Dashboard. If you didn't dump the original dashboard from your console, you can use the [NevolutionX dashboard](https://github.com/dracc/NevolutionX):
- Download the latest iso
- Launch it
- In `Settings > Video`, change:
     *  `Screen Ratio` to `Widescreen`
     * `480p` to `Yes`
     * `720p` to `Yes` (may cause visual glitches depending on the game)
     * Leave `1080i` to `No` as very few games support it and the interlacing can cause many problems.
- Then go back to the main menu and choose: `Power off`
### 16:9 (Widescreen) games
Many games supporting 16:9 ratio are using anamorphic widescreen. To display them correctly, you should change the aspect ratio from `Auto` to `16x9` in the advanced options of the emulator. Note that some elements may display strangely: OutRun 2 stretches the selection menus (coming from the arcade version) but has a correct display while racing.

## Access the internal HDD (containing save files)
The xbox hard disk image is saved here: `/userdata/saves/xbox/xbox_hdd.qcow2` but in a format that is not easy to access.

Extensive information can be found at [https://consolemods.org/wiki/Xbox:Original_Xbox_Mods_Wiki](https://consolemods.org/wiki/Xbox:Original_Xbox_Mods_Wiki)

Most tutorials recommend running a ftp server on xemu to access the files such as [the official xemu doc](https://xemu.app/docs/networking/). This can be tricky on batocera.

Another (easier ?) way which works fine on batocera, is to use a ftp client on xemu to access a ftp server located in your Lan. Android phones, for example, have plenty of applications allowing you to quickly set up a ftp server to share files. This will allow you to upload/download your game saves. Here is the procedure:

### Installing an alternate dashboard with a ftp client
#### Activate networking access in xemu
  - Launch any game with xemu
  - Press your Hotkey Button to bring the xemu menu. Then `Settings`>`All settings`>`Network`>`Enable` . The adapter is attached to `NAT`. No need to do any port forwarding.
#### Run a separate ftp server
  - On another device (computer, smartphone,...) install and run a Ftp server. For example, Android phones have a lot of applications to get this up and running very quickly.
#### Install a ftp client
  - To install the ftp client, you can download a ready-to-use iso from [https://github.com/Rocky5/Xbox-Softmodding-Tool](https://github.com/Rocky5/Xbox-Softmodding-Tool). Make sure to download the `Xbox Softmodding Tool Extras Disc.iso`
  - Launch this iso with xemu
  - `Install Dashboards` > `UnleashX` > `Install as dashboard to: E:\Dashboard\`
  - Once it's done, go back to the main menu and choose: `Advanced Menu: Enter Menu` > `File Manager`.
  - Navigate to `E:\Dashboard\default.xbe`: this will launch UnleashX
  - Go all the way down to `System`>`File Explorer`. Press `start` on the gamepad and go down to `Switch to FTP Browser`. Another press on `start` allows you to enter the details about the server.
  - The save files are located in `E:\UDATA` (sometimes also in `E:\TDATA`)

## Lan and Online Gaming
### System Link
System Link is a form of offline multiplayer gaming on the Xbox and Xbox 360 gaming consoles over a LAN (local area network). Wikipedia has a [list of supported titles](https://en.wikipedia.org/wiki/List_of_Xbox_System_Link_games). The option is sometimes buried deeply (ex: in OutRun2, it lays in OutRun Challenge > Race Mode > System Link).

#### Easy way: use a public server
Using an existing server allows you to play with other users on the same Lan, or on the Internet as if you were on the same LAN:
- us-west-1.lan.xemu.app:9938
- us-east-1.lan.xemu.app:9938
- de-1.lan.xemu.app:9938

Change your Network settings by pressing `Hotkey`, then `Network` > `UDP Tunnel`
- Remote address: de-1.lan.xemu.app:9938
- Bind Address: 0.0.0.0:9938

Alternatively, you can edit directly the `/userdata/system/configs/xemu/xemu.toml` file:
```

[net]
enable = true
backend = 'udp'

[net.udp]
bind_addr = '0.0.0.0:9938'
remote_addr = 'de-1.lan.xemu.app:9938'

```

#### A bit harder: host your own local server
It's also possible to use your own server (see some documentation here https://github.com/mborgerson/l2tunnel/issues/4 ) if you want to locally connect several computers (and even real xbox consoles) running xemu.

### Xbox Live
It offers a completely different approach. The service was shut down by Micrososft in 2010. Some projects, such as insignia, exist to offer replacement servers.

## Controls
Here are the default Microsoft XBOX's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### My games are all in French!
Actually this can be any language, but French seems to be *more common*.

It is recommended to properly set your language on your original Xbox and extract the BIOS files again. As long as your Xbox has the correct language set, it will use that language.

It would be weird if you were using a BIOS for another Xbox, wouldn't it?

If for some reason you aren't able to set the language from your Xbox, you can
- directly edit the EEPROM settings on the hard-drive image using [Ernegien's Original Xbox EEPROM Editor](https://github.com/Ernegien/XboxEepromEditor). The EEPROM can be found at `/userdata/saves/xbox/xemu_eeprom.bin`.
- or use the [NevolutionX dashboard](https://github.com/dracc/NevolutionX) to change the language settings.

### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).