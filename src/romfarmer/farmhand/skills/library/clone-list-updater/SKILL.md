---
name: clone-list-updater
description: Maintain Retool clone lists and metadata when DAT files are updated — detect renames, validate references, auto-patch searchTerms
version: 1.0.0
category: maintenance
author: builtin
tags: [retool, clone-list, dat, 1g1r, maintenance, automation]
platforms: [wii, wiiu, gc, n64, psx, ps2, saturn, dreamcast]
params:
  old_dat:
    type: path
    required: true
    description: Path to older DAT version (baseline)
  new_dat:
    type: path
    required: true
    description: Path to newer DAT version (updated)
  clonelist:
    type: path
    required: true
    description: Path to Retool clone list JSON to maintain
  metadata_output:
    type: path
    required: false
    description: Optional output path for generated metadata JSON
  dry_run:
    type: boolean
    default: true
    description: Preview patches without writing (set false to apply)
preconditions:
  - dat_files_exist
  - clonelist_exists
tools_used:
  - clonelist_diff
  - clonelist_validate
  - clonelist_patch
  - clonelist_metadata_generate
---

# Clone List Updater

## When to use
After downloading a new DAT release (Redump, No-Intro) for a platform that
has an existing Retool clone list. This skill detects what changed between
the old and new DAT, validates the clone list against the new DAT, and
auto-patches searchTerms that broke due to title renames.

## Typical triggers
- New Redump monthly release with updated game names
- No-Intro DAT pack update
- Clone list validation shows broken references after DAT update

## Steps
1. **Diff DATs** — Compare old and new DAT by hash (SHA1/MD5/CRC).
   Produces a rename manifest showing which games were renamed,
   added, or removed.

2. **Validate clone list** — Check all searchTerms against the NEW DAT.
   Report unmatched terms with fuzzy suggestions. This catches both
   rename-related breaks and pre-existing issues.

3. **Review diff** — Examine renames for correctness. Most are safe
   title corrections, punctuation fixes, or region tag updates.
   Flag any that look like data errors.

4. **Patch clone list** — Apply rename-based fixes to searchTerms.
   Start with `--dry-run` to preview, then apply. Only touches
   searchTerms that exactly match a renamed game's base title.

5. **Generate metadata** — Auto-derive language and region metadata
   from the new DAT's game names. Compare against existing metadata
   to spot gaps.

## Decision points
- If a rename changes the base title significantly (not just punctuation),
  verify the game identity before patching
- Additions to the DAT may need new clone list groups — flag these for
  manual review
- Removals are rare (dumps proven bad) — log but don't auto-act

## What it automates (95% of changes)
- Title corrections: "Populous - the Beginning" → "Populous - The Beginning"
- Punctuation fixes: "Let's Tap!" → "Let's Tap"
- Region tag updates: "(USA)" → "(USA, Europe)"
- Language tag additions: new "(En,Fr,De)" suffix
- Metadata language derivation from filename patterns

## What still needs human review (5%)
- Brand new dump groups (3 per year for Wii)
- Complex multi-title splits (game + DLC combos)
- Cross-source tracking (Redump vs No-Intro title differences)
