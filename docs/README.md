# ROM Farmer Documentation

## Quick Start

- **[ROADMAP.md](ROADMAP.md)** - Project roadmap and future plans

## User Guides

Essential documentation for using ROM Farmer:

| Document | Description |
|----------|-------------|
| [USER_GUIDE.md](guides/USER_GUIDE.md) | Complete user guide |
| [INSTALLATION.md](guides/INSTALLATION.md) | Installation instructions |
| [QUICK_REFERENCE.md](guides/QUICK_REFERENCE.md) | Quick command reference |
| [TROUBLESHOOTING.md](guides/TROUBLESHOOTING.md) | Common issues and solutions |
| [ADVANCED-WORKFLOWS.md](guides/ADVANCED-WORKFLOWS.md) | Advanced usage patterns |
| [WORKFLOW.md](guides/WORKFLOW.md) | Pipeline workflow overview |

## Reference Documentation

Technical reference for developers and advanced users:

### Architecture
| Document | Description |
|----------|-------------|
| [ARCHITECTURE_PHASE7.md](reference/ARCHITECTURE_PHASE7.md) | Current architecture overview |
| [PROCESSOR-ARCHITECTURE.md](reference/PROCESSOR-ARCHITECTURE.md) | Pipeline processor design |
| [TRANSFORM_PIPELINE_ARCHITECTURE.md](reference/TRANSFORM_PIPELINE_ARCHITECTURE.md) | File transformation system |
| [HOOKS_SYSTEM.md](reference/HOOKS_SYSTEM.md) | Plugin/hooks system |

### DAT Files & Matching
| Document | Description |
|----------|-------------|
| [DAT_FILES.md](reference/DAT_FILES.md) | DAT file format reference |
| [MD5_DAT_MATCHING.md](reference/MD5_DAT_MATCHING.md) | Hash-based matching |
| [MD5_MATCHING_FLOW.md](reference/MD5_MATCHING_FLOW.md) | Matching flow diagrams |
| [MD5_FOREVER_DATS.md](reference/MD5_FOREVER_DATS.md) | Forever DAT integration |

### Platform-Specific
| Document | Description |
|----------|-------------|
| [PS3_TARGETS_AND_PS3NETSRV.md](reference/PS3_TARGETS_AND_PS3NETSRV.md) | PS3 JB format support |
| [PS3_DLC_UPDATE_INTEGRATION.md](reference/PS3_DLC_UPDATE_INTEGRATION.md) | PS3 DLC/updates |
| [nps-unified-architecture.md](reference/nps-unified-architecture.md) | NoPayStation integration |
| [TARGET_PLATFORMS.md](reference/TARGET_PLATFORMS.md) | Supported target devices |

### Features
| Document | Description |
|----------|-------------|
| [ORGANIZATION.md](reference/ORGANIZATION.md) | File organization styles |
| [MEDIA_FILTERING_FEATURE.md](reference/MEDIA_FILTERING_FEATURE.md) | Selection filters |
| [ROM_TRANSFORMATION_TRACKING.md](reference/ROM_TRANSFORMATION_TRACKING.md) | Transformation history |
| [RETOOL_DAT_INVENTORY.md](reference/RETOOL_DAT_INVENTORY.md) | Retool DAT inventory |

## Configuration Examples

- **[selection-filters-examples.yaml](selection-filters-examples.yaml)** - Selection filter examples

## Archive

Historical documentation from development phases:

- **[archive/phases/](archive/phases/)** - Phase completion reports
- **[archive/implementation/](archive/implementation/)** - Implementation details
- **[archive/research/](archive/research/)** - Research and analysis notes

---

## Directory Structure

```
docs/
├── README.md              # This file
├── ROADMAP.md            # Project roadmap
├── guides/               # User-facing guides
│   ├── USER_GUIDE.md
│   ├── INSTALLATION.md
│   ├── QUICK_REFERENCE.md
│   ├── TROUBLESHOOTING.md
│   ├── ADVANCED-WORKFLOWS.md
│   └── WORKFLOW*.md
├── reference/            # Technical reference
│   ├── ARCHITECTURE*.md
│   ├── DAT_FILES.md
│   ├── MD5_*.md
│   ├── PS3_*.md
│   └── ...
└── archive/              # Historical docs
    ├── phases/           # Phase reports
    ├── implementation/   # Implementation notes
    └── research/         # Research documents
```
