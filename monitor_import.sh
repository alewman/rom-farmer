#!/bin/bash
# Safe monitoring script - check import progress without interfering

echo "=== Import Progress Monitor ==="
echo ""

# Check if import is running
if ps aux | grep -q "[i]mport_all_systems"; then
    echo "✓ Import is RUNNING"
    echo ""
    
    # Show current activity
    CURRENT_IMPORT=$(ps aux | grep "[r]omgroomer metadata import" | awk '{print $NF}' | xargs basename | sed 's/gamelist.xml//')
    if [ -n "$CURRENT_IMPORT" ]; then
        echo "Currently importing: $CURRENT_IMPORT"
    fi
    echo ""
else
    echo "✗ Import is NOT running"
    echo ""
fi

# Show latest summary
echo "--- Latest Summary (last 15 lines) ---"
tail -15 /data/emu/rom-groomer-python/import_summary.txt 2>/dev/null || echo "No summary yet"

echo ""
echo "--- Database Stats ---"
~/.local/bin/romgroomer metadata info 2>/dev/null | grep -E "Total Games|Total Media|Deduplication" || echo "Database not accessible"

echo ""
echo "To watch live progress:"
echo "  watch -n 5 ./monitor_import.sh"
