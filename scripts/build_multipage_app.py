import re
from pathlib import Path

INDEX_PATH = Path("frontend/public/index.html")
PUBLIC_DIR = Path("frontend/public")

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    full_html = f.read()

# 1. Extract Head
head_match = re.search(r'(<head>[\s\S]*?</head>)', full_html)
head_content = head_match.group(1) if head_match else ""

# 2. Extract Header Bar
header_match = re.search(r'(<!-- 1\. Header Bar -->[\s\S]*?</header>)', full_html)
header_content = header_match.group(1) if header_match else ""

# 3. Extract Modals & Chatbot & Scripts
modals_match = re.search(r'(<!-- Direct Telemetry File Upload Modal -->[\s\S]*?</html>)', full_html)
footer_modals_content = modals_match.group(1) if modals_match else ""

# Map of pages to generate
PAGES = [
    {
        "id": "tab-overview",
        "file": "index.html",
        "title": "Executive Overview",
        "icon": "⚡",
        "breadcrumb": "Executive Overview & Narrative Synthesis",
        "extract_regex": r'(<!-- ===+ -->\s*<!-- TAB 1: EXECUTIVE OVERVIEW -->\s*<!-- ===+ -->\s*<section id="tab-overview"[\s\S]*?</section>)'
    },
    {
        "id": "tab-timeline",
        "file": "timeline.html",
        "title": "Forensic Timeline",
        "icon": "🕒",
        "breadcrumb": "Chronological Forensic Timeline & Quotes",
        "extract_regex": r'(<!-- ===+ -->\s*<!-- TAB 2: FORENSIC TIMELINE -->\s*<!-- ===+ -->\s*<section id="tab-timeline"[\s\S]*?</section>)'
    },
    {
        "id": "tab-rca",
        "file": "rca.html",
        "title": "5-Whys Root Cause",
        "icon": "🔍",
        "breadcrumb": "Five-Tier Root Cause Analysis & Action Items",
        "extract_regex": r'(<!-- ===+ -->\s*<!-- TAB 3: 5-WHYS & RCA -->\s*<!-- ===+ -->\s*<section id="tab-rca"[\s\S]*?</section>)'
    },
    {
        "id": "tab-aiops-ml",
        "file": "aiops-ml.html",
        "title": "Trained AIOps AI Models",
        "icon": "🧠",
        "breadcrumb": "Trained AIOps AI Neural Models & Interactive Playground",
        "extract_regex": r'(<!-- ===+ -->\s*<!-- TAB: TRAINED AIOPS AI MODELS & LIVE PREDICTOR -->\s*<!-- ===+ -->\s*<section id="tab-aiops-ml"[\s\S]*?</section>)'
    },
    {
        "id": "tab-topology",
        "file": "topology.html",
        "title": "Service Topology",
        "icon": "🌐",
        "breadcrumb": "System Architecture & Degraded Mesh Topology",
        "extract_regex": r'(<!-- ===+ -->\s*<!-- TAB 4: SERVICE TOPOLOGY -->\s*<!-- ===+ -->\s*<section id="tab-topology"[\s\S]*?</section>)'
    },
    {
        "id": "tab-logs",
        "file": "logs.html",
        "title": "Telemetry Logs",
        "icon": "📋",
        "breadcrumb": "Ingested Multi-Channel Telemetry Logs",
        "extract_regex": r'(<!-- ===+ -->\s*<!-- TAB 5: TELEMETRY LOGS -->\s*<!-- ===+ -->\s*<section id="tab-logs"[\s\S]*?</section>)'
    },
    {
        "id": "tab-privacy",
        "file": "privacy.html",
        "title": "Privacy & Security",
        "icon": "🔒",
        "breadcrumb": "Zero-Trust Privacy & PII Scrubbing Diff",
        "extract_regex": r'(<!-- ===+ -->\s*<!-- TAB 6: PRIVACY & ZERO-TRUST SECURITY -->\s*<!-- ===+ -->\s*<section id="tab-privacy"[\s\S]*?</section>)'
    },
    {
        "id": "tab-report",
        "file": "report.html",
        "title": "Post-Mortem Report",
        "icon": "📄",
        "breadcrumb": "Full 20-Section Enterprise Post-Mortem Report",
        "extract_regex": r'(<!-- ===+ -->\s*<!-- TAB 7: POST-MORTEM REPORT \(20-Section Reader\) -->\s*<!-- ===+ -->\s*<section id="tab-report"[\s\S]*?</section>)'
    },
    {
        "id": "tab-benchmarks",
        "file": "benchmarks.html",
        "title": "Benchmarks",
        "icon": "📊",
        "breadcrumb": "MTTD, MTTR & Noise Reduction Benchmarks",
        "extract_regex": r'(<!-- ===+ -->\s*<!-- TAB 8: BENCHMARKS -->\s*<!-- ===+ -->\s*<section id="tab-benchmarks"[\s\S]*?</section>)'
    },
    {
        "id": "tab-forensic-matrix",
        "file": "forensic-matrix.html",
        "title": "Forensic Matrix & Raw Data",
        "icon": "🧬",
        "breadcrumb": "Forensic Evidence Matrix & 3-Lakh Raw Dataset",
        "extract_regex": r'(<!-- ===+ -->\s*<!-- TAB 10: FORENSIC EVIDENCE MATRIX & FULL RAW DATASET -->\s*<!-- ===+ -->\s*<section id="tab-forensic-matrix"[\s\S]*?</section>)'
    },
    {
        "id": "tab-interactive-timeline",
        "file": "interactive-timeline.html",
        "title": "Interactive Timeline",
        "icon": "⏱️",
        "breadcrumb": "Interactive Timeline & Causal Playback Scrubber",
        "extract_regex": r'(<!-- ===+ -->\s*<!-- TAB 11: INTERACTIVE FORENSIC INVESTIGATION TIMELINE -->\s*<!-- ===+ -->\s*<section id="tab-interactive-timeline"[\s\S]*?</section>)'
    },
    {
        "id": "tab-radar",
        "file": "radar.html",
        "title": "Multi-Task Radar",
        "icon": "📡",
        "breadcrumb": "Multi-Task SRE Operational Radar Vectors",
        "extract_regex": r'(<!-- ===+ -->\s*<!-- TAB 12: MULTI-TASK OPERATIONAL RADAR -->\s*<!-- ===+ -->\s*<section id="tab-radar"[\s\S]*?</section>)'
    },
    {
        "id": "tab-causal-graph",
        "file": "causal-graph.html",
        "title": "Causal Graph & Impacts",
        "icon": "🕸️",
        "breadcrumb": "Directed Causal Dependency & Blast Propagation Graph",
        "extract_regex": r'(<!-- ===+ -->\s*<!-- TAB 13: CAUSAL GRAPH & IMPACT PROPAGATION -->\s*<!-- ===+ -->\s*<section id="tab-causal-graph"[\s\S]*?</section>)'
    },
    {
        "id": "tab-gis-damage",
        "file": "gis-damage.html",
        "title": "Damage Location / GIS",
        "icon": "🗺️",
        "breadcrumb": "Global Datacenter Blast Radius & GIS Map",
        "extract_regex": r'(<!-- ===+ -->\s*<!-- TAB 14: DAMAGE LOCATION / GIS INFRASTRUCTURE BLAST RADIUS -->\s*<!-- ===+ -->\s*<section id="tab-gis-damage"[\s\S]*?</section>)'
    }
]

# Extract each section HTML
sections = {}
for p in PAGES:
    match = re.search(p["extract_regex"], full_html)
    if match:
        content = match.group(1)
        # Ensure section is active and visible
        content = re.sub(r'class="tab-pane[^"]*"', 'class="tab-pane active" style="display:flex;"', content)
        sections[p["file"]] = content
    else:
        print(f"WARNING: Could not extract section for {p['file']}")

def build_subnav(active_file):
    nav_links = []
    for p in PAGES:
        is_active = (p["file"] == active_file)
        active_cls = " active" if is_active else ""
        nav_links.append(f'        <a href="{p["file"]}" class="subnav-tab-btn{active_cls}" data-tab="{p["id"]}"><span>{p["icon"]}</span> {p["title"]}</a>')
    
    links_html = "\n".join(nav_links)
    return f"""    <!-- 2. Subnav Multi-Page Enterprise Tabs Bar -->
    <nav class="subnav-tabs-bar">
      <div class="subnav-tabs">
{links_html}
      </div>
      <div class="subnav-right-meta">
        <span class="status-indicator-live">●</span>
        <span>Deterministic Python Sorter • 100% Grounded</span>
      </div>
    </nav>"""

# Generate each HTML file
for p in PAGES:
    file_name = p["file"]
    section_html = sections.get(file_name, "")
    subnav_html = build_subnav(file_name)
    
    breadcrumb_html = f"""      <!-- Enterprise Breadcrumb Context Header -->
      <div class="enterprise-page-header">
        <div class="page-breadcrumb">
          <a href="index.html" class="breadcrumb-link">🛡️ AegisOps Enterprise</a>
          <span class="breadcrumb-sep">/</span>
          <span class="breadcrumb-current-incident" id="header-incident-badge">INC-2026-PAY-882</span>
          <span class="breadcrumb-sep">/</span>
          <span class="breadcrumb-active-topic">{p["icon"]} {p["breadcrumb"]}</span>
        </div>
        <div style="font-size:11.5px; color:var(--text-tertiary); font-family:var(--font-mono); display:flex; align-items:center; gap:8px;">
          <span>MNC Production Workspace</span>
          <span>•</span>
          <span style="color:#34d399;">● Online</span>
        </div>
      </div>"""

    full_page_html = f"""<!DOCTYPE html>
<html lang="en">
{head_content}
<body>
  <div class="app-container">
    {header_content}

{subnav_html}

    <!-- 3. Main Content Scroll Area -->
    <main class="main-content-scroll" id="main-content-scroll">
{breadcrumb_html}

{section_html}
    </main>
  </div>

{footer_modals_content}
"""

    target_file = PUBLIC_DIR / file_name
    with open(target_file, "w", encoding="utf-8") as out:
        out.write(full_page_html)
    print(f"Generated page: {file_name} ({len(full_page_html):,} bytes)")

print("\nSUCCESS: All 14 dedicated MNC pages generated!")
