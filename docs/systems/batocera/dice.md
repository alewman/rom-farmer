# DICE

**Source:** https://wiki.batocera.org/systems:dice  
**Last fetched:** 2025-12-06 16:18:52

---

# DICE
[DICE](https://adamulation.blogspot.com/) is a Discrete Integrated Circuit Emulator. It emulates computer systems that lack any type of CPU, consisting only of discrete logic components.

It was first released in 2008 as a circuit-level simulation of Pong.  [libretro: dice](https://github.com/mittonk/dice-libretro) is a libretro port.

This system scrapes metadata for the "dice, arcade" group(s) and loads the `dice` set from the currently selected theme, if available.

### Quick reference
- **Emulator:** [RetroArch](#retroarch)
- **Core:** [libretro: dice](#libretro:_dice)
- **Folder:** `/userdata/roms/dice`
- **Accepted ROM formats:** `.zip`, `.dmy`

## BIOS
No DICE emulator in Batocera needs a BIOS file to run.

## ROMs
Place your DICE ROMs in `/userdata/roms/dice`.

Games without any ROM component use .dmy files as dummy launchers.
Some games (pong, breakout, pinpong, etc) do not have any ROM on the board at all. For these, copy the dummy launcher file from dummy_files to your ROM folder; these have a correct name (for example, pong.dmy) that will get RetroArch to set up lr-dice for the correct game.

For more info: https://wiki.batocera.org/arcade

## Emulators
### RetroArch
RetroArch has [its own page](emulators:retroarch).

#### libretro: dice
As of Batocera v42, the DICE system is supported.

| ES setting name `batocera.conf_key` | Description => ES option `key_value` |
| Settings that apply to all systems this core supports ||
| **USE MOUSE POINTER FOR PADDLE 1 `global.ttl_use_mouse_pointer_for_paddle_1`** | Use the system mouse pointer as paddle controller 1.  Does not let you choose a specific mouse if you have several.\\ => Off `disabled`, On `enabled`. |
| **USE MOUSE FOR PADDLE 1 `global.ttl_retromouse_paddle0`** | Use a specific mouse for Paddle 1, chosen by Port 1's Mouse Index.\\ => Off `disabled`, On `enabled`. |
| **USE MOUSE FOR PADDLE 2 `global.ttl_retromouse_paddle1`** | Use a specific mouse for Paddle 2, chosen by Port 2's Mouse Index.\\ => Off `disabled`, On `enabled`. |
| **USE MOUSE FOR PADDLE 3 `global.ttl_retromouse_paddle2`** | Use a specific mouse for Paddle 3, chosen by Port 3's Mouse Index.\\ => Off `disabled`, On `enabled`. |
| **USE MOUSE FOR PADDLE 4 `global.ttl_retromouse_paddle3`** | Use a specific mouse for Paddle 4, chosen by Port 4's Mouse Index.\\ => Off `disabled`, On `enabled`. |
| **MOUSE AXIS FOR PADDLE 1 HORIZONTAL `global.ttl_retromouse_paddle0_x`** | Mouse axis for player 1, horizontal screen motion.\\ => X `x`, Y `y`. |
| **MOUSE AXIS FOR PADDLE 1 VERTICAL `global.ttl_retromouse_paddle0_y`** | Mouse axis for player 1, vertical screen motion.\\ => X `x`, Y `y`. |
| **MOUSE AXIS FOR PADDLE 2 HORIZONTAL `global.ttl_retromouse_paddle1_x`** | Mouse axis for player 2, horizontal screen motion.\\ => X `x`, Y `y`. |
| **MOUSE AXIS FOR PADDLE 2 VERTICAL `global.ttl_retromouse_paddle1_y`** | Mouse axis for player 2, vertical screen motion.\\ => X `x`, Y `y`. |
| **MOUSE AXIS FOR PADDLE 3 HORIZONTAL `global.ttl_retromouse_paddle2_x`** | Mouse axis for player 3, horizontal screen motion.\\ => X `x`, Y `y`. |
| **MOUSE AXIS FOR PADDLE 3 VERTICAL `global.ttl_retromouse_paddle2_y`** | Mouse axis for player 3, vertical screen motion.\\ => X `x`, Y `y`. |
| **MOUSE AXIS FOR PADDLE 4 HORIZONTAL `global.ttl_retromouse_paddle3_x`** | Mouse axis for player 4, horizontal screen motion.\\ => X `x`, Y `y`. |
| **MOUSE AXIS FOR PADDLE 4 VERTICAL `global.ttl_retromouse_paddle3_y`** | Mouse axis for player 4, vertical screen motion.\\ => X `x`, Y `y`. |
| **PADDLE D-PAD SENSITIVITY `global.ttl_paddle_keyboard_sensitivity`** | Sensitivity when using D-pad for a paddle.\\ => 125 `125`, 250 `250`, 375 `375`, 500 `500`. |
| **PADDLE ANALOG STICK SENSITIVITY `global.ttl_paddle_joystick_sensitivity`** | Sensitivity when using analog stick for a paddle.\\ => 125 `125`, 250 `250`, 375 `375`, 500 `500`. |
| **PADDLE MOUSE SENSITIVITY `global.ttl_retromouse_paddle_sensitivity`** | Sensitivity when using mouse for a paddle.\\ => 25 `25`, 50 `50`, 75 `75`, 100 `100`, 125 `125`, 250 `250`, 375 `375`, 500 `500`. |
| **WHEEL SENSITIVITY `global.ttl_wheel_keyjoy_sensitivity`** | Sensitivity when using D-pad or analog stick for a wheel.\\ => 125 `125`, 250 `250`, 375 `375`, 500 `500`. |
| **THROTTLE SENSITIVITY `global.ttl_throttle_keyjoy_sensitivity`** | Sensitivity when using D-pad or analog stick for a throttle.\\ => 125 `125`, 250 `250`, 375 `375`, 500 `500`. |
| **DIP SWITCH 1 `global.ttl_dipswitch_1`** | Setting for DIP switch 1.\\ => Default `-1`, 0 `0`, 1 `1`. |
| **DIP SWITCH 2 `global.ttl_dipswitch_2`** | Setting for DIP switch 2.\\ => Default `-1`, 0 `0`, 1 `1`. |
| **DIP SWITCH 3 `global.ttl_dipswitch_3`** | Setting for DIP switch 3.\\ => Default `-1`, 0 `0`, 1 `1`. |
| **DIP SWITCH HEX 1 `global.ttl_dipswitch16_1`** | Setting for 16-position DIP switch number 1.\\ => Default `-1`, 0 `0`, 1 `1`, 2 `2`, 3 `3`, 4 `4`, 5 `5`, 6 `6`, 7 `7`, 8 `8`, 9 `9`, 10 `10`, 11 `11`, 12 `12`, 13 `13`, 14 `14`, 15 `15`. |
| **DIP SWITCH HEX 2 `global.ttl_dipswitch16_2`** | Setting for 16-position DIP switch number 2.\\ => Default `-1`, 0 `0`, 1 `1`, 2 `2`, 3 `3`, 4 `4`, 5 `5`, 6 `6`, 7 `7`, 8 `8`, 9 `9`, 10 `10`, 11 `11`, 12 `12`, 13 `13`, 14 `14`, 15 `15`. |

You can find DIP switch values at [DIP Switches](https://github.com/mittonk/dice-libretro/blob/main/dipswitches.md).
## Controls
Here are the default DICE controls shown on a [Batocera RetroPad](:configure_a_controller):

DICE also supports one or several mice or mice-like spinners as paddle controllers:
- Easy: One mouse can be used for Paddle 1. Use `ADVANCED SYSTEM OPTIONS` -> `USE MOUSE POINTER FOR PADDLE 1`. You'll still want a keyboard or gamepad handy to have enough buttons.
- Somewhat advanced: Multiple mice are supported using Batocera's input drivers, see [retromouse.md](https://github.com/mittonk/dice-libretro/blob/main/retromouse.md) and use `ADVANCED SYSTEM OPTIONS` -> `USE MOUSE FOR PADDLE 1` and similar in EmulationStation to set options.
## Troubleshooting
### Vertical games like Breakout and Pin Pong are stretched
Set `ADVANCED GAME OPTIONS` -> `GAME ASPECT RATIO` -> `CORE PROVIDED` for these games.

This is more likely with non-default bezels.
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).