#!/usr/bin/env bash
# count-lines.sh — Count lines of our own code in rom-farmer
# Covers: Python source, tests, scripts, tools, config YAML, shell scripts, Makefile
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
WHITE='\033[1;37m'
DIM='\033[2m'
RESET='\033[0m'

printf "\n${WHITE}═══════════════════════════════════════════════════════════════${RESET}\n"
printf "${WHITE}  rom-farmer — Lines of Code Report${RESET}\n"
printf "${WHITE}═══════════════════════════════════════════════════════════════${RESET}\n\n"

# Helper: count lines in a set of files, report per-file breakdown
# Args: label, find_args...
count_section() {
    local label="$1"; shift
    local files
    files=$(eval "$@" 2>/dev/null || true)

    if [[ -z "$files" ]]; then
        printf "  ${DIM}%-40s %6s lines  (%s files)${RESET}\n" "$label" "0" "0"
        echo "0"
        return
    fi

    local file_count line_count
    file_count=$(echo "$files" | wc -l)
    line_count=$(echo "$files" | xargs cat 2>/dev/null | wc -l)

    printf "  ${CYAN}%-40s${RESET} ${GREEN}%6d${RESET} lines  (${DIM}%d files${RESET})\n" "$label" "$line_count" "$file_count"
    echo "$line_count"
}

# We capture totals via a temp file since subshells lose variables
totals_file=$(mktemp)
echo 0 > "$totals_file"

add_total() {
    local current
    current=$(cat "$totals_file")
    echo $(( current + $1 )) > "$totals_file"
}

# ──────────────────────────────────────────────────────────
# Python source (src/romfarmer/**)
# ──────────────────────────────────────────────────────────
printf "${YELLOW}Python Source (src/romfarmer/)${RESET}\n"

n=$(count_section "All .py files" \
    "find src/romfarmer -name '*.py' -not -path '*__pycache__*' -not -path '*.egg-info*'" | tail -1)
add_total "$n"

echo ""

# Breakdown by subdirectory
printf "  ${DIM}Breakdown by package:${RESET}\n"
for dir in src/romfarmer/*/; do
    [[ "$(basename "$dir")" == "__pycache__" ]] && continue
    [[ "$(basename "$dir")" == "*.egg-info" ]] && continue
    pkg=$(basename "$dir")
    files=$(find "$dir" -name '*.py' -not -path '*__pycache__*' 2>/dev/null || true)
    if [[ -n "$files" ]]; then
        fc=$(echo "$files" | wc -l)
        lc=$(echo "$files" | xargs cat 2>/dev/null | wc -l)
        printf "    ${DIM}%-38s %6d lines  (%d files)${RESET}\n" "$pkg/" "$lc" "$fc"
    fi
done

# Top-level .py files in src/romfarmer/
top_py=$(find src/romfarmer -maxdepth 1 -name '*.py' -not -path '*__pycache__*' 2>/dev/null || true)
if [[ -n "$top_py" ]]; then
    fc=$(echo "$top_py" | wc -l)
    lc=$(echo "$top_py" | xargs cat 2>/dev/null | wc -l)
    printf "    ${DIM}%-38s %6d lines  (%d files)${RESET}\n" "(top-level modules)" "$lc" "$fc"
fi

echo ""

# ──────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────
printf "${YELLOW}Tests (tests/)${RESET}\n"
n=$(count_section "Test files (.py)" \
    "find tests -name '*.py' -not -path '*__pycache__*'" | tail -1)
add_total "$n"
echo ""

# ──────────────────────────────────────────────────────────
# Scripts
# ──────────────────────────────────────────────────────────
printf "${YELLOW}Scripts (scripts/)${RESET}\n"
n=$(count_section "Python scripts" \
    "find scripts -name '*.py' -not -path '*__pycache__*'" | tail -1)
add_total "$n"
n=$(count_section "Shell scripts" \
    "find scripts -name '*.sh'" | tail -1)
add_total "$n"
echo ""

# ──────────────────────────────────────────────────────────
# Tools (our own .py/.sh in tools/, not vendored binaries)
# ──────────────────────────────────────────────────────────
printf "${YELLOW}Tools (tools/ — our scripts only)${RESET}\n"
n=$(count_section "Python tools" \
    "find tools -maxdepth 2 -name '*.py' -not -path '*__pycache__*'" | tail -1)
add_total "$n"
n=$(count_section "Shell tools" \
    "find tools -maxdepth 1 -name '*.sh'" | tail -1)
add_total "$n"
echo ""

# ──────────────────────────────────────────────────────────
# CLI entry points / top-level scripts
# ──────────────────────────────────────────────────────────
printf "${YELLOW}CLI & Top-level${RESET}\n"

cli_files=""
for f in build-wizard romgroomer show-status.py; do
    [[ -f "$f" ]] && cli_files="$cli_files $f"
done
if [[ -n "$cli_files" ]]; then
    fc=$(echo $cli_files | wc -w)
    lc=$(cat $cli_files 2>/dev/null | wc -l)
    printf "  ${CYAN}%-40s${RESET} ${GREEN}%6d${RESET} lines  (${DIM}%d files${RESET})\n" "Entry points" "$lc" "$fc"
    add_total "$lc"
fi

# Makefile
if [[ -f Makefile ]]; then
    lc=$(wc -l < Makefile)
    printf "  ${CYAN}%-40s${RESET} ${GREEN}%6d${RESET} lines\n" "Makefile" "$lc"
    add_total "$lc"
fi
echo ""

# ──────────────────────────────────────────────────────────
# Configuration (YAML configs we wrote)
# ──────────────────────────────────────────────────────────
printf "${YELLOW}Configuration (config/)${RESET}\n"
n=$(count_section "YAML config files" \
    "find config -name '*.yaml' -o -name '*.yml' -o -name '*.json'" | tail -1)
add_total "$n"
echo ""

# ──────────────────────────────────────────────────────────
# Documentation (markdown)
# ──────────────────────────────────────────────────────────
printf "${YELLOW}Documentation (top-level & docs/)${RESET}\n"
n=$(count_section "Markdown docs (top-level)" \
    "find . -maxdepth 1 -name '*.md'" | tail -1)
add_total "$n"
if [[ -d docs ]]; then
    n=$(count_section "Markdown docs (docs/)" \
        "find docs -name '*.md'" | tail -1)
    add_total "$n"
fi
echo ""

# ──────────────────────────────────────────────────────────
# pyproject.toml
# ──────────────────────────────────────────────────────────
if [[ -f pyproject.toml ]]; then
    lc=$(wc -l < pyproject.toml)
    printf "  ${CYAN}%-40s${RESET} ${GREEN}%6d${RESET} lines\n" "pyproject.toml" "$lc"
    add_total "$lc"
fi

# ──────────────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────────────
grand_total=$(cat "$totals_file")
rm -f "$totals_file"

# Code-only total (no docs/config)
code_py=$(find src/romfarmer -name '*.py' -not -path '*__pycache__*' -not -path '*.egg-info*' | xargs cat 2>/dev/null | wc -l)
test_py=$(find tests -name '*.py' -not -path '*__pycache__*' | xargs cat 2>/dev/null | wc -l)
script_py=$(find scripts -name '*.py' -not -path '*__pycache__*' | xargs cat 2>/dev/null | wc -l)
script_sh=$(find scripts -name '*.sh' | xargs cat 2>/dev/null | wc -l)
tools_py=$(find tools -maxdepth 2 -name '*.py' -not -path '*__pycache__*' | xargs cat 2>/dev/null | wc -l)
tools_sh=$(find tools -maxdepth 1 -name '*.sh' | xargs cat 2>/dev/null | wc -l)

cli_lc=0
for f in build-wizard romgroomer show-status.py; do
    [[ -f "$f" ]] && cli_lc=$(( cli_lc + $(wc -l < "$f") ))
done

code_total=$(( code_py + test_py + script_py + script_sh + tools_py + tools_sh + cli_lc ))

# Non-blank, non-comment lines for Python
sloc=$(find src/romfarmer tests scripts -name '*.py' -not -path '*__pycache__*' -not -path '*.egg-info*' \
    | xargs grep -v '^\s*$' 2>/dev/null \
    | grep -v '^\s*#' \
    | wc -l)

printf "\n${WHITE}═══════════════════════════════════════════════════════════════${RESET}\n"
printf "${WHITE}  SUMMARY${RESET}\n"
printf "${WHITE}═══════════════════════════════════════════════════════════════${RESET}\n"
printf "  ${GREEN}%-40s %6d${RESET}\n" "Total (code + tests + scripts)" "$code_total"
printf "  ${GREEN}%-40s %6d${RESET}\n" "  └─ Core source (src/)" "$code_py"
printf "  ${GREEN}%-40s %6d${RESET}\n" "  └─ Tests" "$test_py"
printf "  ${GREEN}%-40s %6d${RESET}\n" "  └─ Scripts & tools" "$(( script_py + script_sh + tools_py + tools_sh ))"
printf "  ${GREEN}%-40s %6d${RESET}\n" "  └─ CLI entry points" "$cli_lc"
printf "  ${DIM}%-40s %6d${RESET}\n" "Python SLOC (non-blank, non-comment)" "$sloc"
printf "  ${DIM}%-40s %6d${RESET}\n" "Grand total (incl. config, docs, etc.)" "$grand_total"
printf "${WHITE}═══════════════════════════════════════════════════════════════${RESET}\n\n"
