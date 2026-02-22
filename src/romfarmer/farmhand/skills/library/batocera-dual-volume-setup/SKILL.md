---
name: batocera-dual-volume-setup
description: Set up symlinks between /userdata and secondary volumes for multi-disk Batocera builds
version: 1.0.0
category: target
author: builtin
tags: [batocera, multi-disk, symlinks, volume-management, setup]
targets: [batocera]
params:
  host:
    type: string
    required: true
    description: Batocera target IP or hostname
  secondary_mount:
    type: string
    default: /media/int2tbhd
    description: Mount point of the secondary volume
  platforms_to_move:
    type: list
    default: [ps2, psx, xbox, dreamcast, saturn, xbox360]
    description: Platforms to symlink from /userdata/roms to secondary volume
preconditions:
  - target_connected
  - secondary_volume_mounted
tools_used:
  - farmhand_connect
  - farmhand_remote_exec
  - farmhand_scan_target
artifacts:
  - filename: setup-rom-symlinks.sh
    description: Shell script that creates symlinks from /userdata/roms/<platform> to secondary volume
    artifact_type: script
    executable: true
  - filename: verify-symlinks.sh
    description: Verification script that checks all symlinks are valid
    artifact_type: script
    executable: true
---

# Batocera Dual-Volume Symlink Setup

## When to use
When a Batocera system has multiple storage devices (e.g., NVMe + HDD) and
you want large disc-based platforms stored on the secondary volume while
keeping them visible to EmulationStation through symlinks in /userdata/roms/.

Batocera reads ROM paths from /userdata/roms/<system>/. If the actual files
live on /media/int2tbhd/roms/ps2/, you create:
  /userdata/roms/ps2 → /media/int2tbhd/roms/ps2

This is transparent to EmulationStation and lets you spread ROMs across
multiple drives without reconfiguring anything.

## Steps
1. Connect to the target and verify both volumes are mounted
2. Create ROM directories on the secondary volume
3. Move existing ROM files from /userdata/roms/<platform> to secondary
4. Create symlinks from /userdata/roms/<platform> → secondary
5. Verify symlinks resolve correctly
6. Test by listing ROMs through the symlink

## Important notes
- Always verify the secondary volume is mounted before creating symlinks
- If /userdata/roms/<platform> already has files, move them first
- The setup script is idempotent — safe to run multiple times
- After OS updates, check that symlinks survived (Batocera sometimes resets /userdata)
- Use verify-symlinks.sh periodically to catch broken links

## Artifact: setup-rom-symlinks.sh
The bundled script handles the full workflow: creates directories on the
secondary volume, moves existing ROMs, creates symlinks, and verifies.
Upload it to the target and run with:
```bash
chmod +x setup-rom-symlinks.sh
./setup-rom-symlinks.sh /media/int2tbhd ps2 psx dreamcast saturn
```
