"""Post-build hooks and deployment as ``Protocol`` implementations.

Review G4 #11 / intent brief P0 item 7 (2.9-partial): the orchestrator used to
interpolate config strings into ``subprocess.run(..., shell=True)`` for
``type: command`` hooks and for rsync deploy.  Once an agent authors build
specs that is remote code execution.  Here every hook is a typed object and
every subprocess is an **argv list** (``shell=False``); the only substitution
is per-token replacement of ``{output_base}`` / ``{build_name}``.

Native hooks (``genre_organize``, ``quarantine_unpolished``, ``patch_gamelist``)
were moved verbatim from ``NewBuildOrchestrator``; their behaviour is unchanged.
"""

from __future__ import annotations

import logging
import shlex
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HookContext:
    """What a hook may see: the build's output tree and completed platforms."""

    build_name: str
    output_base: Path
    platforms: tuple[str, ...]  # completed platforms (or the hook's explicit list)
    metadata_db: Path
    workspace_root: Path


@dataclass(frozen=True)
class HookResult:
    ok: bool
    summary: str = ""


class PostBuildHook(Protocol):
    """One post-build action.  ``run`` must not shell out with config strings."""

    kind: str

    def run(self, hook: Any, ctx: HookContext) -> HookResult: ...


def _substitute(token: str, ctx: HookContext) -> str:
    return token.replace("{output_base}", str(ctx.output_base)).replace(
        "{build_name}", ctx.build_name
    )


def _run_argv(argv: Sequence[str], *, cwd: Path | None = None) -> HookResult:
    """Run an argv list (never a shell) and summarise the outcome."""
    logger.info("    argv: %s", " ".join(shlex.quote(a) for a in argv))
    try:
        result = subprocess.run(list(argv), capture_output=True, text=True, cwd=cwd, check=False)
    except OSError as exc:
        return HookResult(False, f"cannot execute {argv[0]!r}: {exc}")
    head = "\n".join(line for line in result.stdout.strip().splitlines()[:5] if line)
    if result.returncode == 0:
        return HookResult(True, head)
    return HookResult(False, f"exit {result.returncode}: {result.stderr.strip()[:500]}")


# ---------------------------------------------------------------------------
# Generic hooks
# ---------------------------------------------------------------------------


class CommandHook:
    """``type: command`` — ``command`` is parsed with ``shlex`` into argv.

    Placeholders are substituted per token, so an ``output_base`` containing
    spaces or shell metacharacters is one argument, never re-parsed.  Pipes,
    redirects and ``&&`` are not supported by design; write a native hook.
    """

    kind = "command"

    def run(self, hook: Any, ctx: HookContext) -> HookResult:
        command = getattr(hook, "command", None)
        if not command:
            return HookResult(True, "skipped (no command)")
        argv = [_substitute(tok, ctx) for tok in shlex.split(command)]
        return _run_argv(argv)


class JdupesHook:
    """``type: jdupes`` — hardlink duplicate files under the output tree.

    Options: ``args`` (list of extra jdupes flags; default ``["-r", "-L"]``).
    """

    kind = "jdupes"

    def run(self, hook: Any, ctx: HookContext) -> HookResult:
        opts: Mapping[str, Any] = getattr(hook, "options", None) or {}
        args = [str(a) for a in (opts.get("args") or ["-r", "-L"])]
        return _run_argv(["jdupes", *args, str(ctx.output_base)])


class NativeHook:
    """Adapter for the in-process hooks below (they log their own summaries)."""

    def __init__(self, kind: str, fn: Any) -> None:
        self.kind = kind
        self._fn = fn

    def run(self, hook: Any, ctx: HookContext) -> HookResult:
        self._fn(hook, ctx)
        return HookResult(True)


# ---------------------------------------------------------------------------
# Native hooks (moved from NewBuildOrchestrator, behaviour unchanged)
# ---------------------------------------------------------------------------


def _genre_organize(hook: Any, ctx: HookContext) -> None:
    """
    Run genre organization for all completed platforms.

    Iterates over completed platforms, looks each up in the metadata DB
    by system name, and creates hardlinked 'By Genre/' subdirectories.
    Zero disk cost on ZFS/same-filesystem hardlinks.

    Hook options (all optional):
        mode: hardlink | copy | symlink | move  (default: hardlink)
        merge_small: int  — merge genres with < N games into 'Other' (default: 3)
        exclude_genres: list of genre names to skip
        system_map: dict mapping platform → system name for DB lookups
        platforms: list of platforms to process (default: all completed)
    """
    from romfarmer.organizers.base import OrganizeMode
    from romfarmer.organizers.genre import GenreOrganizer

    mode = OrganizeMode(hook.options.get("mode", "hardlink"))
    merge_small = hook.options.get("merge_small", 3)
    exclude_genres = hook.options.get("exclude_genres") or None
    system_map: dict[str, str] = hook.options.get("system_map") or {}
    metadata_db = ctx.metadata_db

    if not metadata_db.exists():
        logger.warning(f"  ⚠ Metadata DB not found: {metadata_db} — skipping genre organization")
        return

    # Determine which platforms to process
    platforms = hook.options.get("platforms") or list(ctx.platforms)
    if not platforms:
        logger.info("  No completed platforms to genre-organize")
        return

    logger.info(f"  Genre organizing {len(platforms)} platform(s) (mode: {mode.value})")

    total_organized = 0
    total_skipped = 0

    for platform in platforms:
        platform_dir = ctx.output_base / platform
        if not platform_dir.exists():
            logger.debug(f"  Skipping {platform} (no output dir)")
            continue

        system = system_map.get(platform, platform)

        try:
            organizer = GenreOrganizer(
                metadata_db=metadata_db,
                system=system,
                mode=mode,
                merge_small=merge_small,
                exclude_genres=list(exclude_genres) if exclude_genres else None,
            )
            stats = organizer.organize(platform_dir)
            organized = stats.files_moved + stats.files_copied + stats.symlinks_created
            total_organized += organized
            total_skipped += stats.skipped
            if organized > 0 or stats.errors > 0:
                logger.info(
                    f"    {platform}: {organized} organized, "
                    f"{stats.skipped} skipped"
                    + (f", {stats.errors} errors" if stats.errors else "")
                )
            else:
                logger.debug(f"    {platform}: no genre data in DB")
        except Exception as e:
            logger.warning(f"    {platform}: genre organize failed — {e}")

    logger.info(
        f"  ✅ Genre organization complete: {total_organized} hardlinks created across {len(platforms)} platforms"
    )


def _quarantine_unpolished(hook: Any, ctx: HookContext) -> None:
    """
    Move unpolished root-level games into a quarantine subfolder (default: Other/).

    A game is "unpolished" if it is missing a required metadata field in the
    root gamelist.xml entry.  Unpolished games are:
      - hardlinked into <folder_name>/ (zero disk cost)
      - hidden in the root gamelist via <hidden>true</hidden>
    patch_gamelist then backfills a visible entry for the subdir copy.

    Files already in any subdir (By Genre/, Best Games/, Translations/, etc.)
    are never touched.

    Hook options (all optional):
        folder_name:   destination subdir name (default: Other)
        require_image: hide if <image> is absent (default: true)
        require_desc:  hide if <desc> is absent  (default: true)
        platforms:     list of platforms to process (default: all completed)
    """
    import os
    from xml.etree import ElementTree as ET

    folder_name = hook.options.get("folder_name", "Other")
    require_image = hook.options.get("require_image", True)
    require_desc = hook.options.get("require_desc", True)

    platforms = hook.options.get("platforms") or list(ctx.platforms)
    if not platforms:
        logger.info("  No completed platforms to process")
        return

    logger.info(
        f"  Quarantining unpolished games for {len(platforms)} platform(s) "
        f"→ {folder_name}/  (require_image={require_image}, require_desc={require_desc})"
    )
    total_quarantined = 0

    for platform in platforms:
        platform_dir = ctx.output_base / platform
        gamelist_path = platform_dir / "gamelist.xml"
        if not gamelist_path.exists():
            continue

        tree = ET.parse(gamelist_path)
        xml_root = tree.getroot()
        quarantine_dir = platform_dir / folder_name
        quarantined = 0

        for game in xml_root.findall("game"):
            path_text = game.findtext("path") or ""
            rel = path_text.lstrip("./")
            # Root-level entries only — skip anything already in a subdir
            if "/" in rel:
                continue
            # Skip already-hidden entries
            if game.findtext("hidden") == "true":
                continue

            missing_image = require_image and not (game.findtext("image") or "").strip()
            missing_desc = require_desc and not (game.findtext("desc") or "").strip()
            if not missing_image and not missing_desc:
                continue  # polished — leave in root

            rom_path = platform_dir / rel
            if not rom_path.exists():
                continue

            # Hardlink into quarantine subdir
            quarantine_dir.mkdir(parents=True, exist_ok=True)
            dest = quarantine_dir / rom_path.name
            if not dest.exists():
                try:
                    os.link(rom_path, dest)
                except OSError:
                    import shutil

                    shutil.copy2(rom_path, dest)

            # Hide the root gamelist entry
            hidden_elem = game.find("hidden")
            if hidden_elem is None:
                hidden_elem = ET.SubElement(game, "hidden")
            hidden_elem.text = "true"
            quarantined += 1

        if quarantined > 0:
            ET.indent(tree, space="  ")
            tree.write(gamelist_path, encoding="utf-8", xml_declaration=True)
            logger.info(f"    {platform}: {quarantined} games → {folder_name}/")
        total_quarantined += quarantined

    logger.info(
        f"  ✅ Quarantine complete: {total_quarantined} games moved to {folder_name}/"
        f" across {len(platforms)} platforms"
    )


def _patch_gamelist(hook: Any, ctx: HookContext) -> None:
    """
    Patch gamelist.xml files to include subdirectory entries.

    GenerateMetadataStage only writes root-level entries. After
    GenreOrganizer creates By Genre/ hardlinks (and ApplyListsStage
    creates Best Games/ etc.), those files have no gamelist coverage.
    This hook clones each root entry for every matching file found in
    any subdirectory, so EmulationStation can browse by folder.

    Hook options (all optional):
        platforms: list of platforms to process (default: all completed)
    """
    import importlib.util

    script_path = ctx.workspace_root / "scripts" / "patch_gamelist_subdirs.py"
    if not script_path.exists():
        logger.warning(f"  ⚠ patch_gamelist_subdirs.py not found at {script_path}")
        return

    spec = importlib.util.spec_from_file_location("patch_gamelist_subdirs", script_path)
    if spec is None or spec.loader is None:
        logger.warning("  ⚠ cannot load %s", script_path)
        return
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    platforms = hook.options.get("platforms") or list(ctx.platforms)
    if not platforms:
        logger.info("  No completed platforms to patch")
        return

    logger.info(f"  Patching gamelist subdirs for {len(platforms)} platform(s)")
    total_added = 0

    for platform in platforms:
        platform_dir = ctx.output_base / platform
        if not platform_dir.exists():
            logger.debug(f"  Skipping {platform} (no output dir)")
            continue

        stats = mod.patch_platform(platform_dir)
        added = stats.get("added", 0)
        status = stats.get("status", "?")
        total_added += added

        if added > 0:
            logger.info(f"    {platform}: +{added} gamelist entries added")
        elif status not in ("ok", "skipped (folder format)"):
            logger.debug(f"    {platform}: [{status}]")

    logger.info(
        f"  ✅ Gamelist patch complete: {total_added} entries added"
        f" across {len(platforms)} platforms"
    )


# ---------------------------------------------------------------------------
# Registry + driver entry points
# ---------------------------------------------------------------------------

HOOKS: dict[str, PostBuildHook] = {
    "command": CommandHook(),
    "jdupes": JdupesHook(),
    "genre_organize": NativeHook("genre_organize", _genre_organize),
    "quarantine_unpolished": NativeHook("quarantine_unpolished", _quarantine_unpolished),
    "patch_gamelist": NativeHook("patch_gamelist", _patch_gamelist),
}


def run_post_build_hooks(hooks: Sequence[Any], ctx: HookContext) -> list[tuple[str, HookResult]]:
    """Run every configured hook through the registry; unknown kinds are errors, not shells."""
    results: list[tuple[str, HookResult]] = []
    for i, hook in enumerate(hooks, 1):
        kind = str(getattr(hook, "type", "command"))
        name = str(getattr(hook, "name", kind))
        logger.info("  [%d/%d] Hook: %s (type: %s)", i, len(hooks), name, kind)
        impl = HOOKS.get(kind)
        if impl is None:
            res = HookResult(False, f"unknown hook type {kind!r} (known: {sorted(HOOKS)})")
        else:
            try:
                res = impl.run(hook, ctx)
            except Exception as exc:  # a hook must not abort the build report
                logger.error("    ❌ %s error: %s", name, exc, exc_info=True)
                res = HookResult(False, str(exc))
        logger.info("    %s %s", "✅" if res.ok else "❌", res.summary or "")
        results.append((name, res))
    return results


class Deployer(Protocol):
    method: str

    def run(
        self, output_base: Path, destination: str, options: Mapping[str, Any]
    ) -> HookResult: ...


class RsyncDeploy:
    """``method: rsync`` — argv built from options; ``rsync_flags`` is shlex-split."""

    method = "rsync"

    def argv(self, output_base: Path, destination: str, options: Mapping[str, Any]) -> list[str]:
        flags = shlex.split(str(options.get("rsync_flags", "-avH --progress")))
        argv = ["rsync", *flags]
        if options.get("delete_extra", False):
            argv.append("--delete")
        if options.get("dry_run", False):
            argv.append("--dry-run")
        argv += [f"{output_base}/", destination]
        return argv

    def run(self, output_base: Path, destination: str, options: Mapping[str, Any]) -> HookResult:
        return _run_argv(self.argv(output_base, destination, options))


DEPLOYERS: dict[str, Deployer] = {"rsync": RsyncDeploy()}


def run_deployment(deploy: Any, output_base: Path) -> HookResult | None:
    """Deploy ``output_base`` per the build spec's ``deploy`` block; ``None`` if gated by ``confirm``."""
    method = str(getattr(deploy, "method", "rsync"))
    destination = str(getattr(deploy, "destination", ""))
    options: Mapping[str, Any] = getattr(deploy, "options", None) or {}
    impl = DEPLOYERS.get(method)
    if impl is None:
        return HookResult(False, f"unknown deploy method {method!r} (known: {sorted(DEPLOYERS)})")
    logger.info("  Method: %s", method)
    logger.info("  Destination: %s", destination)
    if options.get("confirm", True):
        logger.info("  (Requires --deploy flag to execute)")
        return None
    return impl.run(output_base, destination, options)
