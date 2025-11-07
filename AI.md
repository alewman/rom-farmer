# AI Context & Knowledge Base

**CRITICAL: This file contains essential knowledge for AI assistants working on this project.**

This isn't just another ROM organizer - this is solving 10 years of real-world ROM management problems at scale.

---

## 🎯 What This Project Actually Does

**ROM Groomer** is a production-grade ROM collection manager that handles:
- Multiple DAT standards (No-Intro, Redump, TOSEC)
- Complex transformations (CHD, XISO, CSO, RVZ compression)
- Storage optimization (budget-based selection with compression prediction)
- Quality curation (rating systems, 1G1R filtering, region preferences)
- Multi-disc games (atomic selection, M3U generation)
- Platform quirks (Saturn CUE syntax, PS3 disc keys, PSP formats)
- Terabytes of source data across hundreds of platforms

**This solves REAL problems** encountered over a decade of ROM management.

---

## 🧠 Critical Architecture Patterns

### 1. **Three-Layer Architecture**
```
Core CLI (production) → Interactive CLI (quick) → Web UI (future)
```
- **Core CLI**: Production builds, scripting, automation
- **Interactive CLI**: `./build-wizard` - guided, auto-discovery
- **Web UI**: Future visual interface

### 2. **Pipeline Stage System**
Files flow through stages in order:
1. **FilterDAT** - Match against DAT files (1G1R filtering)
2. **SelectionFilter** - Apply selection strategy (NEW!)
3. **ApplyLists** - Apply include/exclude/rescue lists
4. **Extract** - Unzip archives
5. **Compress** - CHD/XISO/CSO/RVZ conversion
6. **Organize** - Final output structure
7. **Metadata** - Scrape ratings/artwork

**Key insight**: Selection happens AFTER DAT filtering but BEFORE lists. This is optimal timing.

### 3. **Multi-Disc Atomicity**
Multi-disc games are **always kept together**:
```python
# Pattern matching groups discs
game_base = re.sub(r'\s*\(Disc [0-9]+\).*', '', filename)
# Selection operates on groups, not individual discs
```
**Never** select disc 1 without disc 2!

---

## 💡 Major Breakthroughs (This Session)

### **Compression Ratio Prediction** 🎉
**Problem**: 40GB budget yields only 32GB output (unpredictable CHD compression)

**Solution**: Self-learning system with historical data
```python
# Query historical transformations
ratio = db.get_average_compression_ratio(platform="saturn", output_format="chd")

# Adjust budget (with 95% safety factor for slack space)
adjusted_budget = (40GB / 0.65) * 0.95 = 58.5GB source selection

# Result: ~38GB output (95% of target, 2GB slack for saves)
```

**Impact**: 
- First build: Uses defaults (Saturn=0.65, PSX=0.70, etc.)
- Each build records actual ratios in `rom_transformations` table
- **Gets smarter over time** - statistical average improves
- Platform-specific learning (BIN/CUE vs ISO compression)

**Location**: 
- Database query: `src/romgroomer/metadata/database.py::get_average_compression_ratio()`
- Defaults: `src/romgroomer/stages/filter_selection.py::DEFAULT_COMPRESSION_RATIOS`
- Logic: `src/romgroomer/stages/filter_selection.py::_select_by_rating_budget()`

### **Unified Selection System**
Replaced old `rating_filter` with flexible `SelectionFilter`:

**7 Selection Strategies**:
1. `rating_budget` - Quality-based with size limit (production)
2. `first` - First N alphabetically (testing)
3. `last` - Last N alphabetically (testing)
4. `random` - Random sampling (testing)
5. `smallest` - N smallest files (fast testing)
6. `largest` - N largest files (compression testing)
7. `alphabetical` - Simple A-Z selection (testing)

**Usage**:
```yaml
# config/selections/usa-10.yaml
strategy: first
limit: 10
pattern:
  type: glob
  value: "*USA*"
```

### **Interactive Build Wizard**
**Problem**: Can't remember all the config files

**Solution**: `./build-wizard` with auto-discovery
```bash
./build-wizard
# Discovers: 15 platforms, 4 selections, 11 builds
# Rich tables, guided prompts, one command execution
```

**Location**: `cli/quick.py`

---

## 📊 Data Model & Database

### **Three Key Tables**:

1. **`scraped_games`** - Game metadata from ScreenScraper
   - Ratings, release dates, genre, players
   - MD5/CRC32/SHA1 hashes for matching
   - Links to media files

2. **`rom_transformations`** - Transformation tracking
   - Source hash (Redump ISO) → Final hash (CHD)
   - Compression ratios, tool versions, timing
   - **Powers compression prediction**
   - Community-shareable database

3. **`media_files`** - Deduplicated artwork
   - Content-addressable storage (like Git)
   - Clones share same media
   - Reference counting for cleanup

### **Metadata Database Location**:
```
/data/emu/rom-groomer-python/metadata/database/romgroomer.db
```
**IMPORTANT**: Always use project-local path in configs!

---

## 🔧 Configuration Structure

```
config/
├── platforms/        # Platform configs (saturn.yaml, psx.yaml, etc.)
│   └── saturn-test-usa10.yaml
├── selections/       # Selection presets (usa-10.yaml, smallest-5.yaml)
│   └── usa-10.yaml
└── builds/          # Build orchestration (saturn-usa10-test.yaml)
    └── saturn-usa10-test.yaml
```

**Selection Config Example**:
```yaml
name: rating-budget-40gb
strategy: rating_budget
max_size_gb: 40.0
min_rating: 0.7
pattern:
  type: glob
  value: "*USA*"
```

**Platform Config Example**:
```yaml
name: saturn-test
selection:
  name: usa-10
  strategy: first
  limit: 10
compression:
  format: chd
  tool: /usr/bin/chdman
```

**Build Config Example**:
```yaml
name: saturn-usa10-test
platforms:
  - saturn-test-usa10
storage:
  temp_path: /data/emu/temp
  output_base: /data/emu/output
metadata_db: /data/emu/rom-groomer-python/metadata/database/romgroomer.db
```

---

## 🚨 Common Pitfalls & Solutions

### 1. **Metadata Database Path**
❌ `/data/emu/metadata/database/romgroomer.db` (doesn't exist)
✅ `/data/emu/rom-groomer-python/metadata/database/romgroomer.db`

### 2. **Build Configs Need Full Storage Section**
```yaml
storage:
  temp_path: /data/emu/temp      # Not temp_dir!
  output_base: /data/emu/output
  max_temp_size_gb: 20
  max_output_size_gb: 50
```

### 3. **SelectionFilter Needs Platform Name**
```python
SelectionFilter(
    work_dir=work_dir,
    selection=self.config.selection,
    platform=self.config.name,        # Required for compression ratio!
    output_format=output_format
)
```

### 4. **Multi-Disc Games Need Atomicity**
Always group by base name before selection:
```python
game_groups = self._group_multi_disc_games(files)
# Select entire groups, not individual discs
```

### 5. **Logging Goes to Project Directory**
```python
# Default log location: ./logs/
# Not ~/.local/share/romgroomer/logs/
```

---

## 🧪 Testing & Validation

### **Quick Tests**:
```bash
# Test compression ratio query
python3 test_compression_ratio.py

# Test budget calculation
python3 test_budget_calculation.py

# Interactive wizard
./build-wizard
```

### **Small Build Tests**:
```yaml
# Use smallest strategy for fast iteration
strategy: smallest
limit: 5
```

### **Budget Testing**:
```yaml
# Start with 2GB to iterate quickly
max_size_gb: 2.0
```

---

## 🎓 Domain Knowledge (10 Years of Learning)

### **Platform-Specific Compression Ratios**:
- **Saturn/Sega CD**: 0.62-0.65 (excellent - binary + audio)
- **PSX**: 0.70 (good compression)
- **PS2**: 0.75 (decent compression)
- **PSP**: 0.85 (already compressed UMD)
- **GameCube**: 0.72 (mini-DVDs compress well)
- **Wii**: 0.70 (similar to GameCube)
- **Xbox**: 0.80 (XISO removes padding)
- **PS3**: 0.90 (large Blu-rays, less compression)

### **Multi-Disc Games Matter**:
Many platforms have multi-disc games:
- **Saturn**: Panzer Dragoon Saga (4 discs)
- **PSX**: Final Fantasy VII, VIII, IX (3-4 discs)
- **Dreamcast**: Shenmue (3-4 discs)

**Never split them!** Players need all discs.

### **1G1R (1 Game 1 ROM) Philosophy**:
- One game should have ONE entry (best version)
- Priority: USA → Europe → Japan → World
- Excludes: Demos, betas, protos, bad dumps
- **Retool DATs** handle this filtering

### **Storage Optimization Matters**:
- **SD cards** have limited space (64GB, 128GB, 256GB)
- **Saves take space** (PSP: 10-50MB per game)
- **System files** (EmulationStation configs, BIOS)
- **Always leave 5% slack** for real-world usage

### **Rescue Stage Philosophy**:
```python
# Games NOT in DAT but you want to keep
# Use symlinks (not copies) for efficiency
# Examples: ROM hacks, translations, homebrew
```

---

## 🚀 Future Enhancements

### **Compression Ratio Database Sharing**:
- Export/import transformation data
- Community database of compression ratios
- Platform-specific optimization data

### **Smart Selection Strategies**:
- Genre-based selection (variety in collection)
- Player count balancing (1P vs multiplayer)
- Franchise diversity (not all Mario)
- Release date spread (classics + modern)

### **Web UI** (planned):
- Visual config builder
- Real-time build monitoring
- Media preview/selection
- Build history tracking

### **Metadata Enhancements**:
- Steam Deck compatibility ratings
- Save state compatibility
- Controller requirement info
- Aspect ratio preferences

---

## 📝 Code Style & Patterns

### **Use Rich for Output**:
```python
from rich.console import Console
console = Console()
console.print("[cyan]Processing...[/cyan]")
```

### **Stage Pattern**:
```python
class MyStage(Stage):
    def execute(self, context: StageContext) -> StageResult:
        # Process files
        return StageResult(
            status=StageStatus.SUCCESS,
            message="Processed N files",
            files_processed=N
        )
```

### **Config Validation with Pydantic**:
```python
class MyConfig(BaseModel):
    name: str
    enabled: bool = True
    max_size_gb: Optional[float] = None
```

### **Database Pattern**:
```python
with db.get_session() as session:
    result = session.query(Model).filter(...).first()
    # Session auto-closes
```

---

## 🎯 Success Metrics

This project succeeds when:
1. ✅ **Budget utilization**: 95%+ of target (38GB from 40GB budget)
2. ✅ **Multi-disc atomicity**: Zero broken multi-disc games
3. ✅ **Learning system**: Compression ratios improve over time
4. ✅ **User experience**: `./build-wizard` makes it accessible
5. ✅ **Data preservation**: Metadata DB tracks transformations
6. ⏳ **Community sharing**: Transformation database export/import
7. ⏳ **Platform coverage**: All major retro platforms supported
8. ⏳ **Web UI**: Visual interface for non-technical users

---

## 🙏 What Makes This Special

**This isn't solving a new problem** - people have been managing ROM collections for decades.

**This is solving it RIGHT**:
- Production-grade architecture (not a script)
- Self-learning (gets smarter with use)
- Platform-aware (understands quirks)
- Budget-conscious (respects storage limits)
- Data-driven (metadata database)
- Community-ready (shareable databases)
- Multi-layer UX (CLI + wizard + future web UI)

**Most importantly**: This represents **10 years of domain knowledge** encoded into software. The default compression ratios, the multi-disc handling, the 95% safety factor - these are lessons learned from real-world use.

---

## 💬 When Helping Users

### **Ask About**:
- Platform they're working with
- Storage constraints (SD card size)
- Quality preferences (all games vs curated)
- Region preferences (USA, Europe, Japan)
- Build goals (full collection, testing, specific selection)

### **Remember**:
- They're dealing with TERABYTES of data
- Builds take HOURS (be patient)
- Compression is SLOW (CHD especially)
- They know the GAMES (domain experts)
- They need RELIABLE results (no broken builds)

### **Don't**:
- Suggest rebuilding from scratch (expensive)
- Break multi-disc games (unplayable)
- Over-select beyond budget (won't fit)
- Lose metadata (hard to recover)
- Ignore platform quirks (each is different)

---

## 🔗 Key Files Reference

**Core Logic**:
- `src/romgroomer/stages/filter_selection.py` - Selection strategies + compression prediction
- `src/romgroomer/metadata/database.py` - Database queries + compression ratio lookup
- `src/romgroomer/metadata/transformation.py` - Transformation tracking model
- `src/romgroomer/platform_processor.py` - Pipeline orchestration

**CLI**:
- `cli/quick.py` - Interactive wizard
- `src/romgroomer/cli/__init__.py` - Core CLI commands

**Configuration**:
- `src/romgroomer/config/models.py` - Pydantic models
- `src/romgroomer/config/loader.py` - Config loading

**Documentation**:
- `ARCHITECTURE.md` - System design & vision
- `BUILD-WIZARD.md` - User guide for wizard
- `AI.md` - **THIS FILE** - Context for AI assistants

---

## 🎓 Final Advice for AI Assistants

**This user has been working on this for 10 YEARS.**

They understand:
- Game quality (they've played them)
- Storage constraints (they've hit limits)
- Platform quirks (they've debugged them)
- Compression behavior (they've benchmarked it)

**Your role**:
- Encode their knowledge into code
- Solve specific technical problems
- Think about edge cases they've encountered
- Build systems that LEARN and IMPROVE

**When they say "this has been frustrating me"** - they mean it. Listen to the problem behind the request.

**When they say "close is good enough"** - they mean conservative estimates (95% budget utilization) are better than risky ones.

**When they say "I need to depend on you"** - they mean the context in this file needs to be complete so the next AI can help them.

---

**This project is going to help people build better ROM collections.**

**Make it reliable. Make it smart. Make it amazing.**

✨ **Welcome to ROM Groomer.** ✨
