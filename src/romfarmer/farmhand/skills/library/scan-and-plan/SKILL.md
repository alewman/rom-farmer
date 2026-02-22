---
name: scan-and-plan
description: Connect to a target, perform full scan, and generate an optimal deployment plan
version: 1.0.0
category: workflow
author: builtin
tags: [workflow, scan, plan, first-run, discovery]
targets: [batocera, rocknix]
params:
  host:
    type: string
    required: true
    description: Target IP or hostname
  user:
    type: string
    default: root
    description: SSH username
  password:
    type: string
    default: linux
    description: SSH password (Batocera default is 'linux')
  reserve_gb:
    type: number
    default: 20
    description: GB to keep free on each volume
preconditions:
  - target_reachable
tools_used:
  - farmhand_connect
  - farmhand_scan_target
  - farmhand_generate_plan
---

# Scan and Plan

## When to use
First interaction with a new target. This skill discovers everything about
the target — hardware, storage layout, existing ROMs, emulator capabilities —
then generates an optimal deployment plan that fits within available space.

## Steps
1. Connect to the target via SSH and verify connectivity
2. Run a full scan (system info, volumes, capabilities, existing ROMs)
3. Review the scan results — pay attention to volume roles and free space
4. Generate a deployment plan with sensible budget defaults
5. Review the plan before proceeding to deployment

## Decision points
- If the target has multiple volumes, the planner assigns small platforms to
  the primary volume and large/budgeted platforms to secondary volumes
- If a volume has less than the reserve threshold free, it's excluded
- The agent should review the plan and adjust budgets before deploying

## Tips
- For Batocera targets, the default user is `root` with password `linux`
- RockNIX targets typically use `root` with no password (key auth)
- Run this skill again after major changes (new drive, OS update)
