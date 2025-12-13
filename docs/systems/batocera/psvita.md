# PlayStation Vita

**Source:** https://wiki.batocera.org/systems:psvita  
**Last fetched:** 2025-12-06 16:19:39

---

# PlayStation Vita
The PlayStation Vita is a console developed by Sony. It was released in 2011. As of writing, it is the last *dedicated* handheld console released.

The Vita was the successor to the PlayStation Portable and was backwards compatible with its software, but due to lacking a disc drive it could not play its physical discs (the Vita would use cartridges for its titles instead). The Vita features a quad-core ARM Cortex-A9 MPCore CPU paired with a quad-core SGX543MP GPU. The system, like the PSP before it, had multiple revisions and re-releases, before its eventual discontinuation in 2019. Despite this, it still has a strong following due to its homebrew scene, with software still being developed for it to this day.

PS Vita emulation is still very experimental and only a few select titles work. Do not expect great performance either.

Right now, the PS Vita emulator is only available on x86_64 platforms.

This system scrapes metadata for the "psvita" group(s) and loads the `psvita` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [Vita3K](#vita3k)
- **Folder:** `/userdata/roms/psvita`
- **Accepted ROM formats:** `.psvita`, `.zip` (Mai dump format)

## BIOS
Games require the PS Vita's system modules. These are stored as two files on PlayStation's update server:
- [PS Vita base system software](https://www.playstation.com/en-us/support/hardware/psvita/system-software/)
- [PS Vita system update](http://dus01.psp2.update.playstation.net/update/psp2/image/2022_0209/sd_59dcf059d3328fb67be7e51f8aa33418/PSP2UPDAT.PUP)

Once both are downloaded, transfer them to Batocera at `/userdata/bios/psvita`. Then, on Batocera, press `[F1]` on the system list and go to **Applications** -> **vita3k-emu-config** to open the emulator.

You will need a mouse or trackpad for the initial configuration of the emulator.

First time you launch this application, you will be asked for the language you want to use. Then, keep the default path that is given to you through the wizard (current emulator path = `/userdata/saves/psvita/`) and the next screen will ask you to install the firmware.

Go to **File** -> **Install Firmware**. Then, select the two files you copied in `/userdata/bios/psvita/` and install them both. Once this is done, you will see a "V" next to the "Installed" field of each firmware object. If you get stuck in that screen for whatever reason, quit the emulator by hitting `[ALT]`+`[F4]` and relaunch it from the Applications menu.

Then you will get to a screen to personalize the interface settings:

Then you will get to the final screen, congratulations, the hardest part is done!

Now, you need to create a PSVita user with the next screen:

Once the user has been created, you can select it automatically for all games by clicking on **Automatic User Login**.

Now, you have the main PSVita emulator screen:

You can quit the emulator (menu **File** -> **Exit** or `[ALT]` + `[F4]`)

## ROMs

This page is still under construction.

Place your PlayStation Vita ROMs in `/userdata/roms/psvita`.

There are multiple ways PS Vita ROMs have been dumped. These are the most popular:
- **Mai Dump**: Probably the most bootleg approach. Titles have been individually patched to make them bootable. May be missing game data, and for preservation is generally not recommended. Typically come in ZIP or VPK formats, but at this time, only Mai dumps in ZIP format are supported.
- **VPK**: The "installer" type of dump. This is somewhat close to the official media release. Mai Dumps may also come in VPK format, but they are not the same.
- **PKG**: FIXME
- **NoNpDRM rips**: FIXME
- **EBOOTPBP**: FIXME

The only format that has been confirmed working with Vita3K on Batocera are Mai Dumps in ZIP format.

The process for installing games has two steps:

1. Install the game from the Vita3k interface (that can be launched automatically if you open the .zip file). To do so, go to the File menu and install as a .zip format. You will see Vita's system software (just as you would the original PS Vita) with a new line with the game when it is installed.

2. After the install, you will be requested if you want to delete the .zip file. You can now do it, as the game is now installed in `/userdata/saves/psvita/ux0/app/<TITLE ID>`. Now, you need to create a launcher for Batocera EmulationStation, as a `.psvita` file (a simple text file, that can even be empty). The trick is that you need to put the `<TITLE ID>` 

```

Street Fighter X Tekken (USA) [PCSE00005].psvita

```

The game **TITLE ID** can be gotten by referring to the [compatibility list on Vita3k page](https://vita3k.org/compatibility.html?lang=en#) or from the main Vita3k menu, or again looking at what has been installed into `/userdata/saves/psvita/ux0/app/<TITLE ID>` in Batocera.

## Emulators
### Vita3K
Added in Batocera **v36**, [Vita3K](https:*vita3k.org/) is a highly experimental low-level emulator for the PS Vita. A quick start guide and minimum requirements can be found [on its website](https:*vita3k.org/quickstart.html).

#### Vita3K configuration
Standardized features available to all cores of this emulator: `psvita.videomode`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **GRAPHICS API `psvita.vita3k_gfxbackend`** | Choose which graphics API library to use. Vulkan is better, when supported.\\ => OpenGL `OpenGL`, Vulkan `Vulkan`. |
| **RENDERING RESOLUTION `psvita.vita3k_resolution`** | Enhancement. Increase the rendering resolution. Makes 3D objects clearer.\\ => 1x (960x544) `1`, 2x (1920x1088) `2`, 3x (2880x1632) `3`, 4x (3840x2176) `4`, 5x (4800x2720) `5`, 6x (5760x3264) `6`, 7x (6720x3808) `7`, 8x (7680x4352) `8`. |
| **FXAA `psvita.vita3k_fxaa`** | Anti-aliasing is a technique for smoothing out jagged edges.\\ => Disabled (Default) `False`, Enabled `True`. |
| **VSYNC `psvita.vita3k_vsync`** | Fix screen tearing.\\ => Disabled `False`, Enabled (Default) `True`. |

## Controls
Here are the default PlayStation Vita's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).