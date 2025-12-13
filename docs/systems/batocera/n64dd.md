# N64 Disc Drive

**Source:** https://wiki.batocera.org/systems:n64dd  
**Last fetched:** 2025-12-06 16:19:21

---

# N64 Disc Drive
Better known as the N64DD, this was an expansion available for the original N64 that would allow for the loading from discs instead of cartridges.

Largely a commercial failure, never left Japan. But the few titles that were developed and released for it were incredible.

### Quick reference
- **Accepted ROM formats:** `.z64` `.n64` `.ndd` `.zip` `.7z`
- **Folders:** `/userdata/roms/n64dd`

| Emulators | Accepted ROM formats |
| [libretro: Mupen64Plus-Next](#libretro:_mupen64plus-next) | `.z64`, `.n64`, `.v64`, `.zip`, `.7z` |
| [libretro: ParaLLel_N64](#libretro:_parallel_n64) | `.z64`, `.n64`, `.v64`, `.zip`, `.7z` |

## BIOS
| MD5 checksum                      | Share file path               | Description                                               |
| FIXME                             | `bios/Mupen64plus/IPL.n64`  | N64 Dynamic Disk Initial Program Loader for Mupen64Plus   |
| 8d3d9f294b6e174bc7b1d2fd1c727530  | `bios/64DD_IPL.bin`         | N64 Dynamic Disk Initial Program Loader for Parallel-N64  |

## Using libretro-Mupen64Plus-Next
To play N64DD games:
  - First make sure that you have the right N64DD BIOS file at the right location (see above).
  - Place your N64DD cartridge ROMs in `/userdata/roms/n64dd`. They should have the extension `.z64`.
  - Place your N64DD disk ROMs in the same `/userdata/roms/n64dd`. They should have the extension `.z64.ndd`.
  - While hovering over the game in the gamelist, press `[SELECT]` and set the emulator to [libretro: Mupen64Plus-Next](#libretro:_mupen64plus-next).

Emulators/configuration are the same as the regular N64 emulators.

## Using libretro-Parallel64
Libretro-Parallel64 enables standalone N64DD games like `SimCity 64` or the `Mario Artist` series. These aren't expansions but full games running originally on floppy disks. To play these games:
  - First make sure that you have the right N64DD BIOS file at the right location (see above).
  - Place your N64DD disk ROMs in `/userdata/roms/n64dd`. They should have the extension `.ndd`.
  - While hovering over the game in the gamelist, press `[SELECT]` and set the emulator to `libretro: Parallel N64` and the Graphics API to `Vulkan`.
  - Then you can launch the game from EmulationStation

Emulators/configuration are the same as the regular N64 emulators.