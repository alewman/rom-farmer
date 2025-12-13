# Sega Model 3

**Source:** https://wiki.batocera.org/systems:model3  
**Last fetched:** 2025-12-06 16:19:16

---

# Sega Model 3
The Sega Model 3 is an arcade board released in 1996 by Sega as a successor to the SEGA Model 2 board. It was significantly more powerful than the fifth-gen home consoles available at its time of release, more akin to the power of the sixth-gen consoles. It featured games such as Sega Rally 2, Daytona USA 2, Virtua Fighter 3 and Star Wars Trilogy Arcade.

Due to this power deficit between the Model 3 and the home consoles available at the time, not many games were ported to home consoles, leaving the only way to experience these games from playing them at the arcade.

Sega Model 3 emulation is still in its early stages, but many games are already at playable points with only minor issues.

This system scrapes metadata for the "model3" and "arcade" groups and loads the `model3` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [Supermodel](#supermodel)
- **Folder:** `/userdata/roms/model3`
- **Accepted ROM formats:** `.zip`

## BIOS
No Sega Model 3 emulator in Batocera needs a BIOS file to run.

## ROMs
Place your Sega Model 3 ROMs in `/userdata/roms/model3`.

Leave them as ZIP files, do not extract them. Supermodel in Batocera **v34** and below use MAME's 0.220 ROMset. Batocera **v35** and higher use [the latest MAME ROMset](:arcade#romset_version_per_stable_batocera_release).

Files inside the ZIP must match the board ROM and CRC expected by the emulator to function properly. Each ZIP must only contain one compressed ROM and be named correctly for compatibility.

All Model 3 games (except "Boat Race GP" as it was never dumped) are playable, however the old (outdated) compatibily list can be found on [Supermodel3's website.](https://www.supermodel3.com/About.html)

## Emulators
### Supermodel
[Supermodel](https://www.supermodel3.com/index.html) is a Sega Model 3 emulator that is still in early development, but can play the majority of games released for the unit. To quote their website:

> The aim of the Supermodel project is to develop an emulator that is both accurate and playable. As with virtually all arcade hardware, no public documentation for the Model 3 platform exists. What is known so far has been painstakingly reverse engineered from scratch. There is still plenty left to figure out and the emphasis at this early phase of development is toward accuracy rather than speed and usability.

#### Supermodel configuration
Standardized features available to all cores of this emulator: `model3.videomode`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **3D ENGINE `model3.engine3D`** | Enable the legacy or the new 3D engine (choose legacy for older GPUs)\\ => Legacy3D `legacy3d`, New3D `new3d`. |
| **QUAD RENDERING `model3.quadRendering`** | Enable proper quad rendering (for higher end systems)\\ => Off `0`, On `1`. |
| **ENABLE WIDESCREEN `model3.wideScreen`** | Enable widescreen (may cause rendering issues)\\ => Off `0`, On `1`. |
| **CROSSHAIRS `model3.crosshairs`** | Enable crosshairs in shooting games for the selected players\\ => None `0`, P1 only `1`, P2 only `2`, P1 & P2 `3`. |
| **ENABLE FORCE FEEDBACK `model3.forceFeedback`** | Enable force feedback for supported controllers with Linux drivers\\ => Off `0`, On `1`. |
| **MODERN PEDAL CONTROLS `model3.pedalSwap`** | Moves Accel/Brake to triggers and gear shift to shoulder buttons or right stick\\ => Off `0`, On `1`. |
| **ADJUST POWERPC FREQUENCY `model3.ppcFreq`** | Change the speed of the emulated PowerPC chip (fixes some issues)\\ => 25 `25`, 50 (Default) `50`, 75 `75`, 100 `100`, 125 `125`, 150 `150`. |

The configuration file (`/userdata/system/configs/supermodel/supermodel.ini`) stores input settings as well as most of what can be set on the command line.

Sound and music volume can be adjusted during run-time using the F9-F12 keys.
Volume settings can be specified in the configuration file as well, globally for all games or tailored on a game-by-game basis.

For further help with the usage and configuration of Supermodel, refer to their [official documentation](https://www.supermodel3.com/Usage.html).

### Save states
Save states are fully supported. Up to 10 different slots can be selected with keyboard - `[F6]`. To save and restore states, press `[F5]` and `[F7]`.

State files are saved in the `/saves/supermodel/` folder, which must exist in order for save operations to succeed.

Non-volatile memory (NVRAM) consists of battery-backed backup RAM (typically used for high score data) and an EEPROM (machine settings). It is saved to the NVRAM folder at `/system/configs/supermodel/NVRAM/` each time Supermodel exits and is re-loaded at start-up.

Save states will also save and overwrite NVRAM data.

If you alter any machine settings, loading an earlier state will return them to their former configuration. Be sure to save these files for future use.

## Controls
Here are the default Sega Model 3's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### My game has X issue
Check the [compatibility chart](https://www.supermodel3.com/About.html) first, it may be a known issue.

You might also want to check out [Supermodel's FAQ](https://www.supermodel3.com/FAQ.html).

### Service menu
The game's service menu can be accessed by pressing `[6]` on the keyboard. Tap `[5]` (service button) to navigate and `[6]` (test button) to confirm.

### Network Board Not Present
For certain multiplayer games, if you receive the error "Network Board Not Present" upon starting it, go to the service menu and navigate to **Games Assignments** -> **Link ID** and change its option to "Single". This will put the machine into single player mode, thus allowing the game to boot.

### How do I reload in lightgun games?
Right-click by default.

### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).