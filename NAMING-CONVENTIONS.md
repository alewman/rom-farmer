# ROM Groomer - Naming Conventions

## Problem Statement

The original project naming was based on No-Intro because that's where it started. However, the project now supports both No-Intro and Redump sets, making names like `nointro-processor.sh` and `nointro.py` misleading.

## Proposed Naming Conventions

### 1. DAT File Folders

**Current Structure** (Inconsistent):
```
dats/
├── nointro/                      # Raw No-Intro DATs
├── redump/                       # Raw Redump DATs
├── retool/                       # Retool output (unclear source)
├── retool.all/                   # Retool output (unclear source)
├── nointro.retool.1g1r.all/      # ✓ Clear: No-Intro + Retool
├── nointro.retool.1g1r.eng/      # ✓ Clear: No-Intro + Retool
├── nointro.retool.1g1r.usa/      # ✓ Clear: No-Intro + Retool
├── retool.redump.1g1r.eng/       # ✗ Unclear: Should be redump.retool
└── redump.retool.1g1r.usa/       # ✓ Clear: Redump + Retool
```

**Proposed Structure** (Consistent):
```
dats/
├── nointro/                      # Raw No-Intro DATs (original)
├── redump/                       # Raw Redump DATs (original)
├── nointro.retool/               # No-Intro + Retool (all regions)
├── nointro.retool.1g1r.all/      # No-Intro + Retool + 1G1R (all regions)
├── nointro.retool.1g1r.eng/      # No-Intro + Retool + 1G1R (English)
├── nointro.retool.1g1r.usa/      # No-Intro + Retool + 1G1R (USA)
├── redump.retool/                # Redump + Retool (all regions)
├── redump.retool.1g1r.all/       # Redump + Retool + 1G1R (all regions)
├── redump.retool.1g1r.eng/       # Redump + Retool + 1G1R (English)
└── redump.retool.1g1r.usa/       # Redump + Retool + 1G1R (USA)
```

**Naming Pattern**:
```
{source}.{tool}.{filter}.{region}/

Where:
  source = nointro | redump
  tool   = retool | (other tools in future)
  filter = 1g1r | (other filters)
  region = all | eng | usa | jpn | etc.
```

### 2. Python Modules

**Current Naming** (Source-specific):
```python
romgroomer.parsers.nointro   # Only handles No-Intro
romgroomer.parsers.redump    # Only handles Redump
```

**Proposed Naming** (Format-agnostic):
```python
# Generic parsers based on format, not source
romgroomer.parsers.cartridge     # Cartridge-based (NES, SNES, GB, GBA, etc.)
romgroomer.parsers.disc          # Disc-based (PS1, Saturn, Dreamcast, etc.)
romgroomer.parsers.dat           # DAT file parser (works with any source)

# Or keep source-specific but make it clear they're compatible:
romgroomer.parsers.nointro       # No-Intro naming convention
romgroomer.parsers.redump        # Redump naming convention
romgroomer.parsers.tosec         # TOSEC naming convention (future)
```

### 3. Bash Scripts

**Current Naming** (Source-specific):
```bash
nointro-processor.sh             # Misleading - handles Redump too
build-nointro-usa-1g1r.sh        # Specific to No-Intro
```

**Proposed Naming** (Format-agnostic):
```bash
# Generic processor
rom-processor.sh                 # Main ROM processing engine
dat-processor.sh                 # DAT file processing

# Source-specific build scripts
build-{system}-{source}-{region}-1g1r.sh

Examples:
build-nes-nointro-usa-1g1r.sh
build-saturn-redump-usa-1g1r.sh
build-psx-redump-eng-1g1r.sh
```

### 4. Organization Folders

**Current Naming**:
```
filter/Atari - 2600.all.1g1r/    # Missing source
build/Sega - Mega CD.usa.1g1r/   # Missing source
```

**Proposed Naming**:
```
# Include source in folder name for clarity
filter/{System} - {Source}.{region}.1g1r/
build/{System} - {Source}.{region}.1g1r/

Examples:
filter/Atari - 2600 (No-Intro).usa.1g1r/
filter/Sega - Mega CD (Redump).usa.1g1r/
build/Sony - PlayStation (Redump).usa.1g1r/
```

## Migration Strategy

### Phase 1: Python Code (Now)
1. ✅ Rename `parsers/nointro.py` → Keep as is (it IS No-Intro specific)
2. ✅ Create `parsers/redump.py` for Redump-specific parsing
3. ✅ Create `parsers/dat.py` for generic DAT parsing
4. ✅ Keep source-specific parsers, make naming convention explicit

### Phase 2: DAT Folders (Now)
```bash
# Rename inconsistent folders
mv retool.redump.1g1r.eng redump.retool.1g1r.eng
mv retool/ nointro.retool/
mv retool.all/ nointro.retool.all/
```

### Phase 3: Bash Scripts (Later)
```bash
# Create generic wrapper
cp nointro-processor.sh rom-processor.sh

# Update build scripts to use new processor
# Keep old scripts for backward compatibility
```

### Phase 4: Documentation (Now)
- Update all documentation to use consistent naming
- Create migration guide for existing users
- Add naming convention reference

## Recommended Approach

### For Python (Immediate):

**Keep source-specific parsers** because:
1. No-Intro and Redump have different naming conventions
2. Different metadata in filenames
3. Different disc naming (Disc 1 vs Disc 01)
4. Clear separation of concerns

```python
# This is GOOD design:
from romgroomer.parsers.nointro import NoIntroParser
from romgroomer.parsers.redump import RedumpParser

nointro_parser = NoIntroParser()
redump_parser = RedumpParser()
```

**Add generic interface** for flexibility:
```python
from romgroomer.parsers import get_parser

# Auto-detect parser based on filename or explicit source
parser = get_parser("nointro")  # or "redump"
rom = parser.parse(filepath)
```

### For DAT Folders (Immediate):

**Rename to be consistent**:
```bash
# Rename inconsistent folders
cd /data/emu/dats
mv retool.redump.1g1r.eng redump.retool.1g1r.eng
mv retool/ nointro.retool/                    # If it's No-Intro based
mv retool.all/ nointro.retool.all/            # If it's No-Intro based
```

### For Bash Scripts (Optional):

**Option A**: Keep `nointro-processor.sh` as is
- It's a known name, users are familiar
- Just document that it handles both No-Intro and Redump

**Option B**: Create `rom-processor.sh` as new main script
- Keep `nointro-processor.sh` as symlink for backward compatibility
- Update documentation to use new name

## Implementation Plan

### Step 1: Python Module Structure ✅

```python
romgroomer/
├── parsers/
│   ├── __init__.py              # Generic interface
│   ├── base.py                  # BaseParser abstract class
│   ├── nointro.py               # No-Intro specific (keep name)
│   ├── redump.py                # Redump specific (new)
│   └── dat.py                   # DAT file parser (new)
```

### Step 2: Update Configuration ✅

```yaml
# config.yaml
parsers:
  nointro:
    enabled: true
    conventions: "No-Intro"
  redump:
    enabled: true
    conventions: "Redump"

dat_directories:
  nointro:
    raw: "dats/nointro"
    retool_all: "dats/nointro.retool.1g1r.all"
    retool_eng: "dats/nointro.retool.1g1r.eng"
    retool_usa: "dats/nointro.retool.1g1r.usa"
  redump:
    raw: "dats/redump"
    retool_all: "dats/redump.retool.1g1r.all"
    retool_eng: "dats/redump.retool.1g1r.eng"
    retool_usa: "dats/redump.retool.1g1r.usa"
```

### Step 3: Rename DAT Folders

```bash
cd /data/emu/dats
mv retool.redump.1g1r.eng redump.retool.1g1r.eng
```

## Conclusion

**Recommendations**:

1. ✅ **Keep** `parsers/nointro.py` - it IS No-Intro specific
2. ✅ **Create** `parsers/redump.py` - for Redump specific parsing
3. ✅ **Create** `parsers/base.py` - abstract base class
4. ✅ **Rename** inconsistent DAT folders now
5. ⏳ **Consider** renaming bash scripts later (low priority)
6. ✅ **Document** naming conventions clearly

The Python code is actually well-named because the parsers ARE source-specific. The issue is mainly with the DAT folder naming inconsistency, which we should fix now.
