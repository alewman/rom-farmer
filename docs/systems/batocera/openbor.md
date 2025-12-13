# Open Beats of Rage

**Source:** https://wiki.batocera.org/systems:openbor  
**Last fetched:** 2025-12-06 16:19:28

---

# Open Beats of Rage
Beats of Rage (OpenBOR) is a fan-made tribute game to Sega's Streets of Rage series. It supplants the original graphics and characters with resources taken from The King of Fighters series, albeit with tongue in cheek renames. Originally developed by Senile Team, the underlying engine powering Beats of Rage later went on to become the Open Beats of Rage (OpenBOR) game engine project.

This system scrapes metadata for the "openbor" group and loads the `openbor` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [openbor](#openbor)
- **Cores available:** [openbor: openbor4432](#openbor:_openbor4432), [openbor: openbor6330](#openbor:_openbor6330), [openbor: openbor6412](#openbor:_openbor6412), [openbor: openbor6510](#openbor:_openbor6510)
- **Folder:** `/userdata/roms/openbor`
- **Accepted ROM formats:** `.pak`

## BIOS
No OpenBOR emulator in Batocera needs a BIOS file to run.

## Game files
<csv>
Emulator, ROM Folder, Extension, Config [and/or Savestates]
openbor, /userdata/roms/openbor, .pak, /userdata/saves/openbor/[PAK-Directory]
Upstream version,,, /userdate/system/configs/openbor/config.ini
openbor4432, /userdata/roms/openbor, .pak, /userdata/saves/openbor/[PAK-Directory]
Version 4432,,, /userdate/system/configs/openbor/config4432.ini
</csv>

OpenBOR games are usually non-commercial games made by fans.

However, some of them are ripping sprites and sounds from other games, which actually are under copyrights. 

As for any other type of ROM, Google and search engines are the best way to find PAKs for OpenBOR. 

## Configuration
Standardized features available to all cores of this emulator: `openbor.videomode`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| **SCREEN RATIO `openbor.ratio`** | Stretch games to full-screen, but may distort the aspect ratio\\ => Normal `0`, Stretch `1`. |
| **VIDEO FILTER `openbor.filter`** | Apply a particular visual effect\\ => Simple 2x `0`, Bilinear `1`, 2xSaI `2`, Super 2xSaI `3`, Super Eagle `4`, Advance Mame2x `5`, Lq2x `6`, Hq2x `7`, ScanLines `8`, ScanLines TV `9`, TV 2x `10`, Dot Matrix `11`. |

# Controls
Here are the default OpenBOR's controls shown on a [Batocera Retropad](:configure_a_controller):

```

        UP # MOVEUP                A # ATTACK1
        DOWN # MOVEDOWN            X # ATTACK2
        LEFT # MOVELEFT            Y # ATTACK3
        RIGHT # MOVERIGHT          B # JUMP
        SELECT # SPECIAL          R1 # ATTACK4

                     START # START

```

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).