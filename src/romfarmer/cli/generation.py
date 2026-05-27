"""Generation-level cross-platform deduplication commands.

Provides analysis and rescue list generation for 1G1Gen filtering.
"""

import asyncio
import json
import sqlite3
import click
from pathlib import Path
from collections import defaultdict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

import yaml

from romfarmer.cross_platform.game_normalizer import GameNameNormalizer

console = Console()

# These are resolved lazily at call-time via the paths system to support any workspace layout.
# They can be overridden via CLI flags or environment variables.
def _default_output_base() -> Path:
    from romfarmer.core.paths import paths
    return paths.output_dir.parent / "roms-retrobat"

def _default_generations_yaml() -> Path:
    from romfarmer.core.paths import paths
    return paths.workspace_root / "config" / "generations.yaml"

def _default_rescue_dir() -> Path:
    from romfarmer.core.paths import paths
    return paths.workspace_root / "config" / "curations" / "rescue"

def _default_metadata_db() -> Path:
    from romfarmer.core.paths import paths
    return paths.metadata_db

# File extensions to scan per type
GAME_EXTENSIONS = ['*.chd', '*.rvz', '*.iso', '*.xiso', '*.cue', '*.m3u']
# Folder-based platforms (games are directories, not files)
FOLDER_PLATFORMS = {'ps3'}


def _load_generations() -> dict:
    """Load generation definitions from YAML."""
    data = yaml.safe_load(_default_generations_yaml().read_text())
    return {g['name']: g for g in data['generations']}


def _load_platform_games(platform: str, output_base: Path) -> list[Path]:
    """Load game files/folders from a platform output directory."""
    platform_dir = output_base / platform
    if not platform_dir.exists():
        return []

    if platform in FOLDER_PLATFORMS:
        # Folder-based: each subdirectory (except Best Games) is a game
        return [
            p for p in platform_dir.iterdir()
            if p.is_dir() and p.name not in ('Best Games', '_Best Games')
        ]
    else:
        # File-based: glob game files
        games = []
        for pattern in GAME_EXTENSIONS:
            games.extend(platform_dir.glob(pattern))
        return games


def _find_duplicates(
    output_base: Path,
    platforms: list[str],
) -> tuple[dict, dict[str, list]]:
    """Find cross-platform duplicate games.

    Returns:
        (duplicates, platform_games) where:
        - duplicates: {match_key: {platform: NormalizedGame}}
        - platform_games: {platform: [NormalizedGame]}
    """
    normalizer = GameNameNormalizer()
    platform_games = {}
    game_index = defaultdict(dict)

    for platform_name in platforms:
        files = _load_platform_games(platform_name, output_base)
        normalized = []
        for f in files:
            game_name = f.stem
            ng = normalizer.normalize(game_name, platform_name, str(f))
            normalized.append(ng)
            game_index[ng.match_key()][platform_name] = ng
        platform_games[platform_name] = normalized

    # Filter to games on 2+ platforms
    duplicates = {
        key: platforms_dict
        for key, platforms_dict in game_index.items()
        if len(platforms_dict) >= 2
    }
    return duplicates, platform_games


def _enrich_with_metadata(
    duplicate_games: list[dict],
    db_path: Path | None = None,
) -> list[dict]:
    """Enrich duplicate game records with ScreenScraper metadata.

    Queries the scraped_games table using fuzzy name matching to add
    genre, rating, developer, and player count per platform version.
    """
    if db_path is None:
        db_path = _default_metadata_db()
    if not db_path.exists():
        return duplicate_games

    db = sqlite3.connect(str(db_path))
    db.row_factory = sqlite3.Row

    # System name mapping (our platform names → ScreenScraper system names)
    sys_map = {
        'psx': 'psx', 'saturn': 'saturn',
        'ps2': 'ps2', 'gamecube': 'gamecube', 'xbox': 'xbox',
        'dreamcast': 'dreamcast',
        'ps3': 'ps3', 'xbox360': 'xbox360', 'wii': 'wii',
        'megacd': 'megacd', 'pcenginecd': 'pcenginecd', 'neogeocd': 'neogeocd',
    }

    for game in duplicate_games:
        game['metadata'] = {}
        # Sanitize game name for SQL LIKE
        base_name = game['name'].split('(')[0].strip()
        # Escape SQL LIKE wildcards
        safe_name = base_name.replace('%', '\\%').replace('_', '\\_')
        like_pattern = f"%{safe_name}%"

        for platform in game['platforms']:
            system = sys_map.get(platform, platform)
            try:
                row = db.execute(
                    "SELECT name, genre, rating, developer, players "
                    "FROM scraped_games WHERE system = ? AND name LIKE ? ESCAPE '\\' LIMIT 1",
                    (system, like_pattern),
                ).fetchone()
                if row:
                    game['metadata'][platform] = {
                        'genre': row['genre'] or '',
                        'rating': row['rating'] or 0.0,
                        'developer': row['developer'] or '',
                        'players': row['players'] or '',
                    }
            except Exception:
                pass

    db.close()
    return duplicate_games


@click.group(name='generation')
def generation_group():
    """Cross-generation deduplication (1G1Gen)."""
    pass


@generation_group.command()
@click.argument('gen_name')
@click.option('--output-base', type=click.Path(exists=True),
              default=None, help='Base output directory')
@click.option('--json-out', type=click.Path(), help='Save analysis as JSON')
def analyze(gen_name: str, output_base: str, json_out: str):
    """Analyze cross-platform duplicates for a generation.

    Scans build output directories and identifies games that exist on
    multiple platforms. Does not modify any files.

    Example: romfarmer generation analyze gen6
    """
    gens = _load_generations()
    if gen_name not in gens:
        console.print(f"[red]Unknown generation: {gen_name}[/red]")
        console.print(f"Available: {', '.join(gens.keys())}")
        raise SystemExit(1)

    gen = gens[gen_name]
    platforms = [p['name'] for p in gen['platforms']]

    console.print(Panel(
        f"[bold]{gen['label']}[/bold]\n"
        f"Platforms: {' > '.join(platforms)}\n"
        f"Primary: {platforms[0]}",
        title="Generation Analysis",
    ))

    output_path = Path(output_base)

    # Count games per platform
    console.print("\n[cyan]Scanning platform directories...[/cyan]")
    for p in platforms:
        files = _load_platform_games(p, output_path)
        console.print(f"  {p:12s}: {len(files):,} games")

    # Find duplicates
    duplicates, platform_games = _find_duplicates(output_path, platforms)
    total_games = sum(len(g) for g in platform_games.values())

    console.print(f"\n[green]Cross-platform duplicates: {len(duplicates):,}[/green]")
    console.print(f"Total games across platforms: {total_games:,}")

    # Show platform overlap matrix
    table = Table(title="Platform Overlap")
    table.add_column("Platforms", style="cyan")
    table.add_column("Shared Games", justify="right")

    # Count pairwise overlaps
    pair_counts = defaultdict(int)
    for match_key, plats in duplicates.items():
        plat_names = sorted(plats.keys())
        for i in range(len(plat_names)):
            for j in range(i + 1, len(plat_names)):
                pair = f"{plat_names[i]} + {plat_names[j]}"
                pair_counts[pair] += 1

    for pair, count in sorted(pair_counts.items(), key=lambda x: -x[1]):
        table.add_row(pair, str(count))
    console.print(table)

    # Show what would be removed (mirrors actual FilterGenerationStage logic)
    would_remove = defaultdict(int)
    for match_key, plats in duplicates.items():
        # Find highest priority platform that has this game
        keeper = None
        for p in platforms:
            if p in plats:
                keeper = p
                break
        if not keeper:
            continue
        for p in plats:
            if p != keeper:
                would_remove[p] += 1

    console.print(f"\n[yellow]Without rescue lists, would remove:[/yellow]")
    for p in platforms[1:]:
        before = len(platform_games.get(p, []))
        removed = would_remove.get(p, 0)
        after = before - removed
        pct = (removed / before * 100) if before > 0 else 0
        console.print(f"  {p:12s}: {before:,} -> {after:,}  (-{removed:,}, {pct:.0f}% removed)")

    # Show with rescue lists if available
    rescue_file = _default_rescue_dir() / f"rescue-{gen_name}.yaml"
    if rescue_file.exists():
        import yaml as _yaml
        rescue_data = _yaml.safe_load(rescue_file.read_text())
        rescue_lists = rescue_data.get("rescue_lists", {}) if rescue_data else {}
        if rescue_lists:
            # Recompute with rescue swaps: rescued games swap the keeper
            would_remove_r = defaultdict(int)
            for match_key, plats in duplicates.items():
                keeper = None
                for p in platforms:
                    if p in plats:
                        keeper = p
                        break
                if not keeper:
                    continue
                # Check if any non-keeper platform is rescued
                swapped = False
                for p in plats:
                    if p == keeper:
                        continue
                    rescued_games = rescue_lists.get(p, [])
                    any_game = plats[p]
                    if (any_game.original_name.lower() in [g.lower() for g in rescued_games] or
                            any_game.normalized_name.lower() in [g.lower() for g in rescued_games]):
                        # Swap: remove keeper instead, keep rescued platform
                        would_remove_r[keeper] += 1
                        for other_p in plats:
                            if other_p != p:
                                would_remove_r[other_p] += 1
                        # Undo the rescued platform
                        would_remove_r[p] -= 1
                        swapped = True
                        break
                if not swapped:
                    for p in plats:
                        if p != keeper:
                            would_remove_r[p] += 1

            total_rescued = sum(len(g) for g in rescue_lists.values())
            console.print(f"\n[green]With rescue lists ({total_rescued} rescues), would remove:[/green]")
            total_removed = 0
            for p in platforms:
                removed = would_remove_r.get(p, 0)
                if removed > 0:
                    before = len(platform_games.get(p, []))
                    after = before - removed
                    pct = (removed / before * 100) if before > 0 else 0
                    console.print(f"  {p:12s}: {before:,} -> {after:,}  (-{removed:,}, {pct:.0f}% removed)")
                    total_removed += removed
            console.print(f"  [bold]Total removals: {total_removed:,}[/bold]")

    # Top overlapping games (appear on most platforms)
    multi_plat = sorted(
        [(k, v) for k, v in duplicates.items()],
        key=lambda x: -len(x[1])
    )
    if multi_plat:
        table2 = Table(title=f"Games on Most Platforms (top 20)")
        table2.add_column("Game", style="green")
        table2.add_column("Platforms", style="cyan")
        for key, plats in multi_plat[:20]:
            # Use any platform's original name
            name = next(iter(plats.values())).original_name
            table2.add_row(name, ', '.join(sorted(plats.keys())))
        console.print(table2)

    # Build export data
    export = []
    for match_key, plats in duplicates.items():
        any_game = next(iter(plats.values()))
        export.append({
            'name': any_game.original_name,
            'match_key': match_key,
            'platforms': sorted(plats.keys()),
        })

    if json_out:
        Path(json_out).write_text(json.dumps(export, indent=2))
        console.print(f"\n[green]Saved {len(export)} duplicates to {json_out}[/green]")

    return export


@generation_group.command()
@click.argument('gen_name')
@click.option('--output-base', type=click.Path(exists=True),
              default=None, help='Base output directory')
@click.option('--model', default='claude-haiku-4.5',
              help='Model to use for rescue evaluation')
@click.option('--batch-size', default=50, type=int,
              help='Games per LLM batch (higher = fewer API calls)')
@click.option('--force', is_flag=True, help='Regenerate even if cached')
@click.option('--dry-run', is_flag=True, help='Show what would be sent without calling LLM')
def rescue(gen_name: str, output_base: str, model: str, batch_size: int,
           force: bool, dry_run: bool):
    """Generate AI rescue lists for a generation.

    Finds cross-platform duplicates, enriches with metadata, then asks
    an LLM to identify games that should be "rescued" (kept on a
    non-primary platform because that version is superior).

    Example: romfarmer generation rescue gen6
    """
    from romfarmer.ai.rescue_generator import RescueListGenerator, RescueListResult

    gens = _load_generations()
    if gen_name not in gens:
        console.print(f"[red]Unknown generation: {gen_name}[/red]")
        raise SystemExit(1)

    gen = gens[gen_name]
    platforms = [p['name'] for p in gen['platforms']]
    primary = platforms[0]

    # Check cache first
    cache_file = _default_rescue_dir() / f"rescue-{gen_name}.yaml"
    if cache_file.exists() and not force:
        existing = RescueListResult.from_yaml(cache_file.read_text())
        console.print(f"[yellow]Cached rescue list exists: {cache_file}[/yellow]")
        console.print(f"  Total rescued: {existing.stats.get('total_rescued', '?')}")
        console.print(f"  Model: {existing.model}")
        console.print("  Use --force to regenerate")
        return

    console.print(Panel(
        f"[bold]{gen['label']}[/bold] — Rescue List Generation\n"
        f"Model: {model} | Batch size: {batch_size}\n"
        f"Primary: {primary} | Platforms: {' > '.join(platforms)}",
        title="1G1Gen Rescue Generator",
    ))

    # Find duplicates
    output_path = Path(output_base)
    duplicates, platform_games = _find_duplicates(output_path, platforms)

    console.print(f"Found [green]{len(duplicates):,}[/green] cross-platform duplicates")

    # Build game list for LLM
    games_for_llm = []
    for match_key, plats in duplicates.items():
        any_game = next(iter(plats.values()))
        games_for_llm.append({
            'name': any_game.original_name,
            'platforms': sorted(plats.keys()),
        })

    # Enrich with metadata
    console.print("[cyan]Enriching with ScreenScraper metadata...[/cyan]")
    games_for_llm = _enrich_with_metadata(games_for_llm)
    enriched_count = sum(1 for g in games_for_llm if g.get('metadata'))
    console.print(f"  Enriched {enriched_count}/{len(games_for_llm)} games with metadata")

    if dry_run:
        console.print(f"\n[yellow]DRY RUN — would send {len(games_for_llm)} games "
                       f"in {((len(games_for_llm) - 1) // batch_size) + 1} batches[/yellow]")
        # Show first batch as example
        sample = games_for_llm[:min(5, len(games_for_llm))]
        for g in sample:
            meta_str = ""
            if g.get('metadata'):
                meta_parts = []
                for p, m in g['metadata'].items():
                    meta_parts.append(f"{p}: {m.get('genre', '?')} rating={m.get('rating', '?')}")
                meta_str = f" [{'; '.join(meta_parts)}]"
            console.print(f"  {g['name']} — {', '.join(g['platforms'])}{meta_str}")
        return

    # Generate rescue lists
    generator = RescueListGenerator(model=model, batch_size=batch_size)
    result = asyncio.run(generator.generate_via_api(
        gen_name, platforms, games_for_llm,
    ))

    # Save
    _default_rescue_dir().mkdir(parents=True, exist_ok=True)
    generator.save(result, _default_rescue_dir())

    # Display results
    console.print(f"\n[green]Rescue generation complete![/green]")
    console.print(f"  Total evaluated: {result.stats.get('total_evaluated', 0)}")
    console.print(f"  Total rescued: {result.stats.get('total_rescued', 0)}")
    console.print(f"  Rescue rate: {result.stats.get('rescue_rate', '0%')}")

    if result.rescue_lists:
        table = Table(title="Rescue Summary")
        table.add_column("Platform", style="cyan")
        table.add_column("Rescued Games", justify="right")
        for platform, games in sorted(result.rescue_lists.items()):
            table.add_row(platform, str(len(games)))
        console.print(table)

        # Show rescued games
        for platform, games in sorted(result.rescue_lists.items()):
            console.print(f"\n[bold]{platform}[/bold] rescued games:")
            for g in sorted(games):
                # Find reason
                reason = ""
                for d in result.decisions:
                    if d.rescue_platform == platform and d.game_name == g:
                        reason = d.reason
                        break
                console.print(f"  • {g}")
                if reason:
                    console.print(f"    [dim]{reason}[/dim]")
