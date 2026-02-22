---
name: deploy-platform-budget
description: Build and deploy a disc-based platform within a storage budget
version: 1.0.0
category: deployment
author: builtin
tags: [deployment, budget, disc-based, build-and-deploy]
platforms: [psx, ps2, dreamcast, saturn, 3do, pcenginecd, segacd, psp, 3ds, xbox]
targets: [batocera, rocknix]
params:
  platform:
    type: string
    required: true
    description: ROM platform to deploy (e.g., psx, ps2, dreamcast)
  budget_gb:
    type: number
    required: true
    description: Maximum GB to allocate for this platform
  target:
    type: string
    required: true
    description: Target name or host
  strategy:
    type: string
    default: rating_budget
    description: Selection strategy for choosing which games to include
    enum: [rating_budget, curated_list, random]
  volume:
    type: string
    default: ""
    description: Target volume mount (empty = let planner decide)
preconditions:
  - target_connected
  - platform_in_source
  - rom_source_available
tools_used:
  - farmhand_connect
  - farmhand_generate_plan
  - farmhand_deploy
  - farmhand_remote_exec
---

# Deploy Platform within Budget

## When to use
Use this skill when deploying a disc-based platform (PSX, PS2, Dreamcast,
Saturn, etc.) that exceeds available storage. The full library is too large,
so we select the best titles within a budget using rom-farmer's rating
system.

## Steps
1. Verify target connectivity
2. Check available space on target volumes
3. Generate a deployment plan with the platform budgeted to {{budget_gb}} GB
4. Trigger rom-farmer build with budget selection strategy
5. Deploy build output to the target via SFTP delta sync
6. Verify transfer integrity — file count and total size match
7. Trigger EmulationStation ROM rescan on the target

## Budget guidelines (from experience)
| Platform   | Full Size | Sensible Budget | Notes                        |
|-----------|-----------|-----------------|------------------------------|
| PSX       | ~513 GB   | 40–80 GB        | Top 200-400 titles           |
| PS2       | ~2.97 TB  | 60–120 GB       | Top 100-200 titles           |
| PSP       | ~416 GB   | 30–60 GB        | Top 150-300 titles           |
| Dreamcast | ~136 GB   | 40–80 GB        | Top 200-400 titles           |
| Saturn    | ~86 GB    | 30–50 GB        | Many JP-only gems            |
| 3DS       | ~454 GB   | 30–60 GB        | Mostly first-party           |
| Xbox      | ~351 GB   | 30–60 GB        | Exclusives only              |

## Known issues
- CHD output sizes are estimates until build completes
- Multi-disc games need .m3u file generation (rom-farmer handles this)
- Budget strategy requires metadata (ratings); ensure metadata stage ran
- Some platforms have region-locked titles worth including (see curated-essentials)
