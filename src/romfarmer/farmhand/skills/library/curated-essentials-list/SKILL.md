---
name: curated-essentials-list
description: Maintain and apply curated lists of must-have games that transcend regional releases
version: 1.0.0
category: curation
author: builtin
tags: [curation, game-lists, cultural, essentials, japan-only, regional]
platforms: []
targets: []
params:
  platform:
    type: string
    required: true
    description: Platform to get/apply the essentials list for
  action:
    type: string
    default: show
    description: What to do — show, apply, or add
    enum: [show, apply, add]
  games_to_add:
    type: list
    default: []
    description: Game names to add to the list (for action=add)
preconditions: []
tools_used:
  - farmhand_remote_exec
artifacts:
  - filename: essentials/saturn.yaml
    description: Saturn essentials including JP-only gems
    artifact_type: list
  - filename: essentials/psx.yaml
    description: PSX essentials including PAL/JP exclusives
    artifact_type: list
  - filename: essentials/snes.yaml
    description: SNES/SFC essentials including Famicom exclusives
    artifact_type: list
  - filename: essentials/genesis.yaml
    description: Genesis/Mega Drive essentials including JP exclusives
    artifact_type: list
---

# Curated Essentials Lists

## When to use
When building or reviewing a ROM collection, certain games are culturally
significant enough to include regardless of regional availability or rating
scores. These curated lists capture institutional knowledge about:

- **Japan-only masterpieces** that never got Western releases
- **PAL exclusives** with unique content
- **Region variants** where one version is definitively better
- **Hidden gems** that rating systems undervalue
- **Historical landmarks** every serious collector should have

## How it works
Each platform has a YAML file in `essentials/` listing games with:
- The canonical rom-farmer name pattern (for matching against DATs)
- Why it's essential (brief justification)
- Region preference (which release to pick)
- Category (masterpiece, hidden-gem, historical, regional-exclusive)

## Usage
- **show**: Display the essentials list for a platform
- **apply**: Cross-reference against a rom-farmer build to ensure all
  essentials are included, adding them even if they fall outside a
  budget or 1G1R region filter
- **add**: Add new games to the essentials list (agent can do this
  after researching a platform)

## Philosophy
Rating-based budget selection is great for the bulk of a collection, but
it misses games that are important for reasons algorithms can't capture:
- Cultural significance ("this defined a genre")
- Technical achievement ("first game to do X")
- Community consensus that transcends review scores
- Japan-exclusive titles that Western databases underrate

These lists are living documents — the agent should add to them as it
learns about platforms through research and user feedback.

## Contributing to lists
The agent should add games when:
1. A user mentions a game they consider essential
2. Research reveals historically significant titles
3. Community consensus (forums, wiki) identifies must-haves
4. A title is consistently recommended despite low aggregate scores
