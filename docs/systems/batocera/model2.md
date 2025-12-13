# Sega Model 2

**Source:** https://wiki.batocera.org/systems:model2  
**Last fetched:** 2025-12-06 16:19:15

---

# Sega Model 2
Recommended video: [Batocera Nation's SEGA Model 2 guide.](https://youtu.be/RoeU9hWe8PU)

The SEGA Model 2 is an arcade board released in 1993 by SEGA as a successor to the SEGA Model 1 board. It features several popular arcade games such as Daytona USA, Dead Or Alive, Sega Rally, House of the Dead and Virtua Cop. Most of these had ports to home consoles, some inferior and some superior to their original arcade incarnations. It has an Intel i960-KB CPU at 25 MHz with 9776KB of RAM.

This emulator runs inside of WINE. You need to run a ROM at least once while connected to the Internet in order to download the required DirectX libraries for WINE. This may take a while (up to ten minutes), depending on your internet connection. There is no progress bar.

This only needs to be done once.

This emulator is still under heavy construction, both in terms of the emulator itself *and* its implementation into Batocera. Certain features can only be configured via its standalone component, as detailed below.

In Batocera **v32** and higher there is a bug where WINE cannot run applications/games stored on a NAS. This can be worked around by not using a NAS for your saves folder. The Model 2 emulator is run in WINE.

This system scrapes metadata for the `model2` and `arcade` groups and loads the `model2` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [Model2emu](#model2emu)
- **Folder:** `/userdata/roms/model2`
- **Accepted ROM formats:** `.zip`

## ROMs
ROMs should be put as they are into `roms/model2/`. Leave the files as ZIP files, do not extract them. The entire ROMset is 32 games.

## Emulators
### Model2emu
#### Model2emu configuration
Standardized features available to all cores of this emulator: `model2.videomode`

| ES setting name `batocera.conf key` | Description => ES option `key value` |
| **SCREEN RATIO `model2.screenRatio`** | Choose screen ratio (4:3 default)\\ => 4:3 `0`, 16:9 `1`, 16:10 `2`. |
| **FAKE GOURAUD `model2.fakeGouraud`** | Tries to guess Per-vertex colour (gouraud) from the Model2 per-poly information (flat)\\ => Off `0`, On `1`. |
| **BILINEAR FILTERING `model2.bilinearFiltering`** | Enables bilinear filtering of textures\\ => Off `0`, On `1`. |
| **TRILINEAR FILTERING `model2.trilinearFiltering`** | Enables mipmap usage and trilinear filtering (doesn't work with some games, DoA for example)\\ => Off `0`, On `1`. |
| **FILTER TILEMAPS `model2.filterTilemaps`** | Enables bilinear filtering on tilemaps (looks good, but can cause some stretch artifacts)\\ => Off `0`, On `1`. |
| **FORCE MANAGED `model2.forceManaged`** | Forces the DX driver to use Managed textures instead of Dynamic\\ => Off `0`, On `1`. |
| **ENABLE MIPMAP `model2.enableMIP`** | Enables Direct3D Automipmap generation\\ => Off `0`, On `1`. |
| **ENABLE MESH TRANSPARENCY `model2.meshTransparency`** | Enabled meshed polygons for translucency.\\ => Off `0`, On `1`. |
| **ENABLE FULL SCREEN ANTIALIASING `model2.fullscreenAA`** | Enable full screen antialiasing in Direct3D.\\ => Off `0`, On `1`. |
| **ENABLE RAW INPUT `model2.useRawInput`** | Read mouse through Rawinput, allowing 2 mice for 2 player shooting games\\ => Off `0`, On `1`. |

## Controller configuration

A keyboard & mouse is required to configure your controller(s).

A set on input files is provided however you may want to map your controls per game ROM you intend to run. We recommend you do this using the model2-config application accessible via the file manager (`[F1]` on the system list).

The ROM must be loaded before you can configure its controls.

First, run the game once from EmulationStation. It may take a while to load up initially, wait until it has booted. Then, exit the game and enter the `model2-config` application. Navigate to **Emulator** -> **Load Rom...** and run the ROM you want to configure the controls for, it will begin in fullscreen. Press `Esc` on your keyboard to go back to windowed mode to then set the controller options from **Game** -> **Configure Controls...**.

By default, analog controls are read as digital inputs. Click the check mark on the left side of the input entry to enable analog input (requires an axis to be bound to that control to function).

If you ever lose focus of the `model2-config` application because of clicking on the file manager in the background, you can bring it back to focus by pressing `[Alt]` + `[Tab]`.

Once the controls are set, go to **Emulator** -> **Exit**. This will save the configuration for future use in the Batocera options. (FIXME what does this even mean?)

As of right now, the controls can only be configured for a specific controller, unlike how the rest of the emulators implemented into Batocera behave. This may change in the future.

## Troubleshooting
Many things can and will go wrong.

### Service Menu

A keyboard & mouse is required to navigate the service menu.

This menu is critical to functions and options that can be adjusted within the game itself, such as aligning the crosshair for lightgun games and changing the difficulty. The service menu can be accessed by pressing `[F2]` during gameplay. Press `[F1]` to navigate and `[F2]` to confirm.

You can exit the service menu by navigating to **Exit** and pressing `[F2]` twice.

### Network Board Not Present
For certain multiplayer games, if you receive the error "Network Board Not Present" upon starting it, go to the service menu and navigate to **Games System** -> **Link ID** and change its option to "Single". This will put the machine into single player mode, thus allowing the game to boot.

### My lightgun game's crosshair is way out of sync and I swear I'm not that bad at aiming!
Out of the box, most games need some calibration to align with your on-screen crosshair.

Enter the service menu and navigate to **GUN SETTING** -> **PLAYER1 GUN ADJUSTMENT**. Aim at the targets and click on their centers. You will then be shown a screen showing your real crosshair and your virtual crosshair, they should be aligned (mostly). If it looks good, press `[F2]` to save the calibration. To return to your previous calibration instead, press `[F1]`.