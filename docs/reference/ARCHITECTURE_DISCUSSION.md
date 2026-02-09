# Architecture Discussion: Stage Callbacks vs Linear Pipeline

## Question
Should we add Unmanic-style plugin callbacks where stages can react to events at multiple points in the workflow?

## Use Case
**M3U Metadata Example:**
- `CreateM3UStage` creates M3U files (Stage 5)
- `MetadataStage` generates gamelist.xml (Stage 7)
- Metadata stage needs to know: "Hide individual discs, show only M3U"

## Current Architecture: Linear Pipeline with Rich Context ✅

### How It Works
```python
# CreateM3UStage (Stage 5)
def execute(self, context):
    # Create M3U files
    context.m3u_files = [...]
    context.disc_metadata = {
        "Panzer Dragoon Saga (USA)": DiscMetadata(
            primary_file=Path("Panzer Dragoon Saga (USA).m3u"),
            all_discs=[disc1, disc2, disc3, disc4],
            needs_m3u=True,
        )
    }
    return result

# MetadataStage (Stage 7) - reads context!
def execute(self, context):
    for game_name, metadata in context.disc_metadata.items():
        if metadata.needs_m3u:
            # Create entry for M3U (visible)
            self._add_game_entry(metadata.primary_file, hidden=False)
            
            # Hide individual discs
            for disc in metadata.all_discs:
                self._add_game_entry(disc, hidden=True)
```

**Advantages:**
- ✅ Simple: Each stage runs once in order
- ✅ Clear data flow: Context passed forward
- ✅ Already solves the M3U problem!
- ✅ Easy to debug: Linear execution
- ✅ Predictable: No hidden side effects

**Limitations:**
- ❌ Stages can't react to future events
- ❌ Can't easily add cross-cutting concerns later

## Alternative: Event-Based Callbacks (Unmanic Style)

### How It Would Work
```python
class Stage(ABC):
    def execute(self, context):
        """Main execution"""
        pass
    
    # Optional callbacks
    def on_file_extracted(self, context, file_path):
        """Called when any file is extracted"""
        pass
    
    def on_m3u_created(self, context, m3u_path, discs):
        """Called when M3U is created"""
        pass
    
    def on_metadata_generation(self, context, file_path):
        """Called for each file during metadata generation"""
        pass

# Pipeline execution
for stage in stages:
    result = stage.execute(context)
    
# Then for each event:
for file in context.extracted_files:
    for stage in stages:
        stage.on_file_extracted(context, file)

for m3u in context.m3u_files:
    for stage in stages:
        stage.on_m3u_created(context, m3u, discs)
```

**Advantages:**
- ✅ Flexible: Stages can react to any event
- ✅ Extensible: New stages can hook into existing workflows
- ✅ Decoupled: Stages don't need to know about each other

**Disadvantages:**
- ❌ Complex: More moving parts
- ❌ Harder to debug: Non-linear execution
- ❌ Performance: Multiple passes over data
- ❌ Potential conflicts: Multiple stages modifying same state

## Recommendation: **Enhanced Linear Pipeline** (Best of Both)

Keep our simple linear pipeline, but add **optional lifecycle hooks**:

```python
class Stage(ABC):
    """Base stage with optional hooks."""
    
    @abstractmethod
    def execute(self, context: StageContext) -> StageResult:
        """Main execution - REQUIRED"""
        pass
    
    # Optional hooks (default: do nothing)
    def post_execute_all(self, context: StageContext):
        """Called ONCE after all stages complete.
        
        Use this for:
        - Final validation
        - Cross-stage cleanup
        - Generating reports based on full pipeline
        """
        pass

class Pipeline:
    def execute(self, ...):
        # Phase 1: Execute all stages linearly
        for stage in self.stages:
            result = stage.execute(context)
            if result.status == StageStatus.FAILED:
                break
        
        # Phase 2: Post-execute hooks (optional)
        if all_stages_succeeded:
            for stage in self.stages:
                stage.post_execute_all(context)
        
        return results
```

### Example: M3U Metadata Case
```python
class CreateM3UStage(Stage):
    def execute(self, context):
        # Create M3U files
        context.disc_metadata = {...}  # Store metadata
        return result
    
    # No post_execute_all needed!

class MetadataStage(Stage):
    def execute(self, context):
        # Read context.disc_metadata directly
        for game_name, metadata in context.disc_metadata.items():
            if metadata.needs_m3u:
                # M3U exists, hide individual discs
                self._create_gamelist_entry(
                    file=metadata.primary_file,  # M3U
                    hidden=False,
                    image=f"{metadata.first_disc_path.stem}.png"
                )
                for disc in metadata.all_discs:
                    self._create_gamelist_entry(disc, hidden=True)
        return result
```

**This already works with current architecture!** No changes needed.

## When Would We Need More?

**Scenario: Custom User Stages**

If users want to write custom stages (like Unmanic plugins), callbacks help:

```python
# User's custom stage
class CustomValidationStage(Stage):
    def execute(self, context):
        # Skip - not our main job
        return StageResult(status=StageStatus.SKIPPED)
    
    def post_execute_all(self, context):
        # After everything: validate all CHDs exist
        for chd in context.compressed_files:
            if not chd.exists():
                self.console.print(f"[red]Missing: {chd}[/red]")
```

## Decision Matrix

| Requirement | Current Pipeline | + post_execute_all | Full Event System |
|-------------|------------------|-------------------|-------------------|
| M3U metadata hiding | ✅ | ✅ | ✅ |
| Simple to understand | ✅ | ✅ | ❌ |
| Cross-stage validation | ⚠️ | ✅ | ✅ |
| Custom user stages | ❌ | ⚠️ | ✅ |
| Performance | ✅ | ✅ | ❌ |
| Debugging | ✅ | ✅ | ❌ |

Legend:
- ✅ Fully supports
- ⚠️ Partially supports
- ❌ Doesn't support

## Final Recommendation

**For Now: Keep current linear pipeline** ✅

**Reasons:**
1. **It already solves your M3U case!** Context carries all needed info forward.
2. **YAGNI Principle**: Don't add complexity until we need it.
3. **Clear Data Flow**: Each stage updates context, next stage reads it.
4. **Easy to Debug**: Step through stages in order.

**Future Enhancement (if needed):**

Add **one** optional hook: `post_execute_all()` for final validation/cleanup.

**Don't Add:**
- Multiple callback events (on_file_extracted, on_m3u_created, etc.)
- Event-based plugin system
- Complex lifecycle management

Keep it simple until we hit a real limitation!

## Proof: Current Architecture Already Works

```python
# Phase 5: CreateM3UStage
context.disc_metadata = {
    "Game A": DiscMetadata(primary_file="Game A.m3u", all_discs=[...]),
    "Game B": DiscMetadata(primary_file="Game B.chd", all_discs=[...]),  # Single disc
}

# Phase 7: MetadataStage (reads context.disc_metadata)
for game_name, metadata in context.disc_metadata.items():
    entry = GamelistEntry(
        path=metadata.primary_file,
        name=metadata.title,
        image=f"{metadata.first_disc_path.stem}.png",
    )
    
    if metadata.needs_m3u:
        # Hide the individual discs
        for disc in metadata.all_discs:
            hidden_entry = GamelistEntry(path=disc, hidden=True)
            gamelist.add(hidden_entry)
    
    gamelist.add(entry)
```

**No callbacks needed!** The context already carries all the information forward.

## Summary

**Your M3U Question:** ✅ Already handled by `context.disc_metadata`

**Unmanic-Style Callbacks:** ❌ Not needed for current use cases

**Recommendation:** Keep the simple linear pipeline with rich context passing

**Future:** Add optional `post_execute_all()` hook only if we hit a real limitation
