# Sony PlayStation 4

**Source:** https://wiki.batocera.org/systems:ps4  
**Last fetched:** 2025-12-06 16:19:37

---

# Sony PlayStation 4
The PlayStation 4 (PS4) is a home video game console developed by Sony Interactive Entertainment. Announced as the successor to the PlayStation 3 in February 2013, it was launched on November 15, 2013, in North America, November 29, 2013, in Europe, South America, and Australia, and on February 22, 2014, in Japan. A console of the eighth generation, it competes with Microsoft's Xbox One and Nintendo's Wii U and Switch.

This system scrapes metadata for the `ps4` group and loads the `ps4` set from the currently selected theme, if available.

## Quick reference
- **Emulator:** ShadPS4
- **Folder:** `/userdata/roms/ps4`
- **Accepted ROM formats:** `.ps4` 

## ROMs
Before you can play a game you must install the game via the associated .PKG file of your backed-up game using the F1 menu.
Then in the new installation directory for the installed game, create a file with a .ps4 extension so EmularionStation will see it.
i.e. /userdata/roms/ps4/CUSA03173/Bloodborne.ps4

Afterwards you can launch the game from EmulationStation accordingly.

DLC content will be stored in: /userdata/roms/ps4/DLC

Very important: To play games you may need the system modules from your PS4 that has been jailbroken.
The log file may give an indication of any required system modules.
Place the decrypted system module files in: /userdata/system/configs/shadps4/user/sys_modules

## Emulators
PS4 emulation is very experiemental & requires a highly specified x86_64 PC.
Ideally your CPU supports the AVX2 instruction set and your GPU must support Vulkan 1.3 or later.

### ShadPS4
For compatibility check: https://shadps4.net/compatibility/

## Controls
Here are the Sony PlayStation 4's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).