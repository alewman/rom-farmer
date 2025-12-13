# Voxatron

**Source:** https://wiki.batocera.org/systems:voxatron  
**Last fetched:** 2025-12-06 16:20:00

---

# Voxatron
Voxatron is a fantasy console [created by Lexaloffle](https:*www.lexaloffle.com/voxatron.php), the same folks behind [Pico-8](systems:pico8). The games are meant to be  made only of voxels (3D pixels, or colorful tiny cubes, think Minecraft). It has never been physically released, but runs as a software on computers like Windows / Mac / Linux and web browsers. There is no emulator in Batocera for this system, you need to [purchase it](https:*www.lexaloffle.com/voxatron.php) and while it's in alpha, you will get a free license for [Pico-8](systems:pico8). At this moment, only x86_64 is supported for their Linux engine, nothing for ARM SBC yet.

### Quick reference
- **Emulator:** None
- **Core:** Lexaloffle vox binary
- **Folder:** `/userdata/roms/voxatron`
- **Accepted ROM formats:** `.png`
## BIOS
No BIOS is required, but you need to add the Voxatron binary in the `/bios/` folder (see below).

## ROMs
Place your Voxatron ROMs in `/userdata/roms/voxatron/`. Create an empty file with the name `splore.vx` (or use any PNG as `splore.png`) to explore the Splore universe and download carts from there.

### "Cartridges" and games format
Like Pico-8, Voxatron games are distributed as PNG images with the actual code, sprites and sounds embedded in them. Those are actual, real image files, that stands as the cartridge art too. You have to "load" the PNG to run the game. You can download carts [from the official page](https://www.lexaloffle.com/bbs/?cat=6&carts_tab=1#sub=2&mode=carts), the community is pretty active. Once you select a game, make sure you click on the "cart" link that downloads a `.vx.png` file.

## Emulators
## Support for official Voxatron engine
Starting with Batocera **v40**, you can add the official commercial Lexaloffle Voxatron engine to run all games and explore the Splore universe! In order to do so, you need to do a few manual steps:

  - Buy it from [the official Lexaloffle website](https://www.lexaloffle.com/games.php?page=updates).
  - Download the corresponding binary (it's the ZIP file) appropriate to your platform:
  - **For PC/any x86_64 board:** The Linux (x86_64/64 bits) ZIP file.
  - Unfortunately, at this date, there's no support for ARM SBCs/
  - Extract the files from the zip into the `/userdata/bios/voxatron/` directory on your Batocera machine. You might need to create this directory first.
  - The files in the archive, for v0.3.6 as a reference, are:```

lexaloffle-vox.png
libHoloPlayCore.so
license.txt
vox  <--- make sure this file is executable, with `chmod +x `
vox_dyn
vox.dat
voxatron.txt

```
  - Copy the following ES system addition into `/userdata/system/configs/emulationstation/es_systems_voxatron.cfg`:```

<?xml version="1.0" encoding="UTF-8"?>
<systemList>
  <system>
        <fullname>Voxatron</fullname>
        <name>voxatron</name>
        <manufacturer>Fantasy</manufacturer>
        <release>2015</release>
        <hardware>console</hardware>
        <path>/userdata/roms/voxatron</path>
        <extension>.vx .png</extension>
        <command>emulatorlauncher %CONTROLLERSCONFIG% -system %SYSTEM% -rom %ROM% -gameinfoxml %GAMEINFOXML% -systemname %SYSTEMNAME%</command>
        <platform>voxatron</platform>
        <theme>voxatron</theme>
	<emulators>
            <emulator name="lexaloffle">
                <cores>
                    <core default="true">vox_official</core>
                </cores>
            </emulator>
        </emulators>
  </system>
</systemList>

```
  - Restart ES (or reboot).

If you create a file `splore.vx` or `console.vx` and launch it from Batocera-ES, you'll get access to Voxatron splore universe with all the games to play and download from inside Voxatron (a simple `touch /userdata/roms/voxatron/splore.vx` is sufficient to get access to splore). You can also use a PNG image under the name `splore.png`.

Press `[START]` to open Voxatron's menu, which can be used to exit the emulator and return to Batocera.

## Controls
Keys inside the emulator: `[START]` or `[HOTKEY]` +  opens the Voxatron menu.

`[LEFT SHOULDER]` and `[RIGHT SHOULDER]` can be used to move the camera up and down.

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).