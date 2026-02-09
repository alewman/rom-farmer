# Build Wizard - Interactive Quick Start

## 🚀 One Command to Rule Them All

```bash
./build-wizard
```

The interactive wizard guides you through building perfect ROM collections with beautiful menus and zero guesswork!

---

## 🎯 What It Does

### Auto-Discovery
Scans your configuration and shows:
- ✅ All available platforms (15 found)
- ✅ All selection strategies (4 found)
- ✅ All existing builds (11 found)

### Guided Flow
Asks you exactly what you need:
1. Create new or use existing build?
2. Which platform? (Saturn, PS3, PSX, etc.)
3. How many games? (10 for testing, 40GB for production, etc.)
4. Confirm and run!

### Smart Validation
- Checks configs before running
- Shows you the exact command it will execute
- Confirms before starting the build

---

## 📋 Example Session

```bash
$ ./build-wizard

╭─────────────────────────────────────────────────╮
│ 🎮 ROM Farmer Quick Build                      │
│ Interactive wizard for building ROM collections │
╰─────────────────────────────────────────────────╯

Discovering available configurations...
  ✓ Found 15 platforms
  ✓ Found 4 selections
  ✓ Found 11 existing builds

Step 1: Build Configuration
Would you like to use an existing build or create a new one?
  1. Create new build (guided)
  2. Use existing build

Choice [1/2] (1): 1

Step 2: Select Platform
               Available Platforms               
┏━━━━━┳━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━┓
┃ #   ┃ Platform    ┃ Games ┃ Description ┃
┡━━━━━╇━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━┩
│ 1   │ saturn      │   318 │ Sega Saturn │
│ 2   │ psx         │  1798 │ PlayStation │
│ 3   │ ps3         │   800 │ PS3         │
│ 4   │ virtualboy  │    30 │ Virtual Boy │
└─────┴─────────────┴───────┴─────────────┘

Select platform (1-15) (1): 1
✓ Selected: saturn

Step 3: Select Strategy
How many games do you want to process?
                    Available Selection Strategies                    
┏━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ #   ┃ Name               ┃ Strategy      ┃ Limit      ┃ Description ┃
┡━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ 1   │ usa-10             │ first         │ 10         │ First 10... │
│ 2   │ rating-budget-40gb │ rating_budget │ — (40.0GB) │ Top-rated...│
│ 3   │ smallest-5         │ smallest      │ 5          │ 5 smallest..│
│ 4   │ multi-disc-20      │ first         │ 20         │ 20 multi-...│
└─────┴────────────────────┴───────────────┴────────────┴─────────────┘

Select strategy (1-4 (or 0 for none)) (1): 1
✓ Selected: usa-10

╭───────── Review ─────────╮
│ Build Summary            │
│                          │
│ Platform:  saturn        │
│ Selection: usa-10        │
│ Games:     318 available │
╰──────────────────────────╯

Proceed with build? [y/n] (y): y

╭──────────────────── Executing ────────────────────╮
│ python3 -m romfarmer build run saturn-usa10-test │
╰───────────────────────────────────────────────────╯

[Starting build...]
```

---

## 🎮 Quick Test (Recommended First Run)

```bash
./build-wizard
# Select: saturn (option 1)
# Select: usa-10 (option 1)
# Confirm: y

# Result: 10 USA Saturn games in ~5 minutes
```

This validates:
- ✅ Your source ROMs are accessible
- ✅ DAT files are working
- ✅ Extraction pipeline functions
- ✅ CHD compression works
- ✅ Output organization is correct

---

## 📊 Selection Strategies Explained

### Testing Strategies (Fast)

**usa-10** - `10 games in ~5 minutes`
```yaml
strategy: first
limit: 10
pattern: "*USA*"
```
Perfect for: Initial testing, validating pipeline

**smallest-5** - `5 games in ~2 minutes`
```yaml
strategy: smallest
limit: 5
```
Perfect for: Fast iteration, PS3 testing (large files)

**multi-disc-20** - `20 games in ~10 minutes`
```yaml
strategy: first  
limit: 20
pattern: "*Disc*"
```
Perfect for: Testing M3U generation, PSX multi-disc games

### Production Strategies (Curated)

**rating-budget-40gb** - `Top quality within 40GB`
```yaml
strategy: rating_budget
max_size_gb: 40.0
min_rating: 0.0
```
Perfect for: Storage-limited devices, best games only

---

## 🔧 Advanced Usage

### Skip Interactive Mode
```bash
python3 -m romfarmer quick --platform saturn --selection usa-10
```

### Run Specific Build
```bash
python3 -m romfarmer build run saturn-usa10-test
```

### See Available Options
```bash
ls config/platforms/   # All platforms
ls config/selections/  # All strategies  
ls config/builds/      # All builds
```

---

## 📂 File Locations

```
rom-farmer/
├── build-wizard          ← Run this!
├── logs/                 ← Build logs here
│   └── romfarmer_*.log
├── config/
│   ├── platforms/        ← Platform configs
│   ├── selections/       ← Selection strategies
│   └── builds/           ← Build definitions
└── src/                  ← Source code
```

**Source ROMs:**
```
/data/emu/roms/<platform>/
```

**Output Collections:**
```
/data/emu/output/<target>/<platform>/
```

**Temp Processing:**
```
/data/emu/temp/<platform>/
```

---

## 🔍 Monitoring Progress

### Watch Logs Live
```bash
tail -f logs/romfarmer_*.log
```

### Check for Errors
```bash
grep -i error logs/romfarmer_*.log | tail -20
```

### See Current Processing
```bash
ls -lh /data/emu/temp/saturn/
```

---

## 💡 Pro Tips

### 1. Always Test First
Run small selections (usa-10, smallest-5) before big builds

### 2. Keep Logs Terminal Open
```bash
tail -f logs/*.log
```

### 3. Check Disk Space
```bash
df -h /data/emu/temp
df -h /data/emu/output
```

### 4. Reuse Successful Configs
Share your `config/builds/*.yaml` files

### 5. Create Custom Selections
Add YAML to `config/selections/` for your needs

---

## 🆘 Troubleshooting

### "No platforms found"
Check: `ls config/platforms/*.yaml`

### "No selections found"
Check: `ls config/selections/*.yaml`

### "Build validation failed"
Run with validation only:
```bash
python3 -m romfarmer build run <name> --validate-only
```

### "Permission denied"
Make executable:
```bash
chmod +x build-wizard
```

---

## 🎯 What You Get

### Example: Saturn usa-10 Build

**Input:**
- 2,393 ZIP files in `/data/emu/roms/saturn/`

**Processing:**
1. DAT filter: 318 matched games
2. Selection filter: 10 USA games
3. Extract BIN/CUE from ZIPs
4. Convert to CHD format (best compression)
5. Generate M3U for multi-disc games
6. Organize for target device

**Output:**
```
/data/emu/output/test/saturn/
├── Game 1 (USA).chd
├── Game 2 (USA) (Disc 1).chd
├── Game 2 (USA) (Disc 2).chd
├── Game 2 (USA).m3u
└── ... (10 games total)
```

Ready to copy to your device and play! 🎮

---

## 🚀 Next Steps

1. ✅ Run `./build-wizard`
2. ✅ Select Saturn + usa-10
3. ✅ Watch it complete successfully
4. ✅ Examine output in `/data/emu/output/`
5. ✅ Try other platforms!
6. ✅ Create custom selections for your needs

---

## 🌟 Why This Is Amazing

### Before (Manual Process):
1. Download DAT files
2. Manually match ROMs
3. Extract archives
4. Convert formats
5. Organize files
6. Repeat for each platform
7. **Time: Hours per platform**

### After (Build Wizard):
1. Run `./build-wizard`
2. Select options from menus
3. Confirm
4. **Time: One click**

**The wizard does everything automatically! 🎉**

---

**Built with ❤️ for the ROM preservation community**

*"One command to build them all!"*
