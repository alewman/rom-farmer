Emulation Station in Retrobat Observations

---

FIXED: Sorting isn't working right.
   * Root cause: ARRM scraper embeds a numeric sort key in the <sortname> field:
     "3595 =-  Game Name" — ES treats this as a literal string so everything sorts
     to a random position instead of alphabetically.
   * NES worked because its gamelist was not ARRM-scraped (no sortname fields).
   * Fix applied 2026-05-11: scripts/validate_gamelist.py --fix-sortnames
     Stripped the numeric prefix from ~21,000 sortname fields across 30 platforms.
     If the cleaned value equaled <name>, the <sortname> element was removed entirely.
   * All 63 platforms now have clean sortnames. Alphabetical sorting is correct in ES.

---

Games without metadata - hold off on this until we really get metadata figured out
   * It seems to me that games without metadata should be moved off into maybe an Extras folder?
   * Reason, all the popular games are going to have an image and some description so whatever these are - they are probably not that important.
   * Use: python3 scripts/validate_gamelist.py --stats /data/emu/roms-retrobat
     to see desc/image/rating/video coverage % per platform.

---

FIXED: The ZZZ games
   * There are a lot of ZZZ(notgame):#NONGAME titles in the systems.
   * These are BIOS files, multicarts, and hardware test cartridges — not real games.
   * Fix applied 2026-05-11: scripts/validate_gamelist.py --fix-nongames
     Set <hidden>true</hidden> on all 398 ZZZ(notgame) entries across all platforms.
     Hidden entries don't appear in ES game lists (but remain in the XML and can be
     toggled visible via Show Hidden if ever needed).

---

Systems without Metadata (PS3)
   * PS3 games have no images or video in their gamelist entries (image: 0%).
   * Root cause confirmed: PS3 games are folder-based (.ps3 directories). The metadata
     generator hashes the largest inner file but ScreenScraper IDs games by folder name.
     The ".ps3" extension suffix may also prevent name matching.
   * Still open — needs research into how to scrape folder-format platforms.

---

Sega Master System duplicate names
   * Many games appear multiple times with the same display name but different ROM files:
     12x "3 In 1 - The Best Game Collection (a)", 6x "8 In 1 - The Best Game Collection (a)", etc.
   * These are legitimately different ROM variants (region codes A/B/C/D/E/F, different revisions).
     The scraper matched them all to the same ScreenScraper entry and gave them the same <name>.
   * Informational — not a data corruption issue. ES will show all of them.
   * Possible future fix: append region/revision hint to <name> for disambiguation, or
     use <hidden> to keep only the preferred variant visible.
   * Use: python3 scripts/validate_gamelist.py -v --errors-only roms-retrobat/mastersystem
     to see the full list of duplicate names.

---

Tooling: validate_gamelist.py (scripts/validate_gamelist.py)
   * Created 2026-05-11. Run against all 63 platforms at any time to check health.
   * Checks: XML validity, missing ROM paths, missing media file refs, duplicate paths,
     ARRM bad sortnames, ZZZ nongame visibility, duplicate display names.
   * Flags: --fix-sortnames, --fix-nongames, --stats, -v, --errors-only, --no-media
   * Example: python3 scripts/validate_gamelist.py --errors-only /data/emu/roms-retrobat
