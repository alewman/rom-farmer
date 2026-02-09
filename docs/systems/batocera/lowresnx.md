# LowresNX

**Source:** https://wiki.batocera.org/systems:lowresnx  
**Last fetched:** 2025-12-06 16:19:11

---

# LowresNX
LowresNX is a retro-style game development environment that allows users to create and play 8-bit games. It offers a simple, pixel-based graphic editor and a BASIC-like programming language, making it accessible for beginners and nostalgic for experienced programmers. LowresNX supports a vibrant community where users can share their creations, collaborate on projects, and explore the wide variety of games made by others. It runs on various platforms, including Windows, Mac, and iOS, providing a versatile and engaging tool for game development enthusiasts.

This system scrapes metadata for the "lowresnx" group and loads the `lowresnx` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: lowresnx](#libretro:lowresnx)
- **Folder:** `/userdata/roms/lowresnx`
- **Accepted ROM formats:** .nx .zip .7z

## BIOS
No LowresNX emulator in Batocera needs a BIOS file to run.

## ROMs
Place your LowresNX ROMs in `/userdata/roms/lowresnx`.

## Emulators
### RetroArch
[RetroArch](https:*docs.libretro.com/) (formerly SSNES), is a ubiquitous frontend that can run multiple "cores", which are essentially the emulators themselves. The most common cores use the [libretro](https:*www.libretro.com/) API, so that's why cores run in RetroArch in Batocera are referred to as "libretro: (core name)". RetroArch aims to unify the feature set of all libretro cores and offer a universal, familiar interface independent of platform.

#### RetroArch configuration
RetroArch offers a **Quick Menu** accessed by pressing `[HOTKEY]` +  which can be used to alter various things like [RetroArch and core options](:advanced_retroarch_settings), and [controller mapping](:remapping_controls_per_emulator). Most RetroArch related settings can be altered from Batocera's EmulationStation.

## Controls
## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).