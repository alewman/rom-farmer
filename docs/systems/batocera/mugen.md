# MUGEN

**Source:** https://wiki.batocera.org/systems:mugen  
**Last fetched:** 2025-12-06 16:19:19

---

This article needs some TLC. Read at your own risk.

# MUGEN
MUGEN is a popular, veteran fighting game engine with a huge community behind it. It was developed by Elecbyte, initially released in 1999.

This system scrapes metadata for the "mugen" group and loads the `mugen` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [MUGEN](#mugen)
- **Cores available:** [MUGEN: Lutris](#mugen:_lutris), [MUGEN: Proton](#mugen:_proton)
- **Folder:** `/userdata/roms/mugen`
- **Accepted ROM formats:** `.pc`

## BIOS
No MUGEN emulator in Batocera needs a BIOS file to run.

## Game files
Place your MUGEN game files in `/userdata/roms/mugen`.

They are usually distributed as a folder for Windows PC, with `.exe` files and everything.

  - Rename the folder so that it has a `.pc` extension at the end. For example, if you have a game called `MugenDreamVer1`, copy it to your Batocera machine and rename it to `/userdata/roms/mugen/MugenDreamVer1.pc`.
  - Similarly to [Windows games](systems:windows), you need to create an `autorun.cmd` file that contains the name of the main `.exe` for the Mugen game you want to run. For my example here, the `autorun.cmd` file would contain:

```

CMD=MUGENDreamVer1.exe

```

## Emulators
### MUGEN
The bonafide engine itself. It is run via Lutris or Proton, your choice.

#### MUGEN configuration
Standardized features available to all cores of this emulator: `mugen.videomode`, `mugen.padtokeyboard`, `mugen.decoration`

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all cores of this emulator ||
| **ESYNC `mugen.esync`** | Can increase performance for games that stress the CPU.\\ => Off `0`, On `1`. |
| **FSYNC `mugen.fsync`** | Can improve frame rates and responsiveness.\\ => Off `0`, On `1`. |
| **PBA `mugen.pba`** | Vastly improves the speed of buffer maps.\\ => Off `0`, On `1`. |
| **VIRTUAL DESKTOP `mugen.virtual_desktop`** | Define the resolution and a new dedicated window.\\ => Off `0`, On `1`. |

## Controls
Here are the default MUGEN's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### My game is misbehaving
Some MUGEN games need a pre-config before run on Batocera.

Open the game configuration file at `/userdata/roms/<mugen game>/data/mugen.cfg` and edit the applicable lines to:

```

GameWidth = 1920
GameHeight = 1080
Depth = 32
FullScreen = 1
RenderMode = OpenGL

```

### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).