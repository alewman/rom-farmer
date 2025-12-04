# ROM Farmer - Architecture & Vision

## 🎯 Project Goal

Build a **production-grade ROM collection management system** that transforms the chaotic world of ROM preservation into an elegant, automated workflow. Think "Netflix for ROM collections" - users specify what they want, the system builds it perfectly.

## 🌟 The Vision

**For End Users:**
- Click a button, get a perfect ROM collection
- No manual DAT file juggling
- No command-line expertise needed
- Just works™

**For Enthusiasts:**
- Battle-tested automation
- Quality-based selection (ratings, metadata)
- Multi-platform support (NES → PS3)
- Reproducible builds

**For Preservationists:**
- No-Intro/Redump verification
- Atomic multi-disc handling
- Compression with integrity
- Full audit trails

## 🏗️ Three-Layer Architecture

### Layer 1: Core CLI (Production Ready ✅)
**What:** The engine that does the actual work
**Commands:**
```bash
python3 -m romfarmer build run <build-config>
python3 -m romfarmer dat import <dat-file>
python3 -m romfarmer scan <directory>
```

**Responsibilities:**
- DAT file parsing and validation
- ROM scanning with CRC32/MD5/SHA1
- Intelligent filtering (region, language, 1G1R)
- Archive extraction (ZIP, 7z, RAR)
- Format conversion (BIN/CUE → CHD)
- Multi-disc M3U generation
- Compression with verification
- Output organization (flat, rich, balanced)

**Current Status:** Production ready, battle-tested on Saturn, Virtual Boy, PS3

---

### Layer 2: Interactive CLI Wizard (Just Built! 🎉)
**What:** User-friendly discovery and guidance system
**Command:**
```bash
./build-wizard
```

**Responsibilities:**
- Auto-discover available platforms
- Auto-discover selection strategies
- Auto-discover existing build configs
- Guide users through choices with visual tables
- Validate selections before execution
- Generate and run correct CLI commands

**Why This Matters:**
- **Proves the UX flow** - validates what questions to ask
- **Zero documentation needed** - self-explanatory
- **Reusable logic** - discovery functions work for Web UI too
- **Educational** - shows users the actual commands

**Current Status:** Fully functional, ready for user testing

---

### Layer 3: Web UI (Future Roadmap 🚀)
**What:** Public-facing web interface for ROM collection builds
**Concept:**
```
User visits website → Selects platform/options → Submits job → 
Gets download link when complete
```

**Planned Features:**
- Visual config builder (dropdowns, sliders)
- Job queue with progress tracking
- Email notification on completion
- Download portal for results
- Build history and favorites
- Community sharing (build configs)

**Tech Stack (Proposed):**
- **Backend:** FastAPI (async, type-safe)
- **Queue:** Celery + Redis (background jobs)
- **Frontend:** React/Svelte (interactive UI)
- **WebSockets:** Real-time progress streaming
- **Storage:** S3-compatible for builds

**Reuses Layer 2 Logic:**
```python
# Same discovery functions!
platforms = discover_platforms()
selections = discover_selections()

# Same command execution!
subprocess.run(['python3', '-m', 'romfarmer', 'build', 'run', config_name])
```

**Why Users Will Love It:**
- No CLI knowledge required
- Visual feedback and progress bars
- Can build collections from phone/tablet
- Share configs with community
- "One-click" ROM collections

---

## 🎨 Design Principles

### 1. **Composability**
Each layer is independent. Web UI crashes? CLI still works. CLI has bugs? Core still solid.

### 2. **Discoverability**
No hidden features. If a platform exists in `config/platforms/`, it appears in menus automatically.

### 3. **Reproducibility**
Same config file = same output, every time. Perfect for testing and sharing.

### 4. **Quality Over Quantity**
Rating-based selection ensures best games fit within storage budgets.

### 5. **Correctness**
DAT validation guarantees authentic ROMs. No bad dumps, no hacks (unless explicitly wanted).

### 6. **Flexibility**
Support multiple targets (Batocera, RocknIX, MiSTer, custom) from one source.

---

## 📊 Current Implementation Status

### ✅ Completed
- Core pipeline (scan, filter, extract, compress, organize)
- DAT validation (No-Intro, Redump)
- Multi-disc handling (M3U, atomic selection)
- CHD compression with verification
- Rating-based filtering (size budgets)
- Selection strategies (first, last, random, smallest, largest, rating_budget)
- PS3 decryption and JB folder extraction
- Interactive CLI wizard with auto-discovery
- Project-local logging

### 🚧 In Progress
- Testing selection filter with Saturn build
- Expanding platform coverage

### 📋 Planned
- Web UI with job queue
- Metadata scraping integration
- Box art/screenshot download
- Multi-user support
- Build caching (resume interrupted builds)
- Delta updates (incremental collection updates)

---

## 🎮 Supported Platforms (Expandable)

**Currently Configured:**
- Sega Saturn (Redump, CHD compression)
- Virtual Boy (No-Intro, simple archives)
- PlayStation 3 (Redump, JB folder format)
- Sega CD / Mega CD
- PlayStation (PSX)
- Dreamcast
- GameCube
- NES
- PS2
- PSP
- Wii
- Wii U

**Platform Support is Config-Driven:**
Add a YAML file to `config/platforms/` and it appears in the wizard automatically!

---

## 🔮 Future Vision

### Year 1: CLI Perfection
- All major platforms supported
- Comprehensive testing
- Performance optimization
- Documentation and tutorials

### Year 2: Web Platform
- Public beta of web UI
- Job queue and progress tracking
- Community build sharing
- Mobile-friendly interface

### Year 3: Ecosystem
- Plugin system for custom workflows
- Metadata aggregation (ratings, reviews)
- Social features (collections, recommendations)
- Marketplace for premium builds?

---

## 💡 Why This Will Succeed

### 1. **Solves Real Pain**
ROM collection management is currently:
- Manual and tedious
- Requires expert knowledge
- Error-prone
- Time-consuming

**ROM Farmer makes it:**
- Automated and fast
- Beginner-friendly
- Correct by default
- One-click simple

### 2. **Technical Excellence**
- Clean architecture (layers are independent)
- Type-safe (Pydantic models)
- Well-tested (production use)
- Extensible (plugin-ready)

### 3. **Community Ready**
- Self-documenting (interactive wizard)
- Shareable configs (YAML)
- Open source potential
- Active development

### 4. **Unique Value**
**No other tool does this:**
- ✅ DAT validation + Quality filtering
- ✅ Multi-platform + Multi-target
- ✅ Interactive UX + Web UI path
- ✅ Production-grade + User-friendly

---

## 🚀 Getting Started

### For Users (Now):
```bash
./build-wizard
# Follow the prompts!
```

### For Developers:
```bash
# Core CLI
python3 -m romfarmer build run <config>

# Interactive wizard
python3 -m romfarmer quick --interactive

# Or the shortcut
./build-wizard
```

### For Future Contributors:
1. Read `ARCHITECTURE.md` (this file)
2. Check `config/` directory structure
3. Look at `src/romfarmer/cli/quick.py` for discovery logic
4. Run `./build-wizard` to see it in action
5. Build something awesome! 🎉

---

## 📚 Key Files

- `build-wizard` - One-command launcher
- `src/romfarmer/cli/quick.py` - Interactive wizard
- `src/romfarmer/stages/filter_selection.py` - Selection strategies
- `src/romfarmer/platform_processor.py` - Core pipeline
- `config/platforms/*.yaml` - Platform definitions
- `config/selections/*.yaml` - Selection presets
- `config/builds/*.yaml` - Build configurations

---

## 🎯 Success Metrics

**Technical:**
- ✅ No manual DAT file editing
- ✅ Sub-minute startup for 10-game test builds
- ✅ Zero data corruption (hash verification)
- ✅ Reproducible builds (same config = same output)

**User Experience:**
- ✅ Non-technical users can build collections
- ✅ No documentation reading required
- ✅ Visual feedback throughout process
- ✅ Clear error messages

**Community:**
- 📊 Config sharing between users
- 📊 Public build templates
- 📊 Active GitHub discussions
- 📊 Positive word-of-mouth

---

## 💪 The Community Will Love This Because:

1. **It Just Works** - No PhD in ROM management required
2. **It's Fast** - Automated workflows save hours
3. **It's Correct** - DAT validation ensures quality
4. **It's Flexible** - Supports their specific needs
5. **It's Beautiful** - Rich CLI and (future) Web UI
6. **It's Shareable** - Configs are portable
7. **It's Free** - Open source potential
8. **It's Growing** - Active development, new features

---

**Built with ❤️ for the ROM preservation community**

*"From chaos to curated collections, automatically."*
