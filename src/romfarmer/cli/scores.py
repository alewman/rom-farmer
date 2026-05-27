"""
CLI commands for fetching and querying external game scores.

Usage
-----
    romfarmer scores fetch --platform ps2
    romfarmer scores fetch --all
    romfarmer scores show  --platform ps2 --min-score 8.0
    romfarmer scores stats
    romfarmer scores lookup "Resident Evil 4" --platform ps2
"""

import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

console = Console()

DEFAULT_DB = "metadata/database/romfarmer.db"


@click.group("scores")
def scores_group() -> None:
    """Fetch and query external game scores (MobyGames, RAWG)."""


# ---------------------------------------------------------------------------
# fetch
# ---------------------------------------------------------------------------


@scores_group.command("fetch")
@click.option(
    "--platform",
    "-p",
    default=None,
    help="Platform to fetch (e.g. ps2, snes). Required unless --all is set.",
)
@click.option(
    "--all", "fetch_all", is_flag=True, default=False,
    help="Fetch scores for all supported platforms.",
)
@click.option(
    "--source",
    default="mobygames",
    type=click.Choice(["mobygames", "rawg"], case_sensitive=False),
    show_default=True,
    help="Score source to use.",
)
@click.option(
    "--api-key",
    envvar="MOBYGAMES_API_KEY",
    default=None,
    help="API key. Defaults to MOBYGAMES_API_KEY env var.",
)
@click.option(
    "--rate-limit",
    default=1.1,
    show_default=True,
    type=float,
    help=(
        "Seconds between API requests. "
        "Hobbyist tier = 720 req/hour hard limit. "
        "Use 5.0 for guaranteed no-429 (1 req/5s = exactly 720/hour). "
        "Default 1.1 is faster but may hit hourly quota; "
        "on 429 the client auto-waits until the next UTC :00 reset."
    ),
)
@click.option(
    "--db",
    "db_path",
    default=DEFAULT_DB,
    show_default=True,
    help="Path to romfarmer.db metadata database.",
)
@click.option(
    "--platforms",
    "platform_list",
    default=None,
    help="Comma-separated list of platforms to fetch (alternative to --all).",
)
def fetch_command(
    platform: Optional[str],
    fetch_all: bool,
    source: str,
    api_key: Optional[str],
    rate_limit: float,
    db_path: str,
    platform_list: Optional[str],
) -> None:
    """
    Fetch game scores from an external source and store them in the DB.

    \b
    Examples:
        romfarmer scores fetch --platform ps2
        romfarmer scores fetch --all --rate-limit 15
        romfarmer scores fetch --platforms ps2,ps3,psx
        MOBYGAMES_API_KEY=xxx romfarmer scores fetch --platform snes
    """
    from romfarmer.metadata.database import MetadataDatabase
    from romfarmer.metadata.external_scores import (
        MobyGamesFetcher,
        RawgFetcher,
        MOBYGAMES_PLATFORM_IDS,
        RAWG_PLATFORM_IDS,
    )

    # Determine target platforms
    if platform_list:
        targets = [p.strip() for p in platform_list.split(",") if p.strip()]
    elif platform:
        targets = [platform]
    elif fetch_all:
        platform_map = MOBYGAMES_PLATFORM_IDS if source == "mobygames" else RAWG_PLATFORM_IDS
        targets = list(platform_map.keys())
    else:
        raise click.UsageError(
            "Specify --platform <name>, --platforms <list>, or --all."
        )

    db = MetadataDatabase(Path(db_path))

    if source == "mobygames":
        resolved_key = api_key or os.environ.get("MOBYGAMES_API_KEY", "")
        if not resolved_key:
            console.print(
                "[red]Error:[/red] MobyGames API key required.\n"
                "  Pass [bold]--api-key KEY[/bold] or set "
                "[bold]MOBYGAMES_API_KEY[/bold] environment variable.\n"
                "  Register at: https://www.mobygames.com/info/api/"
            )
            sys.exit(1)
        fetcher = MobyGamesFetcher(db=db, api_key=resolved_key, rate_limit_seconds=rate_limit)
    else:
        resolved_key = api_key or os.environ.get("RAWG_API_KEY", "")
        if not resolved_key:
            console.print(
                "[red]Error:[/red] RAWG API key required.\n"
                "  Pass [bold]--api-key KEY[/bold] or set "
                "[bold]RAWG_API_KEY[/bold] environment variable.\n"
                "  Register at: https://rawg.io/apidocs"
            )
            sys.exit(1)
        fetcher = RawgFetcher(db=db, api_key=resolved_key)

    total_stored = 0
    errors: list[str] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=False,
    ) as progress:
        outer_task = progress.add_task(
            f"[cyan]Fetching {source} scores...[/cyan]",
            total=len(targets),
        )

        for platform_name in targets:
            progress.update(
                outer_task,
                description=f"[cyan]{source}[/cyan] → [yellow]{platform_name}[/yellow]",
            )

            pages_done = [0]

            def on_progress(fetched: int, stored: int, page: int) -> None:
                pages_done[0] = page
                progress.update(
                    outer_task,
                    description=(
                        f"[cyan]{source}[/cyan] → [yellow]{platform_name}[/yellow] "
                        f"page {page} ({stored} stored)"
                    ),
                )

            try:
                count = fetcher.fetch_platform(platform_name, progress_callback=on_progress)
                total_stored += count
                console.print(
                    f"  [green]✓[/green] {platform_name}: "
                    f"[bold]{count}[/bold] games stored "
                    f"({pages_done[0]} pages)"
                )
            except ValueError as exc:
                console.print(f"  [yellow]⚠[/yellow]  {platform_name}: {exc}")
                errors.append(platform_name)
            except Exception as exc:
                console.print(f"  [red]✗[/red] {platform_name}: {exc}")
                errors.append(platform_name)

            progress.advance(outer_task)

    console.print(
        f"\n[bold green]Done.[/bold green] "
        f"Total stored: [bold]{total_stored}[/bold] game scores."
    )
    if errors:
        console.print(
            f"[yellow]Skipped {len(errors)} platform(s) with errors: "
            f"{', '.join(errors)}[/yellow]"
        )


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------


@scores_group.command("show")
@click.option("--platform", "-p", required=True, help="Platform to show (e.g. ps2).")
@click.option(
    "--source",
    default=None,
    type=click.Choice(["mobygames", "rawg"], case_sensitive=False),
    help="Filter by source.",
)
@click.option(
    "--min-score",
    default=None,
    type=float,
    help="Minimum user score (0-10 scale).",
)
@click.option(
    "--min-critic",
    default=None,
    type=int,
    help="Minimum critic score (0-100 scale).",
)
@click.option("--limit", "-n", default=50, show_default=True, help="Max rows to display.")
@click.option("--db", "db_path", default=DEFAULT_DB, show_default=True)
def show_command(
    platform: str,
    source: Optional[str],
    min_score: Optional[float],
    min_critic: Optional[int],
    limit: int,
    db_path: str,
) -> None:
    """Show external scores for a platform."""
    from romfarmer.metadata.database import MetadataDatabase

    db = MetadataDatabase(Path(db_path))
    scores = db.get_external_scores_for_platform(
        platform=platform,
        source=source,
        min_user_score=min_score,
        min_critic_score=min_critic,
    )

    if not scores:
        console.print(
            f"[yellow]No external scores found for '{platform}'.[/yellow] "
            f"Run [bold]romfarmer scores fetch --platform {platform}[/bold] first."
        )
        return

    table = Table(title=f"External Scores — {platform} ({len(scores)} games)")
    table.add_column("Title", style="cyan", max_width=50)
    table.add_column("User Score", justify="right")
    table.add_column("Critic", justify="right")
    table.add_column("Source", style="dim")

    displayed = 0
    for s in scores:
        if displayed >= limit:
            break
        user = f"{s.user_score:.1f}/10" if s.user_score is not None else "—"
        critic = str(s.critic_score) if s.critic_score is not None else "—"
        table.add_row(s.title, user, critic, s.source)
        displayed += 1

    console.print(table)
    if len(scores) > limit:
        console.print(f"[dim]... and {len(scores) - limit} more (use --limit to see more)[/dim]")


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------


@scores_group.command("stats")
@click.option("--db", "db_path", default=DEFAULT_DB, show_default=True)
def stats_command(db_path: str) -> None:
    """Show coverage statistics for all fetched external scores."""
    from romfarmer.metadata.database import MetadataDatabase

    db = MetadataDatabase(Path(db_path))
    rows = db.get_external_scores_stats()

    if not rows:
        console.print(
            "[yellow]No external scores in DB yet.[/yellow] "
            "Run [bold]romfarmer scores fetch --all[/bold] to populate."
        )
        return

    table = Table(title="External Score Coverage")
    table.add_column("Platform", style="cyan")
    table.add_column("Source", style="dim")
    table.add_column("Games", justify="right")
    table.add_column("With User", justify="right")
    table.add_column("With Critic", justify="right")
    table.add_column("Avg User Score", justify="right")
    table.add_column("Last Fetched", style="dim")

    for r in rows:
        last = r["last_fetch"].strftime("%Y-%m-%d") if r["last_fetch"] else "—"
        avg = f"{r['avg_user_score']:.2f}" if r["avg_user_score"] else "—"
        table.add_row(
            r["platform"],
            r["source"],
            str(r["count"]),
            str(r["with_user"]),
            str(r["with_critic"]),
            avg,
            last,
        )

    console.print(table)


# ---------------------------------------------------------------------------
# lookup
# ---------------------------------------------------------------------------


@scores_group.command("lookup")
@click.argument("title")
@click.option("--platform", "-p", required=True, help="Platform to search (e.g. ps2).")
@click.option("--db", "db_path", default=DEFAULT_DB, show_default=True)
def lookup_command(title: str, platform: str, db_path: str) -> None:
    """
    Look up the external score for a game by title.

    Uses the same normalized matching that the pipeline uses.

    \b
    Examples:
        romfarmer scores lookup "Resident Evil 4" --platform ps2
        romfarmer scores lookup "Gran Turismo 3 (USA)" --platform ps2
    """
    from romfarmer.metadata.database import MetadataDatabase
    from romfarmer.metadata.external_scores import normalize_title

    db = MetadataDatabase(Path(db_path))
    normalized = normalize_title(title)
    result = db.lookup_external_score(platform=platform, normalized_title=normalized)

    console.print(f"[dim]Normalized query:[/dim] '{normalized}'")

    if result is None:
        console.print(
            f"[yellow]No match found[/yellow] for '{title}' on {platform}.\n"
            "Try fetching scores first: "
            f"[bold]romfarmer scores fetch --platform {platform}[/bold]"
        )
        return

    user = f"{result.user_score:.1f}/10" if result.user_score is not None else "N/A"
    critic = f"{result.critic_score}/100" if result.critic_score is not None else "N/A"
    normalized_0_to_1 = result.best_score_normalized

    table = Table(show_header=False)
    table.add_column("Field", style="dim")
    table.add_column("Value", style="cyan")
    table.add_row("Title", result.title)
    table.add_row("Platform", result.platform)
    table.add_row("User Score", user)
    table.add_row("Critic Score", critic)
    table.add_row("Normalized (0-1)", f"{normalized_0_to_1:.3f}" if normalized_0_to_1 else "N/A")
    table.add_row("Source", result.source)
    table.add_row("URL", result.url or "—")

    console.print(table)
