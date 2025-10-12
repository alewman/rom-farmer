#!/bin/bash
set -e

# Clone or update MAME source from GitHub
# This includes chdman and all other MAME tools

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAME_DIR="$SCRIPT_DIR/src"
MAME_REPO="https://github.com/mamedev/mame.git"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    MAME Source Management                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

if [ -d "$MAME_DIR" ]; then
    echo "📂 MAME source directory exists: $MAME_DIR"
    echo ""
    
    cd "$MAME_DIR"
    
    # Check if it's a git repo
    if [ -d .git ]; then
        echo "🔄 Updating existing MAME repository..."
        
        # Show current status
        CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
        CURRENT_COMMIT=$(git rev-parse --short HEAD)
        echo "   Current branch: $CURRENT_BRANCH"
        echo "   Current commit: $CURRENT_COMMIT"
        
        # Fetch updates
        echo ""
        echo "🌐 Fetching latest changes from GitHub..."
        git fetch --tags
        
        # Show available tags (recent releases)
        echo ""
        echo "📋 Recent MAME releases:"
        git tag --sort=-version:refname | head -10
        
        echo ""
        read -p "🤔 Update to latest commit? (y/N) " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "⬆️  Pulling latest changes..."
            git pull
            NEW_COMMIT=$(git rev-parse --short HEAD)
            echo "✅ Updated to commit: $NEW_COMMIT"
        else
            echo "ℹ️  Keeping current version"
        fi
        
        # Optionally checkout a specific tag
        echo ""
        read -p "🏷️  Checkout a specific release tag? (leave empty to skip) " TAG
        
        if [ -n "$TAG" ]; then
            echo "🔀 Checking out tag: $TAG"
            git checkout "$TAG"
            echo "✅ Now on tag: $TAG"
        fi
        
    else
        echo "⚠️  Directory exists but is not a git repository!"
        echo "   Please remove $MAME_DIR and run this script again."
        exit 1
    fi
else
    echo "📥 Cloning MAME repository from GitHub..."
    echo "   Repository: $MAME_REPO"
    echo "   Target: $MAME_DIR"
    echo ""
    echo "⚠️  This is a large repository (~1.5GB), this will take a while..."
    echo ""
    
    # Option for shallow clone to save space/time
    read -p "🤔 Do shallow clone (faster, smaller, but no history)? (Y/n) " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo "⚡ Performing shallow clone (depth=1)..."
        git clone --depth 1 "$MAME_REPO" "$MAME_DIR"
    else
        echo "📚 Performing full clone (includes complete history)..."
        git clone "$MAME_REPO" "$MAME_DIR"
    fi
    
    cd "$MAME_DIR"
    
    echo ""
    echo "✅ Clone completed successfully!"
    
    # Show available tags
    echo ""
    echo "📋 Recent MAME releases:"
    git tag --sort=-version:refname | head -10
fi

# Record version information
VERSION_FILE="$SCRIPT_DIR/VERSION.txt"
cd "$MAME_DIR"

COMMIT=$(git rev-parse HEAD)
SHORT_COMMIT=$(git rev-parse --short HEAD)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
DATE=$(git log -1 --format=%cd --date=short)
TAG=$(git describe --tags --exact-match 2>/dev/null || echo "no tag")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Current MAME Source Version"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cat > "$VERSION_FILE" << EOF
MAME Source Version Information
Generated: $(date)

Commit:       $COMMIT
Short:        $SHORT_COMMIT
Branch:       $BRANCH
Tag:          $TAG
Date:         $DATE
Repository:   $MAME_REPO
EOF

cat "$VERSION_FILE"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ MAME source is ready!"
echo ""
echo "Next steps:"
echo "  1. Run ./build.sh to build chdman"
echo "  2. Built binary will be in: $SCRIPT_DIR/build/chdman"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
