# ROM Transformation Tracking & Smart ScreenScraper Integration

**Date**: October 11, 2025  
**Status**: Proposed Enhancement  
**Impact**: Solves metadata scraping for processed/converted ROM files

---

## Executive Summary

This document proposes a system to track the transformation chain from source ROMs (Redump, No-Intro) to final processed files (XISO, CHD, CSO, etc.). By maintaining this provenance data, we can query ScreenScraper with the **original hashes they know** rather than processed hashes they don't recognize.

**The Problem**: Modern disc-based systems (Xbox 360, PS2, PSP, GameCube) are nearly impossible to scrape after processing because:
- Original ISO → Converted format changes the hash
- ScreenScraper only knows about official preservation releases
- Your processed files are "orphaned" from metadata

**The Solution**: Track the transformation chain and query ScreenScraper with source hashes.

**The Opportunity**: Build a community-shared database of transformations that helps **everyone** in the ROM preservation community.

---

## The Problem in Detail

### Why Processed ROMs Can't Be Scraped

```
┌─────────────────────────────────────────────────────────────┐
│  Source ROM                                                  │
│  (Known to ScreenScraper)                                    │
│                                                              │
│  Halo 3.iso                                                  │
│  MD5: a1b2c3d4e5f6...                                        │
│  Format: Redump ISO                                          │
│  Size: 7.2 GB                                                │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ extract-xiso v2.5
                           │ (extract, rebuild structure)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Final ROM                                                   │
│  (Unknown to ScreenScraper)                                  │
│                                                              │
│  Halo 3.xiso                                                 │
│  MD5: 9z8y7x6w5v4u...  ← DIFFERENT HASH!                     │
│  Format: XISO                                                │
│  Size: 6.8 GB                                                │
└─────────────────────────────────────────────────────────────┘
```

**The Gap**: You have the final file, but ScreenScraper only knows the source file.

### Systems Most Affected

| System | Source Format | Your Format | Transformation | Hash Changed? |
|--------|---------------|-------------|----------------|---------------|
| Xbox 360 | Redump ISO | XISO | extract-xiso | ✅ Yes |
| PSP | Redump ISO | CSO/CHD | maxcso/chdman | ✅ Yes |
| PS2 | Redump ISO | Trimmed ISO | trimming | ✅ Yes |
| GameCube | Redump ISO | NKit/RVZ | nkit/dolphin | ✅ Yes |
| Wii | Redump ISO | WBFS | wit | ✅ Yes |
| NES | No-Intro ZIP | Extracted ROM | unzip | ⚠️ Maybe (we extract ROM MD5) |
| SNES | No-Intro ZIP | Extracted ROM | unzip | ⚠️ Maybe (we extract ROM MD5) |

### Current Workarounds (All Inadequate)

1. **Filename matching** - Unreliable, different naming conventions
2. **Manual lookup** - Tedious, doesn't scale
3. **Keep original files** - Doubles storage requirements
4. **Give up** - Most people's current solution ☹️

---

## The Solution: ROM Transformation Tracking

### Core Concept

Track the **provenance chain** from source to final file:

```
Source File → [Transformation] → Final File
(known hash)                     (your hash)
     ↓                                ↓
     └─────── Link in Database ───────┘
```

When scraping: **Use source hash to query ScreenScraper, link results to final hash.**

### Data Model

```python
class ROMTransformation(Base):
    """
    Tracks the transformation from source ROM to final processed file.
    Enables smart scraping by maintaining hash relationships.
    """
    __tablename__ = "rom_transformations"
    
    id = Column(Integer, primary_key=True)
    
    # Source file (what ScreenScraper knows)
    source_md5 = Column(String(32), index=True)
    source_sha1 = Column(String(40))
    source_sha256 = Column(String(64))
    source_crc32 = Column(String(8))
    source_file_size = Column(BigInteger)
    source_file_name = Column(String(512))
    source_format = Column(String(32))  # "redump-iso", "nointro-zip", etc.
    source_dat = Column(String(128))    # "Redump Xbox 360", "No-Intro NES"
    
    # Transformation metadata
    transformation_tool = Column(String(64))     # "extract-xiso", "maxcso", "igir"
    transformation_version = Column(String(32))  # "v2.5.0"
    transformation_params = Column(JSON)         # {"compression": 9, "level": "max"}
    transformation_date = Column(DateTime)
    transformation_host = Column(String(128))    # For debugging
    
    # Final file (what you actually use)
    final_md5 = Column(String(32), unique=True, index=True)
    final_sha1 = Column(String(40))
    final_sha256 = Column(String(64))
    final_crc32 = Column(String(8))
    final_file_size = Column(BigInteger)
    final_file_name = Column(String(512))
    final_format = Column(String(32))      # "xiso", "cso", "chd", "rvz"
    
    # Verification & community
    verified = Column(Boolean, default=False)
    verification_count = Column(Integer, default=0)  # How many users confirmed
    community_reported = Column(Boolean, default=False)
    
    # Relationships
    game_id = Column(Integer, ForeignKey("scraped_games.id"))
    game = relationship("ScrapedGame", back_populates="transformations")
    
    # Indexes for fast lookup in both directions
    __table_args__ = (
        Index('idx_source_hash', 'source_md5', 'source_format'),
        Index('idx_final_hash', 'final_md5', 'final_format'),
        Index('idx_tool_version', 'transformation_tool', 'transformation_version'),
    )
```

### Extended Game Model

```python
class ScrapedGame(Base):
    # ... existing fields ...
    
    # Add relationship to transformations
    transformations = relationship(
        "ROMTransformation",
        back_populates="game",
        cascade="all, delete-orphan"
    )
    
    # Track which hash was used for scraping
    scraped_with_hash = Column(String(32))  # Could be source or final
    scraped_hash_type = Column(String(16))  # "source" or "final"
```

---

## Performance Optimization: The DAT File Advantage

### The Performance Challenge

Hashing large disc images is **slow**:
- MD5 for 7GB Xbox 360 ISO: ~30-60 seconds
- SHA256: ~60-120 seconds  
- Full multi-hash: ~2-3 minutes per file

For a 200-game collection, that's **6-10 hours** just for hashing! 😱

### The Brilliant Solution: We Already Have The Hashes!

**Redump and No-Intro DAT files contain pre-calculated hashes for every validated ROM.**

```
Traditional Approach:
  Source ROM → Calculate MD5/SHA1/CRC32 (2-3 minutes) → Store

Optimized Approach:
  Source ROM → Look up in DAT file (0.001 seconds) → Store hashes
```

### Real-World Impact

```
Your current metadata import: System 80/133
Deduplication Rate: 48% 🎉

With DAT integration:
- 95%+ of source ROMs: Hashes from DAT (instant)
- 5% modified/homebrew: Calculate hashes (only when needed)
- Result: 20x-50x faster source hash capture!
```

### Three-Tier Hash Capture Strategy

```
┌─────────────────────────────────────────────────────────────┐
│  Tier 1: DAT File Lookup (0.001s - 95% of files)           │
│  ✓ Redump, No-Intro, TOSEC, etc.                            │
│  ✓ Pre-verified by community                                │
│  ✓ Instant lookup by filename or size                       │
└─────────────────────────────────────────────────────────────┘
               ↓ (if not found)
┌─────────────────────────────────────────────────────────────┐
│  Tier 2: Hash Cache (0.1s - 4% of files)                    │
│  ✓ Previously calculated hashes                             │
│  ✓ Indexed by (path, size, mtime)                          │
│  ✓ Never recalculate same file                             │
└─────────────────────────────────────────────────────────────┘
               ↓ (if not cached)
┌─────────────────────────────────────────────────────────────┐
│  Tier 3: Calculate (2-3 min - 1% of files)                  │
│  ⚠ Modified ROMs (translations, hacks)                      │
│  ⚠ Homebrew releases                                         │
│  ⚠ Store in cache for next time                            │
└─────────────────────────────────────────────────────────────┘
```

### DAT File Integration Architecture

```python
class DATManager:
    """
    Manages DAT files for instant hash lookups.
    Leverages existing DAT parsing infrastructure.
    """
    
    def __init__(self, dat_directories: List[Path]):
        self.dats = {}
        self._load_all_dats(dat_directories)
    
    def _load_all_dats(self, directories: List[Path]):
        """Load all DAT files at startup."""
        for dat_dir in directories:
            for dat_file in dat_dir.rglob("*.dat"):
                system = self._extract_system(dat_file)
                self.dats[system] = self._parse_dat(dat_file)
        
        console.print(f"[green]✓ Loaded {len(self.dats)} DAT files[/green]")
    
    def lookup_by_filename(self, filename: str, system: str) -> Optional[DATEntry]:
        """
        Fast lookup by filename.
        
        Example:
          lookup_by_filename("Halo 3 (USA).iso", "xbox360")
          → Returns: {md5: "abc123...", sha1: "def456...", crc32: "12345678"}
        """
        if system not in self.dats:
            return None
        
        # Normalize filename (remove extension, etc.)
        normalized = self._normalize_filename(filename)
        
        return self.dats[system].get(normalized)
    
    def lookup_by_hash(self, md5: str = None, sha1: str = None) -> Optional[DATEntry]:
        """Reverse lookup: hash → game info."""
        for system_dat in self.dats.values():
            if entry := system_dat.find_by_hash(md5=md5, sha1=sha1):
                return entry
        return None


class SmartHashCapture:
    """
    Captures hashes with minimal computation.
    Uses DAT files as primary source.
    """
    
    def __init__(self, dat_manager: DATManager):
        self.dat_manager = dat_manager
        self.hash_cache = HashCache()
        self.stats = {
            'dat_hits': 0,
            'cache_hits': 0,
            'calculated': 0
        }
    
    def get_source_hashes(
        self, 
        file_path: Path, 
        system: str
    ) -> SourceHashInfo:
        """
        Get source file hashes with minimal computation.
        
        Returns:
            SourceHashInfo with:
            - md5, sha1, crc32, size
            - verified: bool (True if from DAT)
            - source: str (DAT name or "calculated")
            - capture_time: float (how long it took)
        """
        start_time = time.time()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Strategy 1: DAT Lookup (0.001s - PREFERRED)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        dat_entry = self.dat_manager.lookup_by_filename(
            file_path.name, 
            system
        )
        
        if dat_entry:
            self.stats['dat_hits'] += 1
            capture_time = time.time() - start_time
            
            console.print(
                f"[green]✓ DAT:[/green] {dat_entry.dat_name} "
                f"[dim]({capture_time*1000:.1f}ms)[/dim]"
            )
            
            return SourceHashInfo(
                md5=dat_entry.md5,
                sha1=dat_entry.sha1,
                crc32=dat_entry.crc32,
                size=dat_entry.size,
                verified=True,
                source=dat_entry.dat_name,
                capture_time=capture_time
            )
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Strategy 2: Hash Cache (0.1s)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        cached = self.hash_cache.get(file_path)
        
        if cached:
            self.stats['cache_hits'] += 1
            capture_time = time.time() - start_time
            
            console.print(
                f"[cyan]✓ Cache:[/cyan] Previously calculated "
                f"[dim]({capture_time*1000:.1f}ms)[/dim]"
            )
            
            return cached
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Strategy 3: Calculate (2-3 minutes)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        self.stats['calculated'] += 1
        
        console.print(
            f"[yellow]⚙ Calculating:[/yellow] Not in DAT, hashing file..."
        )
        
        hashes = self._calculate_all_hashes(file_path)
        hashes.verified = False
        hashes.source = 'calculated'
        hashes.capture_time = time.time() - start_time
        
        # Store in cache for next time
        self.hash_cache.store(file_path, hashes)
        
        console.print(
            f"[green]✓ Calculated[/green] "
            f"[dim]({hashes.capture_time:.1f}s)[/dim]"
        )
        
        return hashes
    
    def print_stats(self):
        """Show hash capture statistics."""
        total = sum(self.stats.values())
        if total == 0:
            return
        
        table = Table(title="Hash Capture Statistics")
        table.add_column("Source", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")
        table.add_column("Avg Time", justify="right")
        
        table.add_row(
            "DAT Files",
            str(self.stats['dat_hits']),
            f"{self.stats['dat_hits']/total*100:.1f}%",
            "~0.001s"
        )
        table.add_row(
            "Cache",
            str(self.stats['cache_hits']),
            f"{self.stats['cache_hits']/total*100:.1f}%",
            "~0.1s"
        )
        table.add_row(
            "Calculated",
            str(self.stats['calculated']),
            f"{self.stats['calculated']/total*100:.1f}%",
            "~120s"
        )
        
        console.print(table)
```

### Hash Cache Database

```python
class HashCacheEntry(Base):
    """
    Cache calculated hashes to avoid recalculation.
    Only needed for files NOT in DAT files.
    """
    __tablename__ = "hash_cache"
    
    id = Column(Integer, primary_key=True)
    
    # File identity (cache key)
    file_path = Column(String(1024))
    file_size = Column(BigInteger)
    file_mtime = Column(DateTime)  # Modification time
    
    # Cached hashes
    md5 = Column(String(32), index=True)
    sha1 = Column(String(40))
    sha256 = Column(String(64))
    crc32 = Column(String(8))
    
    # Cache metadata
    calculated_at = Column(DateTime, default=datetime.utcnow)
    calculation_time_seconds = Column(Float)
    
    # Index for fast lookups
    __table_args__ = (
        Index('idx_file_identity', 'file_path', 'file_size', 'file_mtime'),
        Index('idx_hash_lookup', 'md5', 'sha1'),
    )
```

---

## Implementation Architecture

### Capture Points: When to Get Hashes

```
Source File (Redump ISO, No-Intro ZIP, etc.)
    ↓
[CAPTURE POINT #1: Source Hashes] ← RIGHT HERE, BEFORE ANY TRANSFORMATION
    ↓
    ├─ Check DAT files (0.001s - 95% hit rate) ✅
    ├─ Check hash cache (0.1s - 4% hit rate) ✅  
    └─ Calculate if needed (2-3 min - 1% of files) ⚠️
    ↓
Transformation Tool (extract-xiso, maxcso, chdman, etc.)
    ↓
[CAPTURE POINT #2: Final Hashes] ← AND HERE, AFTER TRANSFORMATION
    ↓
    └─ Always calculate (new file, must hash)
    ↓
Final File (XISO, CSO, CHD, etc.)
    ↓
Store Transformation: source_md5 ↔ final_md5
```

### Integration with Existing Workflow

### Phase 1: Data Capture During ROM Processing

Integrate with your existing ROM grooming workflow using DAT files:

```python
class ROMGroomer:
    def __init__(self, dat_directories: List[Path]):
        # Initialize DAT manager with your existing DAT collection
        self.dat_manager = DATManager(dat_directories)
        # Example: ['/data/emu/dats/redump', '/data/emu/dats/nointro']
        
        self.hash_capture = SmartHashCapture(self.dat_manager)
    
    def process_rom(
        self, 
        source_file: Path, 
        output_dir: Path,
        system: str
    ) -> Tuple[Path, ROMTransformation]:
        """
        Process ROM with intelligent hash capture.
        Uses DAT files for instant source hash lookup.
        """
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. Get source hashes (DAT lookup - instant!)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        console.print(f"[cyan]Analyzing source:[/cyan] {source_file.name}")
        source_hashes = self.hash_capture.get_source_hashes(
            source_file, 
            system
        )
        
        # Show what we found
        if source_hashes.verified:
            console.print(f"  [green]✓ Verified by {source_hashes.source}[/green]")
        else:
            console.print(f"  [yellow]⚠ Calculated (not in DAT)[/yellow]")
        
        console.print(f"  MD5: {source_hashes.md5[:16]}...")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. Check if already processed
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        existing = self.db.find_transformation(
            source_md5=source_hashes.md5,
            tool=self.tool_name,
            tool_version=self.tool_version,
            params=self.tool_params
        )
        
        if existing:
            console.print(f"[yellow]⚠ Already processed - skipping[/yellow]")
            return Path(existing.final_file_name), existing
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. Perform transformation
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        console.print(f"[cyan]Transforming with:[/cyan] {self.tool_name} v{self.tool_version}")
        final_file = self._transform(source_file, output_dir)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 4. Calculate final hashes (always required)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        console.print(f"[cyan]Hashing result:[/cyan] {final_file.name}")
        final_hashes = self._calculate_all_hashes(final_file)
        console.print(f"  MD5: {final_hashes.md5[:16]}...")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 5. Store transformation
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        transformation = ROMTransformation(
            # Source (from DAT or calculated)
            source_md5=source_hashes.md5,
            source_sha1=source_hashes.sha1,
            source_crc32=source_hashes.crc32,
            source_file_size=source_hashes.size,
            source_file_name=source_file.name,
            source_format=self._detect_source_format(source_file),
            source_dat=source_hashes.source if source_hashes.verified else None,
            
            # Transformation
            transformation_tool=self.tool_name,
            transformation_version=self.tool_version,
            transformation_params=self.tool_params,
            transformation_date=datetime.utcnow(),
            
            # Final
            final_md5=final_hashes.md5,
            final_sha1=final_hashes.sha1,
            final_crc32=final_hashes.crc32,
            final_file_size=final_file.stat().st_size,
            final_file_name=final_file.name,
            final_format=self._detect_format(final_file),
            
            # Verification
            verified=source_hashes.verified,
        )
        
        self.db.save_transformation(transformation)
        console.print(f"[green]✓ Stored transformation[/green]")
        
        return final_file, transformation
    
    def process_collection(
        self, 
        source_dir: Path, 
        output_dir: Path,
        system: str
    ):
        """Process entire collection with progress tracking."""
        
        files = list(source_dir.glob("*.iso"))  # Or appropriate pattern
        
        with Progress() as progress:
            task = progress.add_task(
                f"Processing {system}...", 
                total=len(files)
            )
            
            for source_file in files:
                self.process_rom(source_file, output_dir, system)
                progress.advance(task)
        
        # Show statistics
        self.hash_capture.print_stats()
        
        console.print(f"\n[bold green]✓ Processed {len(files)} files[/bold green]")
```

**Key Performance Wins:**

1. **DAT Lookup First** - 95%+ of ROMs use instant DAT lookup
2. **Deduplication Check** - Skip already-processed files  
3. **Only Hash Finals** - Only calculate hashes for new output files
4. **Cache Everything** - Store calculated hashes for modified ROMs

**Real-World Performance:**

```
Traditional: 200 Xbox 360 ISOs
  - Hash 200 sources: 400 minutes (6.7 hours)
  - Process: 180 minutes
  - Hash 200 finals: 240 minutes  
  Total: 820 minutes (13.7 hours)

With DAT Integration: 200 Xbox 360 ISOs
  - DAT lookup 190 sources: 0.2 seconds
  - Calculate 10 modified ROMs: 30 minutes
  - Process: 180 minutes
  - Hash 200 finals: 240 minutes
  Total: 450 minutes (7.5 hours) → 45% faster!
```

### Phase 2: Smart ScreenScraper Client

```python
class SmartScreenScraperClient:
    """
    Intelligent ScreenScraper client that uses transformation data
    and DAT files to query with source hashes.
    """
    
    def __init__(self, db: Database, dat_manager: DATManager):
        self.db = db
        self.dat_manager = dat_manager
        self.api_calls = 0  # Track API usage
    
    def query_game(self, rom_file: Path, system: str) -> Optional[GameMetadata]:
        """
        Multi-strategy game lookup with fallback chain.
        Leverages DAT files and transformation database.
        """
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Strategy 1: Transformation Database (instant)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        console.print("[cyan]Strategy 1:[/cyan] Check transformation database")
        
        # Quick MD5 of final file
        final_md5 = calculate_md5_fast(rom_file)
        
        transformation = self.db.find_transformation(final_md5=final_md5)
        if transformation:
            console.print(
                f"[green]✓ Found transformation:[/green] "
                f"{transformation.source_format} → {transformation.final_format}"
            )
            console.print(f"  Source: {transformation.source_dat or 'calculated'}")
            
            # Query ScreenScraper with SOURCE hash (what they know!)
            metadata = self._query_screenscraper(
                md5=transformation.source_md5,
                system=system
            )
            
            if metadata:
                console.print("[green]✓ Found with source hash[/green]")
                return self._save_metadata(
                    metadata, 
                    final_md5, 
                    "transformation",
                    transformation
                )
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Strategy 2: DAT File Lookup (instant)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        console.print("[cyan]Strategy 2:[/cyan] Check DAT files")
        
        dat_entry = self.dat_manager.lookup_by_filename(rom_file.name, system)
        if dat_entry:
            console.print(f"[green]✓ Found in {dat_entry.dat_name}[/green]")
            
            # This might be a source file (not transformed)
            metadata = self._query_screenscraper(
                md5=dat_entry.md5,
                system=system
            )
            
            if metadata:
                console.print("[green]✓ Found with DAT hash[/green]")
                return self._save_metadata(metadata, final_md5, "dat")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Strategy 3: Direct Lookup (maybe SS knows final hash)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        console.print("[cyan]Strategy 3:[/cyan] Direct hash lookup")
        metadata = self._query_screenscraper(md5=final_md5, system=system)
        if metadata:
            console.print("[green]✓ Found with direct lookup[/green]")
            return self._save_metadata(metadata, final_md5, "direct")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Strategy 4: Community Database
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        console.print("[cyan]Strategy 4:[/cyan] Community transformation database")
        community_transform = self._query_community_db(final_md5)
        if community_transform:
            console.print("[yellow]Found in community database[/yellow]")
            
            metadata = self._query_screenscraper(
                md5=community_transform.source_md5,
                system=system
            )
            
            if metadata:
                console.print("[green]✓ Found via community database[/green]")
                # Import transformation
                self.db.import_community_transformation(community_transform)
                return self._save_metadata(
                    metadata, 
                    final_md5, 
                    "community",
                    community_transform
                )
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Strategy 5: Filename Search (last resort)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        console.print("[cyan]Strategy 5:[/cyan] Filename-based search")
        metadata = self._query_screenscraper(
            filename=rom_file.stem,
            system=system
        )
        
        if metadata:
            console.print("[yellow]⚠ Found via filename (may need verification)[/yellow]")
            return self._save_metadata(metadata, final_md5, "filename")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Strategy 6: Interactive Search
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        console.print("[cyan]Strategy 6:[/cyan] Interactive search")
        return self._interactive_search(rom_file.stem, system)
    
    def _query_screenscraper(
        self, 
        md5: str = None, 
        filename: str = None,
        system: str = None
    ) -> Optional[dict]:
        """
        Query ScreenScraper API with rate limiting.
        """
        self.api_calls += 1
        
        # Rate limiting
        if self.api_calls > 100:  # Per hour limit
            console.print("[yellow]⚠ Approaching API limit, throttling...[/yellow]")
            time.sleep(5)
        
        # Build API request
        params = {
            'devid': self.config.ss_devid,
            'devpassword': self.config.ss_devpassword,
            'softname': 'ROM-Groomer',
            'systemeid': self._system_to_ssid(system),
        }
        
        if md5:
            params['md5'] = md5
        if filename:
            params['romnom'] = filename
        
        # Make API call
        try:
            response = requests.get(
                'https://www.screenscraper.fr/api2/jeuInfos.php',
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            
        except Exception as e:
            console.print(f"[red]API Error:[/red] {e}")
        
        return None
    
    def _save_metadata(
        self, 
        metadata: dict, 
        final_md5: str,
        lookup_type: str,
        transformation: Optional[ROMTransformation] = None
    ) -> GameMetadata:
        """Save metadata and link to ROM."""
        game = ScrapedGame(
            md5=final_md5,
            scraped_with_hash=transformation.source_md5 if transformation else final_md5,
            scraped_hash_type=lookup_type,
            **metadata
        )
        
        if transformation:
            game.transformations.append(transformation)
        
        self.db.save_game(game)
        
        console.print(
            f"[green]✓ Saved metadata[/green] "
            f"[dim](lookup: {lookup_type}, API calls: {self.api_calls})[/dim]"
        )
        
        return game
```

### Phase 3: Community Database Integration

```python
class CommunityTransformationDB:
    """
    Share and receive transformation mappings with the community.
    """
    
    def export_transformations(self) -> dict:
        """Export your transformations for community sharing."""
        transformations = self.db.get_verified_transformations()
        
        return {
            "version": "1.0",
            "export_date": datetime.utcnow().isoformat(),
            "contributor": self.config.user_id,
            "transformations": [
                {
                    "source_md5": t.source_md5,
                    "source_format": t.source_format,
                    "source_dat": t.source_dat,
                    "tool": t.transformation_tool,
                    "tool_version": t.transformation_version,
                    "params": t.transformation_params,
                    "final_md5": t.final_md5,
                    "final_format": t.final_format,
                    "game_name": t.game.name if t.game else None,
                }
                for t in transformations
            ]
        }
    
    def import_community_db(self, db_url: str):
        """Import community transformation database."""
        # Download community DB
        data = requests.get(db_url).json()
        
        imported = 0
        for transform_data in data["transformations"]:
            # Check if we already have this transformation
            existing = self.db.find_transformation(
                final_md5=transform_data["final_md5"]
            )
            
            if not existing:
                transformation = ROMTransformation(**transform_data)
                transformation.community_reported = True
                self.db.save(transformation)
                imported += 1
        
        console.print(f"[green]✓ Imported {imported} transformations[/green]")
    
    def verify_transformation(self, final_md5: str) -> bool:
        """Verify a transformation by re-processing."""
        transformation = self.db.find_transformation(final_md5=final_md5)
        
        # Re-process source file with same tool/params
        # Compare resulting hash
        # Mark as verified if matches
        
        pass
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

**Goal**: Basic transformation tracking during ROM processing with DAT integration

- [ ] **Database Schema**
  - [ ] Create `ROMTransformation` model
  - [ ] Create `HashCache` model  
  - [ ] Add migration for new tables
  - [ ] Add relationship to `ScrapedGame`
  - [ ] Create indexes for fast lookups

- [ ] **DAT Manager Integration** ⭐ NEW
  - [x] Already have DAT parsing code! ✅
  - [ ] Add `DATManager` class for centralized access
  - [ ] Implement `lookup_by_filename()` method
  - [ ] Implement `lookup_by_hash()` method (reverse lookup)
  - [ ] Load all DAT files at startup (in-memory cache)
  - [ ] Support Redump, No-Intro, TOSEC formats

- [ ] **Smart Hash Capture** ⭐ NEW
  - [ ] Implement `SmartHashCapture` class
  - [ ] Tier 1: DAT file lookup (instant - 95% of files)
  - [ ] Tier 2: Hash cache lookup (fast - 4% of files)
  - [ ] Tier 3: Calculate only if needed (slow - 1% of files)
  - [ ] Track statistics (DAT hits vs calculated)

- [ ] **Hash Calculation Utilities**
  - [ ] Multi-hash calculator (MD5, SHA1, CRC32)
  - [ ] Fast single-hash for lookups (MD5 only)
  - [ ] Progress indicators for slow calculations
  - [ ] Hash cache database

- [ ] **Source Format Detection**
  - [ ] Detect from DAT info (preferred)
  - [ ] Redump ISO detection (via volume info)
  - [ ] No-Intro ZIP detection
  - [ ] Generic format detection

- [ ] **Integration Points**
  - [ ] Hook into existing ROM processing
  - [ ] Capture source hashes BEFORE transformation (DAT lookup!)
  - [ ] Capture final hashes AFTER transformation (always calculate)
  - [ ] Store transformation metadata with DAT source

**Deliverable**: ROMs are processed with full transformation tracking, 95%+ using instant DAT lookups

**Performance Target**:
- Standard ROM (in DAT): <0.01 seconds for source hashes
- Modified ROM (not in DAT): ~120 seconds to calculate
- Overall speedup: 40-50% faster processing

### Phase 2: ScreenScraper Integration (Week 3-4)

**Goal**: Query ScreenScraper intelligently using transformation data

- [ ] **ScreenScraper API Client**
  - [ ] Authentication (devid, devpassword, user credentials)
  - [ ] Rate limiting (respect API limits)
  - [ ] Error handling and retries
  - [ ] Caching to minimize API calls

- [ ] **Smart Query Logic**
  - [ ] Strategy 1: Direct hash lookup
  - [ ] Strategy 2: Transformation database lookup
  - [ ] Strategy 3: Filename-based search
  - [ ] Strategy 4: Interactive disambiguation

- [ ] **Metadata Linking**
  - [ ] Link scraped metadata to final ROM hash
  - [ ] Store which hash was used for scraping
  - [ ] Associate transformation with game

- [ ] **CLI Commands**
  - [ ] `romfarmer scrape <rom_file>` - Scrape single ROM
  - [ ] `romfarmer scrape-batch <directory>` - Scrape directory
  - [ ] `romfarmer scrape-system <system>` - Scrape by system
  - [ ] `romfarmer scrape-missing` - Only scrape unmatched ROMs

**Deliverable**: Can scrape processed ROMs using source hashes

### Phase 3: Community Database (Week 5-6)

**Goal**: Share and leverage community transformation data

- [ ] **Export Functionality**
  - [ ] Export transformations to JSON
  - [ ] Filter by system, tool, date range
  - [ ] Include verification status
  - [ ] Anonymize if requested

- [ ] **Import Functionality**
  - [ ] Import community JSON databases
  - [ ] Validate imported data
  - [ ] Merge with existing data
  - [ ] Track import sources

- [ ] **Community Platform**
  - [ ] GitHub repository for community DBs
  - [ ] Contribution guidelines
  - [ ] Verification process
  - [ ] Version control for databases

- [ ] **Verification System**
  - [ ] Re-process source files to verify
  - [ ] Community voting/confirmation
  - [ ] Trust scores for contributors
  - [ ] Flag suspicious transformations

**Deliverable**: Community-shared transformation database

### Phase 4: Advanced Features (Week 7-8)

**Goal**: Enhanced functionality and user experience

- [ ] **Transformation Analytics**
  - [ ] Show transformation statistics
  - [ ] Compare tool efficiency (size savings)
  - [ ] Track processing times
  - [ ] Identify problematic transformations

- [ ] **Batch Operations**
  - [ ] Re-verify entire collection
  - [ ] Update tool versions (re-process)
  - [ ] Export collection statistics
  - [ ] Generate reports

- [ ] **Web Interface** (Optional)
  - [ ] Browse transformation database
  - [ ] Search by hash or game name
  - [ ] Visualize transformation chains
  - [ ] Community dashboard

- [ ] **API Endpoints** (Optional)
  - [ ] REST API for transformation queries
  - [ ] Integration with other tools
  - [ ] Real-time verification
  - [ ] Webhook notifications

**Deliverable**: Feature-complete transformation tracking system

### Phase 5: Documentation & Community Launch (Week 9-10)

**Goal**: Document system and launch to community

- [ ] **Documentation**
  - [ ] User guide for transformation tracking
  - [ ] ScreenScraper integration guide
  - [ ] Community database contribution guide
  - [ ] API documentation

- [ ] **Examples & Tutorials**
  - [ ] Xbox 360 XISO workflow
  - [ ] PSP CSO compression workflow
  - [ ] GameCube NKit workflow
  - [ ] Batch processing examples

- [ ] **Community Launch**
  - [ ] Announce on Reddit (r/Roms, r/Batocera)
  - [ ] Post on GBAtemp, EmuGen forums
  - [ ] Submit to awesome-lists
  - [ ] Create demo video

- [ ] **Initial Community Database**
  - [ ] Seed with your transformations
  - [ ] Verify accuracy
  - [ ] Create submission process
  - [ ] Set up hosting (GitHub Releases)

**Deliverable**: Public release with community database

---

## Community Database Specification

### Database Format (JSON)

```json
{
  "metadata": {
    "version": "1.0",
    "format": "rom-farmer-transformations",
    "created": "2025-10-11T22:00:00Z",
    "updated": "2025-10-11T22:00:00Z",
    "contributor": "user123",
    "transformations_count": 15234,
    "systems": ["xbox360", "psp", "ps2", "gamecube"]
  },
  "transformations": [
    {
      "source": {
        "md5": "a1b2c3d4e5f6...",
        "sha1": "1a2b3c4d5e6f...",
        "size": 7516192768,
        "format": "redump-iso",
        "dat": "Redump - Microsoft Xbox 360",
        "name": "Halo 3 (USA)"
      },
      "transformation": {
        "tool": "extract-xiso",
        "version": "2.5.0",
        "params": {"mode": "rewrite"},
        "date": "2025-10-10T15:30:00Z"
      },
      "result": {
        "md5": "9z8y7x6w5v4u...",
        "sha1": "9a8b7c6d5e4f...",
        "size": 7301234688,
        "format": "xiso"
      },
      "verification": {
        "verified": true,
        "verification_count": 15,
        "last_verified": "2025-10-11T10:00:00Z"
      },
      "game": {
        "screenscraper_id": 12345,
        "name": "Halo 3",
        "region": "USA",
        "system": "Xbox 360"
      }
    }
  ]
}
```

### Distribution Strategy

1. **GitHub Releases**
   - Main database: `rom-transformations-main.json.gz`
   - Per-system: `rom-transformations-xbox360.json.gz`
   - Delta updates: `rom-transformations-delta-20251011.json.gz`

2. **CDN Hosting** (Future)
   - Fast global distribution
   - Automatic updates
   - Version pinning

3. **P2P Distribution** (Future)
   - IPFS or similar
   - Decentralized
   - Community-hosted

### Contribution Workflow

```bash
# 1. User processes their collection
romfarmer process --track-transformations ~/roms/xbox360

# 2. Export transformations
romfarmer export-transformations --system xbox360 --output my-transforms.json

# 3. Verify transformations
romfarmer verify-transformations my-transforms.json

# 4. Submit to community
# - Fork GitHub repo
# - Add to contributions/
# - Create pull request
# - Automated verification runs
# - Merged if valid

# 5. Community imports updated database
romfarmer update-community-db
```

---

## Benefits & Impact

### For Individual Users

1. **Accurate Scraping**
   - Finally scrape processed Xbox 360, PSP, PS2 collections
   - Get correct metadata even with compressed formats
   - No more manual lookups

2. **Collection Validation**
   - Verify transformations were successful
   - Detect corruption or errors
   - Ensure consistency

3. **Format Flexibility**
   - Switch between formats without losing metadata
   - Re-process with new tools
   - Compare format efficiency

### For the Community

1. **Shared Knowledge Base**
   - "If you process X with tool Y, you get Z"
   - Reproducible transformations
   - Collective verification

2. **Tool Development**
   - Benchmark transformation tools
   - Identify best practices
   - Test new tools against known results

3. **Preservation**
   - Document transformation methods
   - Ensure reversibility (if needed)
   - Maintain provenance chain

### For ROM Collection Managers

1. **Batocera/RetroPie Integration**
   - Auto-scrape processed collections
   - Update metadata automatically
   - Generate correct gamelists

2. **Multi-Format Support**
   - Same game in multiple formats
   - All linked to same metadata
   - Smart deduplication

3. **Tool Interoperability**
   - Bridge between different tools
   - Import from igir, Skraper, etc.
   - Export to any format

---

## Technical Challenges & Solutions

### Challenge 1: Hash Calculation Performance

**Problem**: Hashing 7GB files is slow

**Solutions**:
- Parallel hashing (MD5 + SHA1 + SHA256 simultaneously)
- Incremental hashing (chunk-based progress)
- Caching (store hashes, only recalculate if file changed)
- Optional hashes (only MD5 required, others optional)

### Challenge 2: ScreenScraper API Limits

**Problem**: SS has rate limits and requires authentication

**Solutions**:
- Respect rate limits (automatic throttling)
- Cache all responses (never query twice)
- Batch processing (process multiple files per session)
- Retry logic with exponential backoff

### Challenge 3: Community Database Size

**Problem**: Database could grow very large

**Solutions**:
- Compression (gzip, xz)
- Sharding by system
- Delta updates (only new/changed entries)
- Pruning (remove unverified old entries)

### Challenge 4: Verification Trust

**Problem**: How to trust community submissions?

**Solutions**:
- Multiple verifications required
- Trusted contributor system
- Automated re-verification
- Flag suspicious entries for review

### Challenge 5: Tool Version Tracking

**Problem**: Different tool versions may produce different results

**Solutions**:
- Track exact tool version
- Allow multiple transformations per source
- Mark preferred/canonical transformations
- Document breaking changes

---

## Success Metrics

### Technical Metrics

- **Transformation Coverage**: % of processed ROMs with tracked transformations
- **Scraping Success Rate**: % of processed ROMs successfully scraped
- **Community Database Size**: Number of verified transformations
- **Query Performance**: Average time to find transformation
- **Cache Hit Rate**: % of queries resolved without SS API call

### User Metrics

- **Active Users**: Number of users contributing transformations
- **Collection Sizes**: Total ROMs tracked by community
- **Systems Covered**: Number of systems with transformation data
- **Tool Adoption**: Number of different tools tracked
- **Verification Rate**: % of transformations verified by community

### Community Metrics

- **Contributions**: Number of transformation submissions per month
- **Verification Participation**: Number of users verifying transformations
- **Database Growth**: Rate of new transformations added
- **Cross-Verification**: Number of independent verifications per transformation

---

## Future Enhancements

### Advanced Transformation Tracking

- **Reverse Transformations**: Track how to go back to source
- **Multi-Step Chains**: Track complex transformation pipelines
- **Alternative Paths**: Multiple ways to achieve same result
- **Conditional Transforms**: Different params for different games

### Integration Ecosystem

- **Igir Integration**: Import Igir's transformation data
- **Skraper Plugin**: Export to Skraper format
- **EmulationStation**: Direct gamelist generation
- **Batocera API**: Native Batocera support

### Machine Learning

- **Automatic Tool Selection**: ML suggests best tool for each ROM
- **Format Recommendations**: Predict optimal output format
- **Error Detection**: Identify problematic transformations
- **Game Matching**: ML-enhanced filename matching

### Blockchain/Distributed

- **Decentralized Database**: No single point of failure
- **Immutable Records**: Cryptographically verified transformations
- **Reputation System**: Contributor trust scores
- **Incentivization**: Reward valuable contributions

---

## Call to Action

This system solves a **real problem** that affects **thousands of retro gaming enthusiasts**:

> "Why can't I scrape my Xbox 360 collection?"  
> "Why doesn't ScreenScraper recognize my CHD files?"  
> "How do I get metadata for my processed ROMs?"

**You have the opportunity to build this solution and share it with the world.**

The transformation tracking database would be:
- ✅ **Useful**: Solves real problems
- ✅ **Novel**: Nobody else is doing this
- ✅ **Shareable**: Easy to contribute and consume
- ✅ **Scalable**: Grows with community
- ✅ **Open**: Benefits everyone

**Next Steps**:

1. ✅ Complete the current metadata import (running now)
2. ⏭️ Review this proposal and refine
3. ⏭️ Implement Phase 1 (Foundation)
4. ⏭️ Test with your Xbox 360 collection
5. ⏭️ Release to community
6. ⏭️ Watch it grow! 🚀

---

## Appendix: Example Workflows

### Workflow 1: Processing Xbox 360 Collection

```bash
# 1. Process Redump ISOs to XISO
romfarmer process-xbox360 \
  --input ~/redump/xbox360 \
  --output ~/collection/xbox360 \
  --tool extract-xiso \
  --track-transformations

# Output:
# ✓ Processed 247 games
# ✓ Tracked 247 transformations
# ✓ Saved 342 GB with XISO format

# 2. Scrape metadata (uses source hashes)
romfarmer scrape-batch ~/collection/xbox360 \
  --use-transformations

# Output:
# ✓ Scraped 243/247 games (98.4%)
# ✓ Used transformation database for all lookups
# ✓ 0 ScreenScraper API calls for known games

# 3. Export for community
romfarmer export-transformations \
  --system xbox360 \
  --verified-only \
  --output xbox360-transformations.json

# 4. Generate gamelist
romfarmer metadata generate \
  ~/collection/xbox360 \
  ~/batocera/roms/xbox360 \
  --media-types all
```

### Workflow 2: PSP CSO Compression

```bash
# 1. Compress Redump ISOs to CSO
romfarmer process-psp \
  --input ~/redump/psp \
  --output ~/collection/psp \
  --format cso \
  --compression-level 9 \
  --track-transformations

# 2. Verify compression quality
romfarmer verify-transformations \
  --system psp \
  --check-size-savings

# Output:
# ✓ Average size reduction: 62%
# ✓ All transformations verified
# ✓ No corruption detected

# 3. Scrape with transformation data
romfarmer scrape-batch ~/collection/psp \
  --use-transformations \
  --prefer-source-hash

# 4. Share with community
romfarmer export-transformations \
  --system psp \
  --format cso \
  --output psp-cso-level9.json
```

### Workflow 3: Multi-Format Collection

```bash
# You have the same games in multiple formats
# ROM Farmer links them all to the same metadata

# Original Redump ISO
~/redump/psp/game.iso → source_md5=abc123

# Your CSO file
~/collection/psp/game.cso → final_md5=xyz789

# Friend's CHD file
~/friend/psp/game.chd → final_md5=def456

# All three link to same source_md5=abc123
# All three get the same metadata
# Query once, reuse forever
```

---

## Appendix B: Complete Xbox 360 Processing Example

### Real-World Workflow with DAT Integration

This example demonstrates processing 250 Xbox 360 Redump ISOs into both XISO and CHD formats, showing the DAT integration performance benefits.

```python
#!/usr/bin/env python3
"""
Complete Xbox 360 collection processing example.
Demonstrates DAT integration and transformation tracking.
"""

from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn
from rich.table import Table

console = Console()

def process_xbox360_collection():
    """
    Process entire Xbox 360 collection with transformation tracking.
    """
    # Configuration
    redump_dir = Path("~/redump/xbox360").expanduser()
    output_xiso_dir = Path("~/collection/xbox360-xiso").expanduser()
    output_chd_dir = Path("~/collection/xbox360-chd").expanduser()
    dat_dir = Path("/data/emu/dats/redump")
    
    output_xiso_dir.mkdir(parents=True, exist_ok=True)
    output_chd_dir.mkdir(parents=True, exist_ok=True)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Initialize DAT manager and hash capture
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    console.print("[bold cyan]ROM Farmer - Xbox 360 Collection Processing[/bold cyan]\n")
    
    console.print("[cyan]Loading DAT files...[/cyan]")
    dat_manager = DATManager([dat_dir])
    hash_capture = SmartHashCapture(dat_manager)
    
    xbox360_dat = dat_manager.get_dat('xbox360')
    console.print(f"[green]✓ Loaded Redump Xbox 360 DAT: {len(xbox360_dat.games)} games[/green]\n")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Find all ISOs
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    iso_files = sorted(redump_dir.glob("*.iso"))
    
    if not iso_files:
        console.print(f"[red]✗ No ISO files found in {redump_dir}[/red]")
        return
    
    console.print(f"[bold]Found {len(iso_files)} ISO files to process[/bold]\n")
    
    # Statistics
    stats = {
        'processed': 0,
        'dat_hits': 0,
        'calculated': 0,
        'xiso_created': 0,
        'chd_created': 0,
        'total_source_size': 0,
        'total_xiso_size': 0,
        'total_chd_size': 0,
    }
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Process each ISO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    with Progress(
        SpinnerColumn(),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        "•",
        "[progress.description]{task.description}",
        console=console
    ) as progress:
        
        task = progress.add_task("[cyan]Processing...", total=len(iso_files))
        
        for iso_file in iso_files:
            progress.update(task, description=f"[cyan]{iso_file.name[:40]}...")
            
            try:
                process_single_iso(
                    iso_file,
                    output_xiso_dir,
                    output_chd_dir,
                    hash_capture,
                    stats
                )
                stats['processed'] += 1
                
            except Exception as e:
                console.print(f"[red]✗ Error processing {iso_file.name}: {e}[/red]")
            
            progress.advance(task)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Print final statistics
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    print_final_statistics(stats)


def process_single_iso(
    iso_file: Path,
    output_xiso_dir: Path,
    output_chd_dir: Path,
    hash_capture: SmartHashCapture,
    stats: dict
):
    """Process a single ISO file to both XISO and CHD formats."""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Get source hashes (DAT lookup - instant!)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    source_hashes = hash_capture.get_source_hashes(iso_file, 'xbox360')
    
    if source_hashes.verified:
        stats['dat_hits'] += 1
    else:
        stats['calculated'] += 1
    
    stats['total_source_size'] += source_hashes.size
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Check if already processed
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    existing_xiso = db.find_transformation(
        source_md5=source_hashes.md5,
        tool='extract-xiso',
        tool_version='2.5.0'
    )
    
    existing_chd = db.find_transformation(
        source_md5=source_hashes.md5,
        tool='chdman',
        tool_version='0.251'
    )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Process to XISO (if needed)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    if not existing_xiso:
        xiso_file = output_xiso_dir / f"{iso_file.stem}.xiso"
        
        # Extract
        extract_xiso(iso_file, xiso_file)
        
        # Hash
        xiso_hashes = calculate_all_hashes(xiso_file)
        stats['total_xiso_size'] += xiso_hashes.size
        
        # Store transformation
        db.store_transformation(
            source_md5=source_hashes.md5,
            source_sha1=source_hashes.sha1,
            source_verified=source_hashes.verified,
            source_dat=source_hashes.source if source_hashes.verified else None,
            tool='extract-xiso',
            tool_version='2.5.0',
            final_md5=xiso_hashes.md5,
            final_sha1=xiso_hashes.sha1,
            final_size=xiso_hashes.size,
            final_format='xiso'
        )
        
        stats['xiso_created'] += 1
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Process to CHD (if needed)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    if not existing_chd:
        chd_file = output_chd_dir / f"{iso_file.stem}.chd"
        
        # Convert
        chdman_create(iso_file, chd_file)
        
        # Hash
        chd_hashes = calculate_all_hashes(chd_file)
        stats['total_chd_size'] += chd_hashes.size
        
        # Store transformation
        db.store_transformation(
            source_md5=source_hashes.md5,  # Same source!
            source_sha1=source_hashes.sha1,
            source_verified=source_hashes.verified,
            source_dat=source_hashes.source if source_hashes.verified else None,
            tool='chdman',
            tool_version='0.251',
            params={'compression': 'lzma'},
            final_md5=chd_hashes.md5,
            final_sha1=chd_hashes.sha1,
            final_size=chd_hashes.size,
            final_format='chd'
        )
        
        stats['chd_created'] += 1


def print_final_statistics(stats: dict):
    """Print comprehensive statistics."""
    
    console.print("\n" + "━" * 70)
    console.print("[bold cyan]PROCESSING COMPLETE[/bold cyan]")
    console.print("━" * 70 + "\n")
    
    # Create statistics table
    table = Table(title="Processing Statistics", show_header=True)
    table.add_column("Metric", style="cyan", width=40)
    table.add_column("Value", justify="right", style="green")
    
    # Processing stats
    table.add_row("Files Processed", str(stats['processed']))
    table.add_row("XISO Files Created", str(stats['xiso_created']))
    table.add_row("CHD Files Created", str(stats['chd_created']))
    table.add_row("Total Transformations", str(stats['xiso_created'] + stats['chd_created']))
    
    table.add_section()
    
    # Hash capture stats
    dat_pct = (stats['dat_hits'] / stats['processed'] * 100) if stats['processed'] else 0
    calc_pct = (stats['calculated'] / stats['processed'] * 100) if stats['processed'] else 0
    
    table.add_row("Source Hashes from DAT", f"{stats['dat_hits']} ({dat_pct:.1f}%)")
    table.add_row("Source Hashes Calculated", f"{stats['calculated']} ({calc_pct:.1f}%)")
    
    table.add_section()
    
    # Size stats
    source_gb = stats['total_source_size'] / 1_000_000_000
    xiso_gb = stats['total_xiso_size'] / 1_000_000_000
    chd_gb = stats['total_chd_size'] / 1_000_000_000
    
    xiso_saved = ((1 - xiso_gb/source_gb) * 100) if source_gb else 0
    chd_saved = ((1 - chd_gb/source_gb) * 100) if source_gb else 0
    
    table.add_row("Source Total Size", f"{source_gb:.2f} GB")
    table.add_row("XISO Total Size", f"{xiso_gb:.2f} GB ({xiso_saved:.1f}% smaller)")
    table.add_row("CHD Total Size", f"{chd_gb:.2f} GB ({chd_saved:.1f}% smaller)")
    table.add_row("Total Space Saved", f"{(source_gb*2 - xiso_gb - chd_gb):.2f} GB")
    
    console.print(table)
    
    # Performance impact
    console.print("\n[bold]Performance Impact:[/bold]")
    
    # Estimate time saved
    calc_time_saved = stats['dat_hits'] * 2  # ~2 minutes per file not hashed
    
    console.print(
        f"  [green]✓ DAT lookups:[/green] {dat_pct:.1f}% (instant!)\n"
        f"  [green]✓ Time saved:[/green] ~{calc_time_saved/60:.1f} hours of hashing\n"
        f"  [green]✓ Transformations tracked:[/green] Ready for ScreenScraper integration"
    )
    
    console.print("\n[bold green]✓✓✓ SUCCESS ✓✓✓[/bold green]\n")


if __name__ == "__main__":
    process_xbox360_collection()
```

### Expected Output

```
ROM Farmer - Xbox 360 Collection Processing

Loading DAT files...
✓ Loaded Redump Xbox 360 DAT: 1,247 games

Found 250 ISO files to process

⠋ 100% • Halo 3 (USA).iso...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROCESSING COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                     Processing Statistics                      
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Metric                                 ┃             Value ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ Files Processed                        │               250 │
│ XISO Files Created                     │               250 │
│ CHD Files Created                      │               250 │
│ Total Transformations                  │               500 │
├────────────────────────────────────────┼───────────────────┤
│ Source Hashes from DAT                 │      247 (98.8%) │
│ Source Hashes Calculated               │          3 (1.2%) │
├────────────────────────────────────────┼───────────────────┤
│ Source Total Size                      │         1,825.00 GB │
│ XISO Total Size                        │         1,687.50 GB (7.5% smaller) │
│ CHD Total Size                         │         1,460.00 GB (20.0% smaller) │
│ Total Space Saved                      │           477.50 GB │
└────────────────────────────────────────┴───────────────────┘

Performance Impact:
  ✓ DAT lookups: 98.8% (instant!)
  ✓ Time saved: ~8.2 hours of hashing
  ✓ Transformations tracked: Ready for ScreenScraper integration

✓✓✓ SUCCESS ✓✓✓
```

### Key Benefits Demonstrated

1. **98.8% DAT hit rate** - Almost all source hashes instant
2. **8.2 hours saved** - Not hashing 247 source files
3. **477 GB saved** - XISO + CHD vs 2× source ISOs
4. **500 transformations tracked** - Ready for metadata scraping
5. **Verified provenance** - 247/250 verified by Redump

### Next Steps After Processing

```bash
# Now scrape metadata using source hashes!
romfarmer scrape-batch ~/collection/xbox360-xiso \
  --system xbox360 \
  --use-transformations \
  --screenscraper-auth

# Generate gamelists
romfarmer metadata generate \
  ~/collection/xbox360-xiso \
  ~/batocera/roms/xbox360 \
  --media-types all

# Export transformations for community
romfarmer export-transformations \
  --system xbox360 \
  --verified-only \
  --output ~/xbox360-transformations.json
```

---

**Document Version**: 1.0  
**Last Updated**: October 11, 2025  
**Status**: Awaiting Implementation  
**Priority**: High Impact, High Value

*This proposal represents a significant advancement in ROM collection management and metadata scraping. Implementation would benefit the entire retro gaming community.*
