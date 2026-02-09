# Adobe Flash Player

**Source:** https://wiki.batocera.org/systems:flash  
**Last fetched:** 2025-12-06 16:18:56

---

# Adobe Flash Player
The ubiquitous Adobe Flash Player, mainstay of popular browser-based games and animations which peaked during the early 2000s. Includes titles such as [Bloons Tower Defense](https:*ninjakiwi.com/Games/Tower-Defense/Bloons-Tower-Defense.html), [QWOP](http:*www.foddy.net/Athletics.html) and N.

First released by FutureWave as "FutureSplash Animator" ((Technically, SmartSketch was the "first" iteration, but its functionality and scope was a far cry from what Flash would eventually become.)) in 1993, who offered to sell the platform to Adobe Systems in 1995. Adobe initially declined the offer. It didn't really start gaining traction until FutureWave was acquired by Macromedia in 1996, who then renamed the platform to "Macromedia Flash Player". In an ironic series of events, Adobe then acquired Macromedia, and ended up inheriting the entire Macromedia product line which included their Flash player. Adobe continued development of it from 2005 and the rest is history.

Tools to develop Flash media were fleshed out and widely available, encouraging professional studios and amateur devs alike to develop software using it. Popular sites such as Newgrounds, Miniclip and Armor Games would host almost exclusively Flash-based content. Most browser came with built-in or easy to install plugins to play Flash media, and it being one of the most easily accessible and portable platforms, it quickly rose to be the standard for interactive web applications. YouTube initially used Flash to play their videos.

As web browser engines and JavaScript matured, Flash's functionality was seen as redundant and development slowed down on the platform. Due to this, and the increasing security flaws, Adobe officially deprecated Flash in 2017 and opted to focus on the Adobe Air platform. Flash support was removed from most mainstream browsers circa 2021. ((Except in China.))

This system scrapes metadata for the "flash" group and loads the `flash` set from the currently selected theme, if available.

### Quick reference
- **Accepted ROM formats:** `.swf`
- **Folder:** `/userdata/roms/flash`

| Emulators |
| [Lightspark](#lightspark) |
| [ruffle](#ruffle) |

## BIOS
No Adobe Flash Player emulator in Batocera needs a BIOS file to run.

## Game files
Place your Adobe Flash Player SWFs in `/userdata/roms/flash`.

## Emulators
### Lightspark
Lightspark is an LGPLv3 licensed Flash Player and browser plugin written in C++/C that runs on Linux and Windows. It aims to support all of Adobe's Flash formats. 

#### Lightspark configuration
Standardized features available to all cores of this emulator: `flash.videomode`, `flash.padtokeyboard`, `flash.decoration`

### ruffle
[ruffle](https://ruffle.rs/) is a Flash Player emulator built in the Rust programming language. It also comes in browser extension form, although most websites now have depreciated actually using it on the live web.

#### ruffle configuration
Standardized features available to all cores of this emulator: `flash.videomode`, `flash.padtokeyboard`, `flash.decoration`

## Controls
Being intended to be played in a web browser, most games only support keyboard and mouse input. However, it was possible for certain games to have native joystick support, although this was a rarity.

Is Joy2Key implemented?

Here are the default Adobe Flash Player's controls shown on a [Batocera Retropad](:configure_a_controller):

## Troubleshooting
### Further troubleshooting
For further troubleshooting, refer to the [generic support pages](:support).