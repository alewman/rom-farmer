#!/bin/bash
#
# Bulk import all gamelist.xml files from roms-batocera directory
#

ROM_DIR="/data/emu/share/roms-batocera"
LOG_FILE="/data/emu/rom-groomer-python/import_all_systems.log"
SUMMARY_FILE="/data/emu/rom-groomer-python/import_summary.txt"

echo "=== ROM Groomer Bulk Import ===" | tee "$SUMMARY_FILE"
echo "Started: $(date)" | tee -a "$SUMMARY_FILE"
echo "" | tee -a "$SUMMARY_FILE"

# Find all gamelist.xml files
GAMELISTS=$(find "$ROM_DIR" -maxdepth 2 -name "gamelist.xml" | sort)
TOTAL=$(echo "$GAMELISTS" | wc -l)

echo "Found $TOTAL gamelist.xml files" | tee -a "$SUMMARY_FILE"
echo "" | tee -a "$SUMMARY_FILE"

# Initialize counters
SUCCESS=0
FAILED=0
SKIPPED=0

# Process each gamelist
COUNT=0
for GAMELIST in $GAMELISTS; do
    COUNT=$((COUNT + 1))
    SYSTEM=$(basename "$(dirname "$GAMELIST")")
    
    echo "[$COUNT/$TOTAL] Processing: $SYSTEM" | tee -a "$SUMMARY_FILE"
    
    # Skip if gamelist is too small (probably empty)
    SIZE=$(stat -c%s "$GAMELIST" 2>/dev/null || stat -f%z "$GAMELIST" 2>/dev/null)
    if [ "$SIZE" -lt 200 ]; then
        echo "  ⚠ Skipped (file too small)" | tee -a "$SUMMARY_FILE"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi
    
    # Import (ignore exit code - check log output instead)
    ~/.local/bin/romgroomer metadata import-arrm "$GAMELIST" >> "$LOG_FILE" 2>&1 || true
    
    # Check if import actually completed by looking at log
    if tail -20 "$LOG_FILE" | grep -q "Import completed successfully\|✓ Import completed"; then
        echo "  ✓ Success" | tee -a "$SUMMARY_FILE"
        SUCCESS=$((SUCCESS + 1))
    elif tail -20 "$LOG_FILE" | grep -q "Import completed with.*errors"; then
        echo "  ✓ Success (with warnings)" | tee -a "$SUMMARY_FILE"
        SUCCESS=$((SUCCESS + 1))
    else
        echo "  ✗ Failed (see log)" | tee -a "$SUMMARY_FILE"
        FAILED=$((FAILED + 1))
    fi
    
    echo "" | tee -a "$SUMMARY_FILE"
done

# Summary
echo "=== Import Complete ===" | tee -a "$SUMMARY_FILE"
echo "Finished: $(date)" | tee -a "$SUMMARY_FILE"
echo "" | tee -a "$SUMMARY_FILE"
echo "Results:" | tee -a "$SUMMARY_FILE"
echo "  Success: $SUCCESS" | tee -a "$SUMMARY_FILE"
echo "  Failed:  $FAILED" | tee -a "$SUMMARY_FILE"
echo "  Skipped: $SKIPPED" | tee -a "$SUMMARY_FILE"
echo "  Total:   $TOTAL" | tee -a "$SUMMARY_FILE"
echo "" | tee -a "$SUMMARY_FILE"

# Show database stats
echo "=== Database Statistics ===" | tee -a "$SUMMARY_FILE"
~/.local/bin/romgroomer metadata info | tee -a "$SUMMARY_FILE"

echo ""
echo "Full log: $LOG_FILE"
echo "Summary:  $SUMMARY_FILE"
