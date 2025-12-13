# SNES MSU-1

**Source:** https://wiki.batocera.org/systems:snes-msu1  
**Last fetched:** 2025-12-06 16:19:48

---

# SNES MSU-1
There was going to be a disc-based add-on for the SNES just like the original Famicom's Disk System add-on. Nintendo was going to collaborate with the small and local but well-known hardware manufacturer Sony at the time, and despite getting far into the development phase, the project was cancelled due to licensing disagreements. [I wonder what Sony did with that disc-based video-game console prototype they were working on?](systems:psx)

Although a prototype unit was discovered and repaired, it wasn't finished and had severe limitations. The MSU-1 is a fan-made custom hardware specification to emulate what would be believed to be capable of the ill-fated SNES-CD. It's even compatible with a real SNES!

Of course, no commercial games have been released for the SNES MSU-1, but there have been romhacks and fan-patches that can utilize it. Place your patched roms into the `roms/snes-msu1` folder to add them. They'll even get their own system entry (though most themes don't seem to support it yet), which you can group with the SNES system using custom collections. The PocketSNES emulator doesn't support MSU-1 patched ROMs.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Cores available:** [libretro: pocketsnes](#libretro:_pocketsnes), [libretro: snes9x_next](#libretro:_snes9x_next), [libretro: snes9x](#libretro:_snes9x), [libretro: bsnes](#libretro:_bsnes), [libretro: bsnes_hd](#libretro:_bsnes_hd)
- **Folder:** `/userdata/roms/snes-msu1`
- **Accepted ROM formats:** `.smc`, `.sfc`, `.squashfs`, `.zip`, `.7z`

## BIOS
No SNES MSU-1 emulator in Batocera needs the BIOS to run.

## ROMs
Place your SNES MSU-1 `smc` or `sfc` ROMs in `/userdata/roms/snes-msu1`. ROMs can be compressed into `zip` or `7z` files.