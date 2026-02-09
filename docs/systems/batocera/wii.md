# Nintendo Wii

**Source:** https://wiki.batocera.org/systems:wii  
**Last fetched:** 2025-12-06 16:20:02

---

# Nintendo Wii
The Nintendo Wii is a console developed by Nintendo. It was released on November the 19th, 2006 and retailed for $249.99 USD.

The Wii sports a IBM PowerPC CPU at 729 MHz with 88MB of RAM, and a GPU infamously created by ATI (Wii consoles have "ATI" printed on its shell) dubbed the "Hollywood" chip. Its internal architecture is very similar to its predecessor, the [GameCube](:systems:gamecube), so [Dolphin](#dolphin) supports running both Wii and GameCube games. In fact, some GameCube games can be more difficult to run than Wii games.

Dolphin is pretty much the only Wii emulator.

This system scrapes metadata for the `wii` group and loads the `wii` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.gcm`, `.iso`, `.gcz`, `.ciso`, `.wbfs`, `.wad`, `.rvz`, `.elf`, `.dol`, `.m3u`, `.json`
- **Folder:** `/userdata/roms/wii`

| Emulators |
| [Dolphin](#dolphin) |
| [libretro: Dolphin](#libretro:_dolphin) |

## BIOS
The libretro version of Dolphin requires its NAND to be stored in `bios/dolphin-emu/Sys`.

The standalone version will generate the needed files on first launch.

## ROMs

Some users have reported issues with using regular traditional controllers as Wiimotes in Wii games if the game loaded has the `.cc.rvz` extension. Renaming this extension to `.nkit.iso` solved the issue for them (no actual conversion was done, just renaming).

Place your Wii ROMs in `/userdata/roms/wii`.

If you have a Riivolution patch, first create its JSON file as [outlined on the Dolphin emulator page](emulators:dolphin#riivolution_patches).

## Emulators
### Dolphin

For general information about the Dolphin Emulator itself, you can also visit the [Dolphin emulator page instead.](emulators:dolphin)

#### Dolphin configuration
| ES setting name `batocera.conf key` | Description => ES option `key value` |
| Settings that apply to all cores of this emulator |
| **GRAPHICS BACKEND `wii.gfxbackend`** | Choose your graphics rendering\\ => OpenGL `OGL`, Vulkan `Vulkan`. |
| **UBERSHADERS `wii.ubershaders`** | Improve performance with Ubershaders. Ubershaders take advantage of your GPU to avoid in-game stutters as it generates shaders for the first time; this can happen when a certain special effect shows on the screen or a new model is rendered. Hybrid ubershaders are preferred, it will use the GPU accelerated ubershader if available to avoid stutter, otherwise it will fall back to traditional shader generation. Exclusive ubershaders will only use ubershaders, only activate this option if you have an extremely powerful GPU. Normally there is no downside to activating ubershaders, however it does increase the minimum requirements out of your GPU to run. On especially weak hardware, such as SBCs, ubershaders are disabled by default. They can still be manually turned on, but you may encounter *more* stutter if on an SBC. Skip draw is a hack that opts to take a different approach altogether: don't display the object in game if its shader hasn't compiled yet. Obviously, this can result in visual glitches, but may be the best option performance-wise if your hardware is extremely weak.; asynchronous is preferred, synchronous is more compatible\\ => No Ubershaders `no_ubershader`, Exclusive Ubershaders `exclusive_ubershader`, Hybrid Ubershaders `hybrid_ubershader`, Skip Drawing `skip_draw`. |
| **PRE-CACHE SHADERS `wii.wait_for_shaders`** | Wait for shaders to compile completely before starting the game, can reduce micro-freezes\\ => Off (default) `0`, On `1`. |
| **PERFORMANCE HACKS `gamecube.perf_hacks`** | Increase emulator performance, at the cost of accuracy/stability. Settings set to "True" with this option: Defer EFB copies to RAM `DeferEFBCopies`, Scaled EFB Copy `EFBScaledCopy`, EFB Copies `EFBToTextureEnable`, Skip Presenting Duplicate Frames `SkipDuplicateXFBs`, XFB copies `XFBToTextureEnable`, Force Texture Filtering `ForceFiltering`, Arbitrary Mipmap Detection `ArbitraryMipmapDetection`, Disable Copy Filter `DisableCopyFilter`, Force 24-Bit Color `ForceTrueColor`. Settings set to "False" with this option: Bounding Box `BBoxEnable`, Ignore Format Changes `EFBEmulateFormatChanges`.\\ => Off `0`, On `1`. |
| **USE PAD PROFILES `wii.use_pad_profiles`** | Search for custom configured joystick profiles\\ => Off `0`, On `1`. |
| **VIDEO RESOLUTION `wii.internal_resolution`** | Improve the fidelity of 3D models (does not affect 2D sprites)\\ => 1x native (640x528) `1`, 2x 720p (1280x1056) `2`, 3x 1080p (1920x1584) `3`, 4x 1440p (2560x2112) `4`, 5x (3200x2640) `5`, 6x 4K (3840x3168) `6`, 7x (4480x3696) `7`, 8x 5K (5120x4224) `8`. |
| **ANISOTROPIC FILTERING `wii.anisotropic_filtering`** | Enhance the quality of distant perspective textures\\ => Off `0`, 2x `1`, 4x `2`, 8x `3`, 16x `4`. |
| **DUAL CORE MODE `wii.dual_core`** | Usually not much faster than single core mode\\ => Off `0`, On `1`. |
| **GPU SYNC `wii.gpu_sync`** | Speed hack for dual core mode to fix some glitches\\ => Off `0`, On `1`. |
| **ANTI-ALIASING `wii.antialiasing`** | Smooth out jagged edges on 3D object polygons\\ => Off `0`, 2x `2`, 4x `4`, 8x `8`. |
| **ANTI-ALIASING MODE `wii.use_ssaa`** | Toggle MSAA/SSAA. Depends on anti-aliasing being enabled.\\ => MSAA (default) `0`, SSAA `1`. |
| **HIRES TEXTURES `wii.hires_textures`** | Use HD texture packs\\ => Off `0`, On `1`. |
| **WIDESCREEN HACK `wii.widescreen_hack`** | You must use a 16/9 RATIO to work\\ => Off `0`, On `1`. |
| **ENABLE CHEATS `wii.enable_cheats`** | To use game cheats or 16/9 Aspect Ratio Fix codes\\ => Off `0`, On `1`. |
| **MEMORY MANAGEMENT UNIT `wii.enable_mmu`** | Allows many games to boot and work properly\\ => Off `0`, On `1`. |
| **FAST DISK SPEED `wii.enable_fastdisc`** | Speeds up disc speed to remove any loading\\ => Off `0`, On `1`. |
| **VSYNC `wii.vsync`** | Fix the heavy screen tearing in games (CPU heavy)\\ => Off `0`, On `1`. |
| **DUALSHOCK MOTION CONTROL `wii.dsmotion`** | Emulate the Wii pointer with your DS4's gyroscope\\ => Off `0`, On `1`. |
| **MOUSE AS IR WIIMOTE `wii.mouseir`** | Emulate the Wiimote IR control with a mouse\\ => Off `0`, On `1`. |
| **RUMBLE `wii.rumble`** | To use vibration on games with Rumble mode\\ => Off `0`, On `1`. |
| Settings specific to `wii` |
| **EMULATE WIIMOTE `wii.emulatedwiimotes`** | Use your gamepad like a vertical Wiimote in game\\ => Off `0`, On `1`. |
| **CUSTOMIZE WIIMOTE & GAMEPAD `wii.controller_mode`** | Emulate a Wiimote Sideway with L2 for Shake and Nunchuk on R-stick.\\ => Off `disabled`, Classic Controller `cc`, Wiimote Sideway `side`, Wiimote Sideway + Swing `is`, Wiimote Sideway + Tilt `it`, Wiimote Sideway + Nunchuk `in`. [More details on its own page.](systems:wii:wiimoteprofiles) |
| **SHOW LIGHT GUN CROSSHAIRS `wii.dolphin-lightgun-hide-crosshair`** | Show a crosshair for the Wiimote's emulated IR sensor.\\ => Off `0`, On `1`. |

### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: Dolphin
Standardized features for this core: `wii.autosave`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **RENDERING RESOLUTION `global.wii_resolution`** | Enhancement. Increase the rendering resolution. Makes 3D objects clearer.\\ => 1x native (640x528) `x1 (640 x 528)`, 2x 720p (1280x1056) `x2 (1280 x 1056)`, 3x 1080p (1920x1584) `x3 (1920 x 1584)`, 4x 1440p (2560x2112) `x4 (2560 x 2112)`, 5x (3200x2640) `x5 (3200 x 2640)`, 6x 4K (3840x3168) `x6 (3840 x 3168)`. |
| **LANGUAGE `global.wii_language`** | Wii NAND's language setting.\\ => English `English`, French `French`, German `German`, Spanish `Spanish`, Italian `Italian`, Dutch `Dutch`, Japanese `Japanese`, Simplified Chinese `Simplified Chinese`, Traditional Chinese `Traditional Chinese`, Korean `Korean`. |
| **WIDESCREEN HACK (GLITCHY) `global.wii_widescreen_hack`** | Enhancement. Only works with a 16/9 ratio and bezels disabled.\\ => Off `disabled`, On `enabled`. |
| **UBERSHADERS `global.wii_shader_mode`** | May not work well on all hardware. Hybrid is preferred, where supported.\\ => No Ubershaders `sync`, Exclusive Ubershaders `sync UberShaders`, Hybrid Ubershaders `a-sync UberShaders`, Skip Drawing `a-sync Skip Rendering`. |
| **ANISOTROPIC FILTERING `global.wii_anisotropic`** | Improves clarity of distant textures.\\ => Off `1x`, 2x `2x`, 4x `4x`, 8x `8x`, 16x `16x`. |
| Settings specific to wii ||
| **WII TV MODE `wii.wii_widescreen`** | Wii NAND's aspect ratio setting. Most games support both ratios natively.\\ => 16:9 `enabled`, 4:3 `disabled`. |
| **CONTROLLER 1 TYPE `wii.controller1_wii`** | Emulate a Wiimote Sideway with L2 for Shake and Nunchuk on R-stick.\\ => WiiMote `1`, WiiMote Sideways `513`, WiiMote + Nunchuk `769`, WiiMote + Classic Controller `1025`, WiiMote + Classic Controller Pro `1281`, Real Wiimote `1536`, GameCube Controller `1281`. |
| **CONTROLLER 2 TYPE `wii.controller2_wii`** | Emulate a Wiimote Sideway with L2 for Shake and Nunchuk on R-stick.\\ => WiiMote `1`, WiiMote Sideways `513`, WiiMote + Nunchuk `769`, WiiMote + Classic Controller `1025`, WiiMote + Classic Controller Pro `1281`, Real Wiimote `1536`, GameCube Controller `1281`. |
| **CONTROLLER 3 TYPE `wii.controller3_wii`** | Emulate a Wiimote Sideway with L2 for Shake and Nunchuk on R-stick.\\ => WiiMote `1`, WiiMote Sideways `513`, WiiMote + Nunchuk `769`, WiiMote + Classic Controller `1025`, WiiMote + Classic Controller Pro `1281`, Real Wiimote `1536`, GameCube Controller `1281`. |
| **CONTROLLER 4 TYPE `wii.controller4_wii`** | Emulate a Wiimote Sideway with L2 for Shake and Nunchuk on R-stick.\\ => WiiMote `1`, WiiMote Sideways `513`, WiiMote + Nunchuk `769`, WiiMote + Classic Controller `1025`, WiiMote + Classic Controller Pro `1281`, Real Wiimote `1536`, GameCube Controller `1281`. |

Further options can be adjusted in RetroArch's Quick Menu ( `[HOTKEY]` +  in-game).
## Controllers for the Wii

There are multiple choices for controllers and connections for playing Wii on Batocera:
- [Native Wiimote using native Bluetooth](#native_wiimote_using_native_bluetooth): Use original Wiimote controllers with either a native Bluetooth receiver.
- [Native Wiimote using a Dolphinbar](#native_wiimote_using_a_dolphinbar): Use original Wiimote controllers with a Dolphinbar.
- [Emulated Wiimote/Classic controller with a gamepad](#emulated_wiimote_classic_controller_with_a_gamepad): Use a standard gamepad to emulate a Wiimote for the emulated game.
- [Emulated GameCube controller with a gamepad](#emulated_gamecube_controller_with_a_gamepad): Use standard gamepads for [classic/GameCube controller-compatible games](#classic_controller_compatible_games_list). This is the default mode.

### Native Wiimote using native Bluetooth

We can use the Wiimote as if though it were connected to an original Wii, just instead of the Wii it's the emulated Wii running inside of Batocera. To do this, the Wiimote must **not** be paired to Batocera while in the EmulationStation menu, only after launching a Wii game using the Dolphin emulator. When Dolphin is launched, put the Wiimote into pair mode and it will pair. That's it. Use the IR bar as you would a normal Wii, place it either at the top or bottom of the TV screen and point at it for the on-screen Wiimote cursor.

This will work for as long as the Bluetooth dongle itself supports communicating with the Wiimote.

An ordinary controller (or keyboard) will be required to navigate menus when outside of the emulated Wii game, as the Wiimote itself cannot be used for this.

This method cannot be used simultaneously with pairing the Wiimote in EmulationStation (the main menu), as that will use the ordinary method of attempting to map the current controller to an emulated GameCube controller (by default)/Wiimote instead of the native interface.

(FIXME unless you choose the "gamepad" option for the wiimote gun settings? Needs confirmation)

It is possible to sync the Wiimote to ES and then to re-sync again after opening Dolphin by using the temporary sync mode (hold `[1]` and `[2]` on the Wiimote) so it only remembers for that session if you intend on using the Wiimote to play systems other than Wii as well.

### Native Wiimote using a Dolphinbar

The Dolphinbar acts as an intermediary body between the machine and the Wiimote. It also includes IR LEDs which automatically shut off when not in use. Its Bluetooth module is the most unresponsive of all the available options, usage of native Bluetooth connection instead is usually more responsive.

An ordinary controller (or keyboard) will be required to navigate menus when outside of the emulated Wii game, as the Wiimote itself cannot be used for this.

  - Connect your **DolphinBar** with USB to the machine.
  - Press the right (FIXME MODE?) button to switch to **MODE 4**, the passthrough mode.
  - Launch any Wii game from ES using a traditional controller.
  - **To permanently pair the Wiimote:**
    - On the Wiimote, hold down the red sync button inside of the battery compartment. The LEDs will begin flashing.
  - **To only temporarily pair the Wiimote:**
    - On the Wiimote, hold down buttons `[1]` + `[2]`. The LEDs will begin flashing.
  - Wait until the LEDs stop flashing. Once they do, the Wiimote is connected to the emulated Wii system.

Repeat for each **Wiimote** desired.

For more info, refer to the [Dolphinbar-specific page](hardware:dolphinbar).

Do the same limitations about pairing in ES apply here?

What does the light gun page for Dolphinbar have to do with this? Maybe the link to it should be removed.

There's a SYNC button on the Dolphinbar itself. What does that do in this context? Is it required to be pressed or does Batocera automatically put the Dolphinbar into pairing mode once Dolphin is launched? Is the button just a passthrough for the Dolphin hotkey which automatically puts the emulated Wii into its sync mode?

### Using Bluetooth passthrough

<wrap em>This is not required to use Wiimotes regularly with Bluetooth adapters.</wrap> Dolphin works fine using its [emulated Bluetooth connections](#configuring_a_wiimote_using_native_bluetooth) in most cases.

Doing this will render your Bluetooth module inoperable with anything that *isn't* Dolphin, including navigating the EmulationStation front-end! Be sure to have a different way of navigating the menus prepared.	

	
A keyboard and mouse are required to initially configure this.

If instead you'd like to utilize [Dolphin's Bluetooth passthrough feature](https://wiki.dolphin-emu.org/index.php?title=Bluetooth_Passthrough), do the following:
  - Go to the `dolphin-emu-config` application in **Files** (`[F1]` in system list) -> **Applications**.
  - Go to **Options** -> **Configuration** -> **Wii** and add your Bluetooth module to the **Whitelisted USB Passthrough Devices** box.
You can test for this by plugging in your Bluetooth USB dongle and seeing which device appears, if that's what you're using.

  - Close the configuration window, then launch a Wii game directly from Dolphin (double-click one of the Wii games on the list).
  - Press `[Alt]` + `[Tab]` to go back to the Dolphin menu.
  - Go to **Options** -> **Controller Settings** and under **Passthrough a Bluetooth adapter** click **Sync**.
  - Press the red `[SYNC]` button on the underside of your Wiimote. You can either remove the battery cover to get to it or use a toothpick to press it through the hole in the cover.
You can press `[Alt]` + `[Tab]` again to get in-game and confirm that your controller is working.

  - Go to **Emulation** -> **Stop** to stop the game.
  - Exit Dolphin.

You can now use Bluetooth passthrough with Dolphin after launching the game from Batocera!

Wiimote profiles can be [manually set via Batocera configs](systems:wii:wiimoteprofiles), however it is recommended to just [use Dolphin's sophisticated remapping tools](:remapping_controls_per_emulator#wii) and use a custom pad profile instead.

### Use of the Skylanders portal with Dolphin's passthrough
Navigate to `[F1]` **File manager** -> **Applications** -> **dolphin-emuconfig**

Once Dolphin is opened, navigate to **Options** -> **Configuration** -> **Wii** and then add the portal to the **Whitelisted USB Passthrough Devices**.

#### Batocera v35 and below
Batocera v35 and below requires a new udev rule to be intsalled to function correctly. Save this file to `/userdata/rules.d/51-gcadapter.rules`:

```

SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device", ATTRS{idVendor}=="1430", ATTRS{idProduct}=="0150", MODE="0666"

```

### Emulated GameCube controller with a gamepad
This is the default mode, when nothing else is configured. Shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### There are infrequent frame-drops in my games despite them running at full-speed most of the time
Your GPU might not be strong enough to calculate the caches in real-time while playing. This can be worked around by activating the **PRE-CACHE SHADERS `wii.wait_for_shaders`** setting, at the cost of having to wait a while on your next launch of the game (one time only).

#### It's still happening!
For exceptionally weak hardware, it might also be worth turning off **UBERSHADERS `wii.ubershaders`** altogether.

### I have X problem with Y game
Dolphin has a great and informative wiki, usually detailing which settings may need to be altered to avoid issues in certain games. Search for your game on it here: https://wiki.dolphin-emu.org/index.php?title=Main_Page

### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).