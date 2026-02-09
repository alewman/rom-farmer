#!/usr/bin/env python3
"""
ROM Farmer Project Report Generator

Generates a self-contained HTML report showcasing ROM Farmer's capabilities.
Mermaid diagrams are rendered to PNG and embedded as base64 for portability.
"""

import base64
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path("/data/emu/rom-farmer/docs")
OUTPUT_DIR.mkdir(exist_ok=True)


def render_mermaid_to_base64(mermaid_code: str, width: int = 800) -> str:
    """Render Mermaid diagram to base64-encoded PNG using Playwright."""
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <style>
            body {{ margin: 0; padding: 20px; background: white; }}
            .mermaid {{ font-family: 'Segoe UI', Arial, sans-serif; }}
        </style>
    </head>
    <body>
        <div class="mermaid">
{mermaid_code}
        </div>
        <script>
            mermaid.initialize({{ 
                startOnLoad: true, 
                theme: 'default',
                flowchart: {{ curve: 'basis' }},
                securityLevel: 'loose'
            }});
        </script>
    </body>
    </html>
    """
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 600})
        page.set_content(html_template)
        page.wait_for_timeout(2000)  # Wait for Mermaid to render
        
        # Get the mermaid element and screenshot it
        element = page.query_selector(".mermaid")
        if element:
            png_bytes = element.screenshot()
        else:
            png_bytes = page.screenshot()
        
        browser.close()
    
    return base64.b64encode(png_bytes).decode('utf-8')


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT CONTENT
# ═══════════════════════════════════════════════════════════════════════════════

MERMAID_ARCHITECTURE = """
flowchart TB
    subgraph Sources["📦 Source Management"]
        M[Myrient Archive]
        I[Internet Archive]
        R[Redump DATs]
        N[No-Intro DATs]
    end
    
    subgraph Pipeline["⚙️ ROM Farmer Pipeline"]
        DAT[DAT Validation]
        FILTER[1G1R Filtering]
        LISTS[Best-Of Lists]
        EXTRACT[Smart Extraction]
        COMPRESS[Optimal Compression]
        META[Metadata + Media]
        ORG[Organization]
    end
    
    subgraph Targets["🎮 Target Devices"]
        BAT[Batocera/EmuELEC]
        ROCK[ROCKNIX]
        FLASH[Flash Carts]
        STEAM[Steam Deck]
    end
    
    M --> DAT
    I --> DAT
    R --> DAT
    N --> DAT
    
    DAT --> FILTER --> LISTS --> EXTRACT --> COMPRESS --> META --> ORG
    
    ORG --> BAT
    ORG --> ROCK
    ORG --> FLASH
    ORG --> STEAM
"""

MERMAID_PIPELINE = """
flowchart LR
    subgraph Stage1["Stage 1"]
        S1[📋 DAT Filter]
        S1D["Validate ROMs against\nNo-Intro/Redump DATs\nMD5 hash verification"]
    end
    
    subgraph Stage2["Stage 2"]
        S2[🌍 1G1R Filter]
        S2D["One Game One ROM\nEnglish priority\nRetool processed"]
    end
    
    subgraph Stage3["Stage 3"]
        S3[⭐ Best-Of Lists]
        S3D["Curated game lists\nPer-platform selection\n54+ lists included"]
    end
    
    subgraph Stage4["Stage 4"]
        S4[📤 Extract]
        S4D["Smart extraction\nCartridge vs Disc\nFormat-aware"]
    end
    
    subgraph Stage5["Stage 5"]
        S5[🗜️ Compress]
        S5D["Target-optimal format\nZIP/7z/CHD/RVZ\nMax compression"]
    end
    
    subgraph Stage6["Stage 6"]
        S6[🎨 Metadata]
        S6D["gamelist.xml\nBoxart & videos\nPre-scraped DB"]
    end
    
    S1 --> S2 --> S3 --> S4 --> S5 --> S6
"""

MERMAID_TIERS = """
flowchart TD
    subgraph Budget["💾 Storage Budget System"]
        B1[Parse Budget: 512GB]
        B1 --> B2[Account Overhead: ~456GB usable]
        B2 --> B3[Order by Tier Priority]
    end
    
    subgraph Tiers["📊 Platform Tiers"]
        T1["🟢 Tier 1: Tiny\nGB, GBC, GG, NGP, etc.\n~500MB total"]
        T2["🟡 Tier 2: Small\nNES, SNES, GBA, Genesis\n~2GB total"]
        T3["🟠 Tier 3: Medium\nPSX, Saturn, N64\n5-15GB each"]
        T4["🔴 Tier 4: Large\nDreamcast, PSP, NDS\n20-50GB each"]
        T5["⚫ Tier 5: Massive\nPS2, GameCube, Wii, PS3\n100GB+ each"]
    end
    
    B3 --> T1 --> T2 --> T3 --> T4 --> T5
"""

MERMAID_TARGETS = """
flowchart TB
    subgraph Composition["🎯 Composed Targets"]
        F[Frontend Config]
        D[Device Config]
        F --> CT[Composed Target]
        D --> CT
    end
    
    subgraph Frontend["Frontend Examples"]
        F1[Batocera]
        F2[ROCKNIX]
        F3[EmuELEC]
        F4[Everdrive]
    end
    
    subgraph Device["Device Examples"]
        D1[R36S]
        D2[Steam Deck]
        D3[RGB10 Max3]
        D4[X55]
    end
    
    subgraph Result["Result: rocknix-r36s"]
        R1["✓ ZIP compression"]
        R2["✓ Skip N64, Saturn, DC"]
        R3["✓ 256GB budget profile"]
        R4["✓ Balanced organization"]
    end
    
    F1 & F2 --> CT
    D1 & D2 --> CT
    CT --> R1 & R2 & R3 & R4
"""

CAPABILITIES = [
    {
        "icon": "🎯",
        "name": "DAT-Driven Validation",
        "description": "Every ROM validated against official No-Intro and Redump DAT files using MD5 hashes. No guessing, no bad dumps, no wrong regions.",
        "details": ["Auto-discovers DAT files by platform name", "Supports Retool-processed 1G1R DATs", "MD5 hash database for fast lookups", "Reports match rates and rejections"]
    },
    {
        "icon": "🌍",
        "name": "1G1R Smart Filtering",
        "description": "One Game, One ROM. Automatically selects the best version of each game based on region priority (USA → Europe → Japan) and revision.",
        "details": ["Retool pre-filtered DATs supported", "English language prioritized", "Latest revisions preferred", "No duplicates, no clones"]
    },
    {
        "icon": "⭐",
        "name": "Curated Best-Of Lists",
        "description": "54+ hand-curated platform lists ensure you get the cream of each library. When storage is limited, quality over quantity.",
        "details": ["PSX: 60 essential games", "NDS: 57 must-plays", "Dreamcast: 27 classics", "Auto-rescue from filtered sets"]
    },
    {
        "icon": "💾",
        "name": "Storage Budget System",
        "description": "Define your storage limit and ROM Farmer intelligently prioritizes platforms by tier. Tier 1-2 always included, Tier 3+ uses best-of when space is tight.",
        "details": ["Parses '512GB' → ~456GB usable", "5-tier priority system", "Real-time size tracking", "Learns from previous builds"]
    },
    {
        "icon": "🗜️",
        "name": "Target-Aware Compression",
        "description": "Different targets need different formats. ROM Farmer picks the optimal compression for each target automatically.",
        "details": ["ZIP for fast loading (handhelds)", "7z for maximum compression", "CHD for disc images", "XISO, RVZ for specific consoles"]
    },
    {
        "icon": "🎨",
        "name": "Pre-Scraped Metadata",
        "description": "Skip the ScreenScraper rate limits. ROM Farmer includes a pre-built database with artwork, videos, and game info ready to go.",
        "details": ["gamelist.xml generation", "Boxart, screenshots, videos", "Wheels and marquees", "MD5-based accurate matching"]
    },
    {
        "icon": "📱",
        "name": "Composed Device Targets",
        "description": "Combine Frontend (Batocera, ROCKNIX) + Device (R36S, Steam Deck) into smart targets that know what works and what doesn't.",
        "details": ["Auto-skip unsupported platforms", "Device-specific compression", "Storage profile selection", "Frontend folder structure"]
    },
    {
        "icon": "🔄",
        "name": "Resumable Builds",
        "description": "Interrupted? No problem. Full state tracking lets you resume exactly where you left off. No re-processing completed platforms.",
        "details": ["Build state persistence", "Per-platform checkpoints", "Error recovery", "Progress reporting"]
    },
]

PLATFORM_SUPPORT = {
    "Cartridge Systems (Tier 1-2)": [
        "NES", "SNES", "N64", "Game Boy", "GBC", "GBA", "NDS", "3DS",
        "Genesis", "Master System", "Game Gear", "32X", "SG-1000",
        "TurboGrafx-16", "Neo Geo Pocket", "NGPC", "WonderSwan", "WSC",
        "Atari 2600", "5200", "7800", "Jaguar", "Lynx",
        "Virtual Boy", "ColecoVision", "Intellivision", "Vectrex"
    ],
    "Disc Systems (Tier 3-5)": [
        "PlayStation", "PS2", "PS3", "PSP",
        "Sega CD", "Saturn", "Dreamcast",
        "TurboGrafx-CD", "PC Engine CD",
        "GameCube", "Wii", "Wii U",
        "Xbox", "Xbox 360",
        "3DO", "CD-i"
    ],
    "Special Format Handling": [
        "Multi-disc → Auto M3U playlists",
        "PS1/Saturn/etc → CHD compression",
        "Xbox/360 → XISO extraction",
        "GameCube/Wii → RVZ compression",
        "PS3 → JB folder structure"
    ]
}

STATS = {
    "platforms": "40+",
    "best_of_lists": "54",
    "compression_formats": "8",
    "device_profiles": "5+",
    "stages": "8",
}


def generate_html_report():
    """Generate the complete HTML report with embedded diagrams."""
    
    print("🎨 Rendering Mermaid diagrams to PNG...")
    
    # Render all diagrams
    print("  - Architecture diagram...")
    arch_png = render_mermaid_to_base64(MERMAID_ARCHITECTURE, width=1000)
    
    print("  - Pipeline diagram...")
    pipeline_png = render_mermaid_to_base64(MERMAID_PIPELINE, width=1100)
    
    print("  - Tier system diagram...")
    tier_png = render_mermaid_to_base64(MERMAID_TIERS, width=900)
    
    print("  - Targets diagram...")
    targets_png = render_mermaid_to_base64(MERMAID_TARGETS, width=900)
    
    # Generate capability cards
    capability_cards = ""
    for cap in CAPABILITIES:
        details_html = "".join(f"<li>{d}</li>" for d in cap["details"])
        capability_cards += f"""
        <div class="capability-card">
            <div class="cap-icon">{cap["icon"]}</div>
            <h3>{cap["name"]}</h3>
            <p>{cap["description"]}</p>
            <ul class="cap-details">{details_html}</ul>
        </div>
        """
    
    # Generate platform lists
    platform_html = ""
    for category, platforms in PLATFORM_SUPPORT.items():
        platform_html += f'<h4>{category}</h4><div class="platform-grid">'
        for p in platforms:
            platform_html += f'<span class="platform-badge">{p}</span>'
        platform_html += '</div>'
    
    # Stats cards
    stats_html = ""
    stat_labels = {
        "platforms": "Platforms Supported",
        "best_of_lists": "Curated Lists",
        "compression_formats": "Compression Formats",
        "device_profiles": "Device Profiles",
        "stages": "Pipeline Stages"
    }
    for key, value in STATS.items():
        stats_html += f"""
        <div class="stat-card">
            <div class="stat-value">{value}</div>
            <div class="stat-label">{stat_labels[key]}</div>
        </div>
        """
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ROM Farmer - Project Report</title>
    <style>
        :root {{
            --primary: #10b981;
            --primary-dark: #059669;
            --primary-light: #34d399;
            --secondary: #6366f1;
            --accent: #f59e0b;
            --dark: #1f2937;
            --darker: #111827;
            --light: #f3f4f6;
            --card-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.2);
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            line-height: 1.6;
            color: var(--dark);
            background: var(--darker);
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        header {{
            background: linear-gradient(135deg, var(--primary-dark) 0%, var(--secondary) 100%);
            padding: 4rem 2rem;
            text-align: center;
            color: white;
            position: relative;
            overflow: hidden;
        }}
        
        header::before {{
            content: "🌾";
            position: absolute;
            font-size: 20rem;
            opacity: 0.1;
            top: -2rem;
            right: -2rem;
        }}
        
        header h1 {{
            font-size: 3.5rem;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            position: relative;
        }}
        
        header .subtitle {{
            font-size: 1.4rem;
            opacity: 0.95;
            max-width: 600px;
            margin: 0 auto;
        }}
        
        header .date {{
            margin-top: 1.5rem;
            font-size: 0.9rem;
            opacity: 0.7;
        }}
        
        .stats-bar {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            flex-wrap: wrap;
            padding: 1.5rem;
            background: rgba(255,255,255,0.1);
            margin-top: 2rem;
            border-radius: 12px;
        }}
        
        .stat-card {{
            text-align: center;
            padding: 0.5rem 1.5rem;
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: bold;
        }}
        
        .stat-label {{
            font-size: 0.85rem;
            opacity: 0.8;
        }}
        
        section {{
            padding: 4rem 0;
        }}
        
        section:nth-child(even) {{
            background: var(--light);
        }}
        
        section:nth-child(odd) {{
            background: white;
        }}
        
        .section-header {{
            text-align: center;
            margin-bottom: 3rem;
        }}
        
        .section-header h2 {{
            font-size: 2.5rem;
            color: var(--dark);
            margin-bottom: 0.5rem;
        }}
        
        .section-header p {{
            color: #666;
            font-size: 1.1rem;
            max-width: 600px;
            margin: 0 auto;
        }}
        
        .card {{
            background: white;
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: var(--card-shadow);
        }}
        
        .diagram {{
            text-align: center;
            margin: 2rem 0;
            padding: 1rem;
            background: #fafafa;
            border-radius: 12px;
        }}
        
        .diagram img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }}
        
        .diagram-caption {{
            margin-top: 1rem;
            color: #666;
            font-size: 0.9rem;
        }}
        
        .capabilities-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
        }}
        
        .capability-card {{
            background: white;
            border-radius: 16px;
            padding: 2rem;
            box-shadow: var(--card-shadow);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .capability-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 20px 50px -15px rgba(0, 0, 0, 0.25);
        }}
        
        .cap-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}
        
        .capability-card h3 {{
            color: var(--primary-dark);
            margin-bottom: 0.75rem;
            font-size: 1.3rem;
        }}
        
        .capability-card p {{
            color: #555;
            margin-bottom: 1rem;
        }}
        
        .cap-details {{
            list-style: none;
            font-size: 0.9rem;
            color: #666;
        }}
        
        .cap-details li {{
            padding: 0.25rem 0;
            padding-left: 1.25rem;
            position: relative;
        }}
        
        .cap-details li::before {{
            content: "→";
            position: absolute;
            left: 0;
            color: var(--primary);
        }}
        
        .highlight-box {{
            background: linear-gradient(135deg, #ecfdf5, #d1fae5);
            border-left: 4px solid var(--primary);
            padding: 1.5rem 2rem;
            border-radius: 0 12px 12px 0;
            margin: 2rem 0;
        }}
        
        .highlight-box h4 {{
            color: var(--primary-dark);
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
        }}
        
        .highlight-box p {{
            color: #065f46;
        }}
        
        .platform-grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 1rem 0 2rem;
        }}
        
        .platform-badge {{
            background: var(--light);
            padding: 0.35rem 0.85rem;
            border-radius: 20px;
            font-size: 0.85rem;
            border: 1px solid #e5e7eb;
        }}
        
        h4 {{
            color: var(--dark);
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
        }}
        
        .code-block {{
            background: var(--darker);
            color: #e2e8f0;
            padding: 1.5rem;
            border-radius: 12px;
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 0.9rem;
            overflow-x: auto;
            margin: 1.5rem 0;
        }}
        
        .code-comment {{
            color: #6b7280;
        }}
        
        .code-key {{
            color: var(--primary-light);
        }}
        
        .code-value {{
            color: #fbbf24;
        }}
        
        .two-col {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            align-items: start;
        }}
        
        .workflow-step {{
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        
        .step-num {{
            background: var(--primary);
            color: white;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            flex-shrink: 0;
        }}
        
        .step-content h4 {{
            margin: 0 0 0.25rem;
            color: var(--dark);
        }}
        
        .step-content p {{
            color: #666;
            font-size: 0.95rem;
            margin: 0;
        }}
        
        footer {{
            background: var(--darker);
            color: white;
            text-align: center;
            padding: 3rem 2rem;
        }}
        
        footer p {{
            opacity: 0.7;
        }}
        
        @media (max-width: 768px) {{
            header h1 {{
                font-size: 2.5rem;
            }}
            
            .two-col {{
                grid-template-columns: 1fr;
            }}
            
            .capabilities-grid {{
                grid-template-columns: 1fr;
            }}
            
            .stats-bar {{
                gap: 1rem;
            }}
            
            .stat-value {{
                font-size: 1.8rem;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>🌾 ROM Farmer</h1>
            <p class="subtitle">The configuration-driven ROM collection pipeline that maximizes great games per gigabyte</p>
            <p class="date">Project Report • {datetime.now().strftime('%B %d, %Y')}</p>
            
            <div class="stats-bar">
                {stats_html}
            </div>
        </div>
    </header>
    
    <section>
        <div class="container">
            <div class="section-header">
                <h2>🎯 What is ROM Farmer?</h2>
                <p>A complete solution for building optimized retro gaming collections</p>
            </div>
            
            <div class="highlight-box">
                <h4>💡 Core Philosophy</h4>
                <p><strong>"EVERYTHING is really about getting the best compression ratio so that we can have more great games than anyone else for the storage space."</strong></p>
            </div>
            
            <p style="font-size: 1.1rem; color: #444; margin: 1.5rem 0;">ROM Farmer transforms ROM collection management from tedious manual work into a streamlined, configuration-driven process. Define your target device and storage budget in YAML, and ROM Farmer handles everything else: validation, filtering, compression, metadata, and organization.</p>
            
            <div class="diagram">
                <img src="data:image/png;base64,{arch_png}" alt="ROM Farmer Architecture">
                <p class="diagram-caption">End-to-end pipeline from source archives to deployment-ready collections</p>
            </div>
        </div>
    </section>
    
    <section>
        <div class="container">
            <div class="section-header">
                <h2>⚙️ The Pipeline</h2>
                <p>8 stages process your ROMs with surgical precision</p>
            </div>
            
            <div class="diagram">
                <img src="data:image/png;base64,{pipeline_png}" alt="ROM Farmer Pipeline">
            </div>
            
            <div class="two-col" style="margin-top: 2rem;">
                <div>
                    <div class="workflow-step">
                        <div class="step-num">1</div>
                        <div class="step-content">
                            <h4>DAT Validation</h4>
                            <p>Verify every ROM against official No-Intro/Redump DAT files using MD5 hashes</p>
                        </div>
                    </div>
                    <div class="workflow-step">
                        <div class="step-num">2</div>
                        <div class="step-content">
                            <h4>1G1R Filtering</h4>
                            <p>One Game, One ROM - select best version per title with English priority</p>
                        </div>
                    </div>
                    <div class="workflow-step">
                        <div class="step-num">3</div>
                        <div class="step-content">
                            <h4>Selection Filters</h4>
                            <p>Apply curated best-of lists or custom selection criteria</p>
                        </div>
                    </div>
                    <div class="workflow-step">
                        <div class="step-num">4</div>
                        <div class="step-content">
                            <h4>List Processing</h4>
                            <p>Delete unwanted titles, add extras from Myrient/other sources</p>
                        </div>
                    </div>
                </div>
                <div>
                    <div class="workflow-step">
                        <div class="step-num">5</div>
                        <div class="step-content">
                            <h4>Smart Extraction</h4>
                            <p>Extract cartridge ROMs from ZIPs, handle disc images appropriately</p>
                        </div>
                    </div>
                    <div class="workflow-step">
                        <div class="step-num">6</div>
                        <div class="step-content">
                            <h4>Optimal Compression</h4>
                            <p>Target-aware format selection: ZIP, 7z, CHD, RVZ, or uncompressed</p>
                        </div>
                    </div>
                    <div class="workflow-step">
                        <div class="step-num">7</div>
                        <div class="step-content">
                            <h4>Organization</h4>
                            <p>Arrange files using flat, alphabetical, or rich subdirectory structures</p>
                        </div>
                    </div>
                    <div class="workflow-step">
                        <div class="step-num">8</div>
                        <div class="step-content">
                            <h4>Metadata Generation</h4>
                            <p>Create gamelist.xml with artwork, videos, and game information</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
    
    <section>
        <div class="container">
            <div class="section-header">
                <h2>✨ Key Capabilities</h2>
                <p>Everything you need for professional-grade ROM management</p>
            </div>
            
            <div class="capabilities-grid">
                {capability_cards}
            </div>
        </div>
    </section>
    
    <section>
        <div class="container">
            <div class="section-header">
                <h2>💾 Smart Storage Management</h2>
                <p>Intelligent tier-based prioritization ensures quality over quantity</p>
            </div>
            
            <div class="diagram">
                <img src="data:image/png;base64,{tier_png}" alt="Tier System">
                <p class="diagram-caption">5-tier system ensures must-have platforms always fit</p>
            </div>
            
            <div class="highlight-box">
                <h4>How It Works</h4>
                <p>Define a storage budget like "256GB" and ROM Farmer calculates usable space (accounting for filesystem overhead), then processes platforms in tier order. Tier 1-2 platforms are always included in full. When space gets tight, Tier 3+ platforms automatically switch to "best-of" mode, including only curated essential games instead of full libraries.</p>
            </div>
        </div>
    </section>
    
    <section>
        <div class="container">
            <div class="section-header">
                <h2>🎯 Composed Targets</h2>
                <p>Smart device profiles that know what works and what doesn't</p>
            </div>
            
            <div class="diagram">
                <img src="data:image/png;base64,{targets_png}" alt="Composed Targets">
            </div>
            
            <div class="two-col">
                <div class="card">
                    <h3>Frontend Configs</h3>
                    <p>Define how the frontend organizes and accesses ROMs:</p>
                    <ul style="margin-top: 1rem; color: #555;">
                        <li>Preferred compression format</li>
                        <li>Folder structure expectations</li>
                        <li>Metadata format (gamelist.xml)</li>
                        <li>Media types supported</li>
                    </ul>
                </div>
                <div class="card">
                    <h3>Device Configs</h3>
                    <p>Define hardware capabilities and limitations:</p>
                    <ul style="margin-top: 1rem; color: #555;">
                        <li>Unsupported platforms (auto-skip)</li>
                        <li>Storage capacity profiles</li>
                        <li>Performance characteristics</li>
                        <li>Display considerations</li>
                    </ul>
                </div>
            </div>
            
            <div class="code-block">
<span class="code-comment"># Example: rocknix-r36s-handheld.yaml</span>
<span class="code-key">name:</span> <span class="code-value">rocknix-r36s-handheld</span>
<span class="code-key">target:</span> <span class="code-value">rocknix-r36s</span>  <span class="code-comment"># Combines rocknix frontend + r36s device</span>
<span class="code-key">profile:</span> <span class="code-value">handheld</span>

<span class="code-key">storage:</span>
  <span class="code-key">budget:</span> <span class="code-value">256gb</span>

<span class="code-key">platforms:</span>
  - <span class="code-value">nes</span>      <span class="code-comment"># Tier 2 - full library</span>
  - <span class="code-value">snes</span>     <span class="code-comment"># Tier 2 - full library</span>
  - <span class="code-value">gb</span>       <span class="code-comment"># Tier 1 - full library</span>
  - <span class="code-value">gbc</span>      <span class="code-comment"># Tier 1 - full library</span>
  - <span class="code-value">gba</span>      <span class="code-comment"># Tier 2 - full library</span>
  - <span class="code-value">psx</span>      <span class="code-comment"># Tier 3 - best-of list (60 games)</span>
  - <span class="code-value">genesis</span>  <span class="code-comment"># Tier 2 - full library</span>
  <span class="code-comment"># n64, saturn, dreamcast auto-skipped (R36S can't emulate well)</span>
            </div>
        </div>
    </section>
    
    <section>
        <div class="container">
            <div class="section-header">
                <h2>🎮 Platform Support</h2>
                <p>40+ platforms with format-specific handling</p>
            </div>
            
            <div class="card">
                {platform_html}
            </div>
        </div>
    </section>
    
    <section>
        <div class="container">
            <div class="section-header">
                <h2>🚀 Why ROM Farmer?</h2>
                <p>The problems we solve</p>
            </div>
            
            <div class="two-col">
                <div class="card">
                    <h3 style="color: #dc2626;">❌ The Old Way</h3>
                    <ul style="margin-top: 1rem; color: #555; list-style: none;">
                        <li style="padding: 0.5rem 0;">• Download massive full sets blindly</li>
                        <li style="padding: 0.5rem 0;">• Write custom scripts per platform</li>
                        <li style="padding: 0.5rem 0;">• Manually run scraper for hours</li>
                        <li style="padding: 0.5rem 0;">• Guess at compression formats</li>
                        <li style="padding: 0.5rem 0;">• Delete random games when out of space</li>
                        <li style="padding: 0.5rem 0;">• Start over when something breaks</li>
                        <li style="padding: 0.5rem 0;">• Different process for each device</li>
                    </ul>
                </div>
                <div class="card">
                    <h3 style="color: var(--primary-dark);">✅ The ROM Farmer Way</h3>
                    <ul style="margin-top: 1rem; color: #555; list-style: none;">
                        <li style="padding: 0.5rem 0;">• DAT-validated, 1G1R filtered ROMs</li>
                        <li style="padding: 0.5rem 0;">• Single YAML config for all platforms</li>
                        <li style="padding: 0.5rem 0;">• Pre-scraped metadata database</li>
                        <li style="padding: 0.5rem 0;">• Target-aware optimal compression</li>
                        <li style="padding: 0.5rem 0;">• Tier-based intelligent selection</li>
                        <li style="padding: 0.5rem 0;">• Full resume support</li>
                        <li style="padding: 0.5rem 0;">• Composed targets for any device</li>
                    </ul>
                </div>
            </div>
            
            <div class="highlight-box" style="margin-top: 2rem;">
                <h4>🏆 The Result</h4>
                <p>More great games, better organized, with full metadata and media, optimized for your specific device — all from a single YAML configuration file. Build once, deploy anywhere.</p>
            </div>
        </div>
    </section>
    
    <footer>
        <div class="container">
            <h2 style="margin-bottom: 1rem;">🌾 ROM Farmer</h2>
            <p>Configuration-driven ROM collection management</p>
            <p style="margin-top: 2rem; font-size: 0.85rem;">Report generated {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
        </div>
    </footer>
</body>
</html>
"""
    
    output_path = OUTPUT_DIR / "rom-farmer-report.html"
    output_path.write_text(html)
    print(f"\n✅ Report generated: {output_path}")
    print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")
    
    return output_path


if __name__ == "__main__":
    generate_html_report()
