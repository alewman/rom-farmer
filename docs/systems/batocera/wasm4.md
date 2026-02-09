# WASM-4

**Source:** https://wiki.batocera.org/systems:wasm4  
**Last fetched:** 2025-12-06 16:20:01

---

# WASM-4
The [WASM-4](https://wasm4.org) is a fantasy console developed by Aduros, similar to the likes of the [Pico-8](systems:pico8) and [TIC-80](systems:tic80). It was released in 2021.

WASM-4 runs games written in WebAssembly, which is compatible with a wide variety of programming languages (as long as they compile in WebAssembly). This fantasy console is opensource and distributed [on Github](https://github.com/aduros/wasm4).

The specifications should be mentioned in their respective sections, not here in the summary.

Fantasy hardware constraints:
- Display: 160x160 with 4 customizable colors
- Cartridge: `.wasm` file, max 64kB
- Memory: 64kB
- Sound: 2 pulse wave channels, 1 triangle wave channel, 1 noise channel
- Code: WebAssembly
- Input: 2-button gamepad, keyboard, mouse, up to 4 gamepads
- Disk Storage: 1024 bytes

This system scrapes metadata for the "wasm4" group(s) and loads the `wasm4` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: wasm4](#libretro:_wasm4)
- **Folder:** `/userdata/roms/wasm4`
- **Accepted ROM formats:** `.wasm`

## BIOS
No WASM-4 emulator in Batocera needs a BIOS file to run.

## ROMs
Place your WASM-4 ROMs in `/userdata/roms/wasm4`.

## Emulators
### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: wasm4
##### libretro: wasm4 configuration
Standardized features for this core: `wasm4.rewind`, `wasm4.autosave`, `wasm4.netplay`, `wasm4.padtokeyboard`

There is currently no intergrated configuration for this core. Use RetroArch's quick menu for now.

## Controls
- Movement: D-pad / left analog stick
- Action buttons:  and   
- Mouse: Right analog stick, left and right triggers for left and right mouse clicks.

Here are the default WASM-4's controls shown on a [Batocera RetroPad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).