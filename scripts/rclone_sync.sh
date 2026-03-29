#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
    echo "Usage: $0 <URL> <LOCAL_BASE_DIR> [INCLUDE_PATTERN]"
    exit 1
fi

# Define variables
REMOTE_URL="$1"
LOCAL_BASE_DIR="$2"
INCLUDE_PATTERN="$3"

# Extract the hostname and path from the URL
HOSTNAME=$(echo "$REMOTE_URL" | awk -F/ '{print $3}')
PATH=$(echo "$REMOTE_URL" | awk -F/ '{for (i=4; i<=NF; i++) printf "%s/", $i}')

# Construct the local directory path
LOCAL_DIR="$LOCAL_BASE_DIR/$HOSTNAME/$PATH"

# Ensure the local directory exists
/usr/bin/mkdir -p "$LOCAL_DIR"

# Configure the HTTP remote
REMOTE_NAME="myhttpremote"
/usr/bin/rclone config create "$REMOTE_NAME" http url "$REMOTE_URL"

# Sync files from the remote to the local directory, optionally including only files that match the pattern
if [ -n "$INCLUDE_PATTERN" ]; then
    /usr/bin/rclone sync "$REMOTE_NAME:" "$LOCAL_DIR" --include "$INCLUDE_PATTERN"
else
    /usr/bin/rclone sync "$REMOTE_NAME:" "$LOCAL_DIR"
fi
