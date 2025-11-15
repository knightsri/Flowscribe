#!/usr/bin/env python3
"""
Generate master index for Flowscribe documentation (C4 L1-L4 + Architecture Review)

Enhancements included:
- Architectural Layers = union(Deptrac layers, L3 docs)
- Rich Mermaid overview with real inter-layer arrows from deptrac.yaml ruleset
- Clear counters ("Total Components (Deptrac)" and "L4 Component Docs")
- "Uncovered dependencies" KPI parsed from architecture-review.md
- Cost & Usage Summary (v1.0 usage-first metrics) + legend
- NEW: Footnote when roll-up Total Time differs >5% from per-stage table sum
"""

import json
import argparse
import time
import re
from pathlib import Path
from datetime import datetime
from logger import setup_logger

logger = setup_logger(__name__)

try:
    import yaml
except ImportError:
    yaml = None


# -------------------------------
# Metrics (v1.0-first + legacy)
# -------------------------------

def _json_load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _ensure_stage(bucket, key):
    if key not in bucket:
        bucket[key] = {
            "cost": 0.0,
            "time": 0.0,
            "tokens_in": 0,
            "tokens_out": 0,
            "model": None
        }


def _extract_v1(obj: dict):
    """Extract totals and per-level details from canonical v1.0 metrics object."""
    if not isinstance(obj, dict):
        return None
    if str(obj.get("version", "")).strip() != "1.0":
        return None

    levels = obj.get("levels", {})
    totals = obj.get("totals", {})

    if not isinstance(levels, dict) or not isinstance(totals, dict):
        return None

    def num(x, t=float):
        try:
            return t(x or 0)
        except Exception:
            return t(0)

    out = {
        "totals": {
            "cost": num(totals.get("cost_usd")),
            "time": num(totals.get("time_seconds")),
            "tokens_in": int(totals.get("tokens_in", 0) or 0),
            "tokens_out": int(totals.get("tokens_out", 0) or 0),
        },
        "levels": {}
    }

    for k, v in levels.items():
        if not isinstance(v, dict):
            continue
        out["levels"][k] = {
            "cost": num(v.get("cost_usd")),
            "time": num(v.get("time_seconds")),
            "tokens_in": int(v.get("tokens_in", 0) or 0),
            "tokens_out": int(v.get("tokens_out", 0) or 0),
            "model": v.get("model")
        }
    return out


def _extract_legacy(obj: dict):
    """Best-effort extraction from older metrics files; returns v1-like shape."""
    if not isinstance(obj, dict):
        return None

    def num(x, t=float):
        try:
            return t(x or 0)
        except Exception:
            return t(0)

    cost = obj.get("total_cost")
    if cost is None:
        cost = obj.get("cost_usd") or 0.0
    cost = num(cost)

    ti = obj.get("input_tokens", 0) or 0
    to = obj.get("output_tokens", 0) or 0
    tokens_in = int(ti)
    tokens_out = int(to)

    time_s = obj.get("total_time")
    if time_s is None:
        time_s = obj.get("duration_seconds") or 0.0
    time_s = num(time_s)

    guess = str(obj.get("level") or obj.get("stage") or obj.get("phase") or "legacy")
    model = obj.get("model")

    return {
        "totals": {"cost": cost, "time": time_s, "tokens_in": tokens_in, "tokens_out": tokens_out},
        "levels": {guess: {"cost": cost, "time": time_s, "tokens_in": tokens_in, "tokens_out": tokens_out, "model": model}}
    }


def read_all_metrics(output_dir):
    """Aggregate totals across all metrics files (v1.0-first, legacy fallback)."""
    out_dir = Path(output_dir)

    files = [
        '.flowscribe-metrics.json',
        '.c4-level1-metrics.json',
        '.c4-level2-metrics.json',
        '.architecture-review-metrics.json',
        '.c4-level4-metrics.json',
    ]
    files += [p.name for p in out_dir.glob('.c4-level3-*-metrics.json')]

    total_cost = 0.0
    total_time = 0.0
    total_tokens_in = 0
    total_tokens_out = 0

    stages = {}
    breakdown = {}

    for name in files:
        p = out_dir / name
        if not p.exists():
            continue
        obj = _json_load(p)
        if not obj:
            continue

        parsed = _extract_v1(obj) or _extract_legacy(obj)
        if not parsed:
            continue

        total_cost += parsed["totals"]["cost"]
        total_time += parsed["totals"]["time"]
        total_tokens_in += parsed["totals"]["tokens_in"]
        total_tokens_out += parsed["totals"]["tokens_out"]

        for lvl, data in parsed["levels"].items():
            _ensure_stage(stages, lvl)
            s = stages[lvl]
            s["cost"] += data["cost"]
            s["time"] += data["time"]
            s["tokens_in"] += data["tokens_in"]
            s["tokens_out"] += data["tokens_out"]
            if not s["model"] and data.get("model"):
                s["model"] = data["model"]

    for lvl, s in stages.items():
        breakdown[lvl] = {"cost": float(s["cost"]), "time": float(s["time"]), "tokens": int(s["tokens_in"] + s["tokens_out"])}

    return {
        "total_cost": float(total_cost),
        "total_tokens": int(total_tokens_in + total_tokens_out),
        "total_time": float(total_time),
        "breakdown": breakdown,
        "stages": stages
    }


# -------------------------------
# Deptrac readers
# -------------------------------

def read_deptrac_stats(output_dir):
    """Read high-level stats from deptrac-report.json (violations, layers)."""
    path = Path(output_dir) / 'deptrac-report.json'
    if not path.exists():
        return {'violations': 0, 'layers': {}, 'total_components': 0}

    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        violation_count = 0
        layers = {}
        files = data.get('files', {})
        for file_path, file_data in files.items():
            msgs = file_data.get('messages', [])
            violation_count += len(msgs)
            for msg_data in msgs:
                msg = msg_data.get('message', '')
                if ' on ' in msg and '(' in msg:
                    layer_part = msg.split('(')[-1].strip(')')
                    if ' on ' in layer_part:
                        src_layer = layer_part.split(' on ')[0].strip()
                        layers.setdefault(src_layer, set())
                        comp = file_path.split('/')[-1].replace('.php', '')
                        layers[src_layer].add(comp)
        layer_counts = {k: len(v) for k, v in layers.items()}
        return {'violations': violation_count, 'layers': layer_counts, 'total_components': sum(layer_counts.values())}
    except Exception:
        return {'violations': 0, 'layers': {}, 'total_components': 0}


def _find_deptrac_yaml(output_dir):
    """Locate deptrac.yaml close to the output directory."""
    cands = [
        Path(output_dir) / 'deptrac.yaml',
        Path(output_dir).parent / 'deptrac.yaml',
    ]
    for c in cands:
        if c.exists():
            return c
    # Walk up parents
    for p in Path(output_dir).parents:
        cand = p / 'deptrac.yaml'
        if cand.exists():
            return cand
    return None


def read_deptrac_edges(output_dir):
    """
    Read allowed layer dependencies from deptrac.yaml ruleset.
    Returns a list of (source_layer, target_layer) edges.
    """
    if yaml is None:
        return []

    yml_path = _find_deptrac_yaml(output_dir)
    if not yml_path or not yml_path.exists():
        return []

    try:
        cfg = yaml.safe_load(yml_path.read_text(encoding='utf-8'))
    except Exception:
        return []

    root = cfg.get('deptrac') or cfg
    ruleset = root.get('ruleset') or root.get('rules') or {}
    edges = []
    if isinstance(ruleset, dict):
        for src, targets in ruleset.items():
            if isinstance(targets, (list, tuple)):
                for dst in targets:
                    if isinstance(dst, str):
                        edges.append((str(src), dst))
    # dedupe
    seen = set()
    unique = []
    for a, b in edges:
        k = (a.strip(), b.strip())
        if k not in seen:
            seen.add(k)
            unique.append(k)
    return unique


# -------------------------------
# Review parser
# -------------------------------

def parse_architecture_review(output_dir):
    """Pull grade, executive summary, and 'uncovered dependencies' KPI from architecture-review.md"""
    path = Path(output_dir) / 'architecture-review.md'
    if not path.exists():
        raise FileNotFoundError(f"Architecture review not found at {path}")

    try:
        content = path.read_text(encoding='utf-8')
        m = re.search(r'\*\*Overall (?:Grade|Architecture Grade):\*\*\s*\[?([A-F][+-]?)\]?', content, re.I)
        if not m:
            m = re.search(r'Overall (?:Grade|Architecture Grade):\s*\[?([A-F][+-]?)\]?', content, re.I)
        grade = m.group(1) if m else "Not Available"

        m2 = re.search(r'##\s+Executive Summary\s*\n+(.*?)(?=\n##|\Z)', content, re.S | re.I)
        exec_summary = m2.group(1).strip() if m2 else "Not available"

        uncovered = None
        m3 = re.search(r'(\d+)\s+uncovered dependencies', content, re.I)
        if m3:
            uncovered = int(m3.group(1))

        return {'exists': True, 'grade': grade, 'executive_summary': exec_summary, 'uncovered_dependencies': uncovered}
    except Exception:
        return {'exists': True, 'grade': 'Parse Error', 'executive_summary': 'Could not parse', 'uncovered_dependencies': None}


# -------------------------------
# File presence helpers
# -------------------------------

def count_level4_components(output_dir):
    out = Path(output_dir)
    files = [f for f in out.glob('c4-level4-*.md') if f.name != 'c4-level4.md']
    return len(files)


def validate_documentation_files(output_dir):
    out = Path(output_dir)
    status = {
        'l1': (out / 'c4-level1.md').exists(),
        'l2': (out / 'c4-level2.md').exists(),
        'l4_hub': (out / 'c4-level4.md').exists(),
        'arch_review': (out / 'architecture-review.md').exists(),
    }
    status['l3_files'] = list(out.glob('c4-level3-*.md'))
    status['l3_count'] = len(status['l3_files'])
    return status


# -------------------------------
# Mermaid rendering
# -------------------------------

def _slug(s):
    return re.sub(r'[^A-Za-z0-9_]', '_', s or '')


def render_rich_layered_mermaid(layers_dict, edges=None):
    """Build a rich layered overview using subgraphs; zero-count allowed. Draw edges if provided."""
    if not layers_dict:
        return "```mermaid\nflowchart TB\n    NoLayers[\"No layer information available\"]\n```"

    lines = []
    lines.append("```mermaid")
    lines.append("flowchart TB")

    palette = ["#e1f5fe", "#fff3e0", "#f3e5f5", "#e8f5e9", "#fce4ec", "#f1f8e9", "#ede7f6", "#e0f2f1"]
    items = sorted(layers_dict.items(), key=lambda x: (-x[1], x[0].lower()))
    for idx, (layer, count) in enumerate(items):
        sid = _slug(layer)
        color = palette[idx % len(palette)]
        lines.append(f"    subgraph {sid}_grp[\"{layer} Layer\"]")
        lines.append(f"        {sid}[\"{layer}<br/>({count} components)\"]")
        lines.append("    end")
        lines.append(f"    style {sid} fill:{color},stroke:#b0bec5,stroke-width:1px")
        lines.append(f"    classDef small fill:{color},stroke:#b0bec5,color:#263238;")

    # draw edges from ruleset if provided; otherwise simple top-to-bottom
    names = [k for k,_ in items]
    idmap = {n: _slug(n) for n in names}

    if edges:
        lower_to_actual = {n.lower(): n for n in names}
        for src, dst in edges:
            s = lower_to_actual.get(str(src).lower())
            d = lower_to_actual.get(str(dst).lower())
            if s and d and s != d:
                lines.append(f"    {idmap[s]} --> {idmap[d]}")
    else:
        if len(items) >= 2:
            for i in range(len(items) - 1):
                a = _slug(items[i][0])
                b = _slug(items[i + 1][0])
                lines.append(f"    {a} --> {b}")

    lines.append("```")
    return "\n".join(lines)


# -------------------------------
# Master index generator
# -------------------------------

def generate_master_index(project_name, output_dir):
    metrics = read_all_metrics(output_dir)
    total_cost = metrics['total_cost']
    total_tokens = metrics['total_tokens']
    total_time = metrics['total_time']

    stats = read_deptrac_stats(output_dir)
    dep_layers = stats['layers'] or {}
    total_components = stats['total_components'] or sum(dep_layers.values())
    violations = stats['violations']

    docs = validate_documentation_files(output_dir)
    l3_files = docs['l3_files']
    l3_count = docs['l3_count']
    l4_count = count_level4_components(output_dir)

    arch = parse_architecture_review(output_dir)

    # Build union of layer names: deptrac + L3 files
    l3_layer_names = []
    for f in l3_files:
        slug = f.stem.replace('c4-level3-', '')
        l3_layer_names.append(slug.replace('-', ' ').title())

    union_layers = {**{k: dep_layers.get(k, 0) for k in dep_layers.keys()}}
    for name in l3_layer_names:
        if name not in union_layers:
            union_layers[name] = 0  # zero-count allowed; still render and link

    # L3 links with counts
    l3_links = []
    for f in l3_files:
        slug = f.stem.replace('c4-level3-', '')
        display = slug.replace('-', ' ').title()
        count = union_layers.get(display, 0)
        l3_links.append(f"- **{display}:** ✅ [L3 Documentation →](./{f.name}) — {count} components")

    # Rich mermaid on union set with edges from deptrac ruleset
    edges = read_deptrac_edges(output_dir)
    mermaid_md = render_rich_layered_mermaid(union_layers, edges=edges)

    # Cost & Usage Summary table
    display_order = [
        ("level1", "🧭 C4 Level 1 - Context"),
        ("level2", "🏗️ C4 Level 2 - Containers"),
        ("level3", "🧩 C4 Level 3 - Components"),
        ("level4", "⚙️ C4 Level 4 - Code"),
        ("architecture_review", "🧱 Architecture Review"),
    ]

    stages = metrics.get("stages", {})
    rows = []
    grand_cost = 0.0
    grand_in = 0
    grand_out = 0
    grand_time = 0.0

    for key, label in display_order:
        s = stages.get(key)
        if not s:
            continue
        cost = float(s["cost"])
        tin = int(s["tokens_in"])
        tout = int(s["tokens_out"])
        tsec = float(s["time"])
        model = s.get("model") or "—"
        rows.append((label, model, cost, tin, tout, tsec))
        grand_cost += cost
        grand_in += tin
        grand_out += tout
        grand_time += tsec

    stage_sum_time = grand_time  # sum of per-stage durations

    table_lines = []
    table_lines.append("| Stage | Model | Cost (USD) | Tokens (in/out) | Duration (s) |")
    table_lines.append("|-------|-------|-----------:|----------------:|-------------:|")
    for label, model, cost, tin, tout, tsec in rows:
        table_lines.append(f"| {label} | {model} | ${cost:.4f} | {tin:,} / {tout:,} | {tsec:.1f} |")
    if rows:
        table_lines.append(f"| 💼 **TOTAL** |  | **${grand_cost:.4f}** | **{grand_in:,} / {grand_out:,}** | **{grand_time:.1f}** |")
    cost_usage_md = "\n".join(table_lines)

    legend = "_Legend: **in** = prompt tokens, **out** = completion tokens. All costs are from OpenRouter usage accounting._"
    # Add note if no L3 stage metrics present
    if not any("C4 Level 3 - Components" in r for r in table_lines):
        legend += "\n\n_Note: No L3 analysis run for this repo._"
    # Footnote when roll-up time and per-stage time differ significantly (>5%)
    try:
        if total_time and abs(total_time - stage_sum_time) / total_time > 0.05:
            delta = total_time - stage_sum_time
            legend += (
                f"\n\n_Footnote: Total time ({total_time:.1f}s) includes non-LLM overhead "
                f"(e.g., parsing, IO, prompt build). Per-stage durations sum to "
                f"{stage_sum_time:.1f}s; delta {delta:+.1f}s._"
            )
    except Exception:
        pass

    now_date = datetime.now().strftime('%Y-%m-%d')
    now_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    parts = []

    parts.append(f"# {project_name} - Complete C4 Architecture Documentation\n")
    parts.append("**Generated by Flowscribe**  \n")
    parts.append(f"**Date:** {now_date}  \n")
    parts.append(f"**Analysis Cost:** ${total_cost:.3f}  \n")
    parts.append(f"**Total Components (Deptrac):** {total_components}  \n")
    parts.append(f"**L4 Component Docs:** {l4_count}  \n")
    parts.append(f"**Architecture Grade:** {arch['grade']}\n\n")
    parts.append("---\n\n")

    parts.append("## 📋 Table of Contents\n\n")
    parts.append("1. [Quick Start](#quick-start)\n")
    parts.append("2. [Documentation Levels](#documentation-levels)\n")
    parts.append("3. [Architecture Overview](#architecture-overview)\n")
    parts.append("4. [C4 Level 1: System Context](#c4-level-1-system-context)\n")
    parts.append("5. [C4 Level 2: Containers](#c4-level-2-containers)\n")
    parts.append("6. [C4 Level 3: Components](#c4-level-3-components)\n")
    parts.append("7. [C4 Level 4: Code](#c4-level-4-code)\n")
    parts.append("8. [Architecture Review](#architecture-review)\n")
    parts.append("9. [Key Insights](#key-insights)\n")
    parts.append("10. [Refactoring Priorities](#refactoring-priorities)\n")
    parts.append("11. [How to Use This Documentation](#how-to-use-this-documentation)\n\n")
    parts.append("---\n\n")

    parts.append("## Quick Start\n\n")
    parts.append("**Path 1: High-Level Overview (5 minutes)**\n")
    parts.append("1. 📊 [C4 Level 1: System Context](./c4-level1.md) - Who uses it, what it connects to\n")
    parts.append("2. 🗄️ [C4 Level 2: Containers](./c4-level2.md) - Major architectural layers\n")
    parts.append("3. ⚡ Key insights below\n\n")
    parts.append("**Path 2: Architecture Deep Dive (30 minutes)**\n")
    parts.append("1. Start with Path 1 above\n")
    parts.append("2. 🔍 [C4 Level 3: Components](#c4-level-3-components) - Pick a layer to explore\n")
    parts.append("3. 💡 [C4 Level 4: Code Hub](./c4-level4.md) - Understand key components\n")
    parts.append("4. 📋 [Architecture Review](./architecture-review.md) - Expert assessment and recommendations\n\n")
    parts.append("**Path 3: Component-Focused**\n")
    parts.append("1. 📚 [C4 Level 4: Code Hub](./c4-level4.md)\n")
    parts.append("2. 🔬 Dive into specific component documentation\n")
    parts.append("3. 🔄 Trace back to L3 and L2 for context\n\n")
    parts.append("---\n\n")

    parts.append("## Documentation Levels\n\n")
    parts.append("| Level | Document | What It Shows | Audience | Status |\n")
    parts.append("|------:|----------|---------------|----------|--------|\n")
    parts.append(f"| **L1** | [System Context](./c4-level1.md) | Boundaries, users, externals | Everyone | {'✅' if docs['l1'] else '⚠️'} |\n")
    parts.append(f"| **L2** | [Containers](./c4-level2.md) | High-level architecture | Architects/Leads | {'✅' if docs['l2'] else '⚠️'} |\n")
    parts.append(f"| **L3** | [Components](#c4-level-3-components) | Components by layer | Devs/Architects | {'✅' if l3_count > 0 else '⚠️'} |\n")
    parts.append(f"| **L4** | [Code](./c4-level4.md) | Code-level design | Sr Devs/Architects | {'✅' if docs['l4_hub'] else '⚠️'} |\n")
    parts.append(f"| **Review** | [Architecture Review](./architecture-review.md) | Assessment + roadmap | Architects/Leads | {'✅' if docs['arch_review'] else '⚠️'} |\n\n")
    parts.append("---\n\n")

    parts.append("## Architecture Overview\n\n")
    parts.append("**Key Statistics**\n")
    parts.append(f"- **Architectural Layers:** {len(union_layers)}\n")
    parts.append(f"- **Total Components (Deptrac):** {total_components}\n")
    parts.append(f"- **L4 Component Docs:** {l4_count}\n")
    parts.append(f"- **Architectural Violations:** {violations}\n")
    if arch.get('uncovered_dependencies') is not None:
        parts.append(f"- **Uncovered dependencies:** {arch['uncovered_dependencies']}\n")
    parts.append(f"- **Architecture Grade:** {arch['grade']}\n")
    parts.append(f"- **Analysis Cost:** ${total_cost:.3f}\n")
    parts.append(f"- **Analysis Tokens:** {total_tokens:,}\n\n")

    parts.append("### Rich Layered Overview\n\n")
    parts.append(mermaid_md + "\n\n")

    parts.append("### Layers\n")
    parts.append("\n".join([f"- **{k}:** {union_layers[k]} components" for k in sorted(union_layers.keys(), key=lambda x: (-union_layers[x], x.lower()))]) or "_No layer data available_")
    parts.append("\n\n")

    parts.append("### Layer Documentation\n")
    parts.append("\n".join(l3_links) if l3_links else "_No L3 documents found yet_")
    parts.append("\n\n---\n\n")

    parts.append("## C4 Level 1: System Context\n")
    parts.append(f"📄 **[Open L1 →](./c4-level1.md)** {'✅' if docs['l1'] else '⚠️ Not found'}\n\n")
    parts.append("## C4 Level 2: Containers\n")
    parts.append(f"📄 **[Open L2 →](./c4-level2.md)** {'✅' if docs['l2'] else '⚠️ Not found'}\n\n")
    parts.append("## C4 Level 3: Components\n")
    parts.append(("_See layer links above_" if l3_links else "_No L3 documentation found_") + "\n\n")
    parts.append("## C4 Level 4: Code\n")
    parts.append(f"📄 **[Open L4 Hub →](./c4-level4.md)** {'✅' if docs['l4_hub'] else '⚠️ Not found'}\n\n")
    parts.append("---\n\n")

    parts.append("## Architecture Review\n")
    parts.append(f"📋 **[Open Review →](./architecture-review.md)** {'✅' if docs['arch_review'] else '⚠️ Not found'}\n\n")
    parts.append("### Executive Summary\n")
    parts.append(arch['executive_summary'] + "\n\n")
    parts.append(f"**Grade:** {arch['grade']}\n\n")
    parts.append("---\n\n")

    parts.append("## Analysis Metrics\n\n")
    parts.append(f"**Total Cost:** ${total_cost:.4f}  \n")
    parts.append(f"**Total Tokens:** {total_tokens:,}  \n")
    parts.append(f"**Total Time:** {total_time:.1f}s ({total_time/60:.1f} minutes)\n\n")

    parts.append("## 📊 Cost & Usage Summary\n\n")
    parts.append(cost_usage_md + "\n\n")
    parts.append(legend + "\n\n")
    parts.append("---\n\n")

    parts.append("## Files\n")
    parts.append("- `README.md` (this index)\n")
    parts.append("- `c4-level1.md`, `c4-level2.md`, `c4-level4.md`, `architecture-review.md`\n")
    parts.append("- `c4-level3-*.md` (per-layer components)\n")
    parts.append("- `.c4-level*-metrics.json`, `.architecture-review-metrics.json`, `.flowscribe-metrics.json`\n\n")
    parts.append(f"**Last Updated:** {now_dt}\n")

    return "".join(parts)


def main():
    ap = argparse.ArgumentParser(description="Generate master documentation index for C4 L1-L4")
    ap.add_argument("--project", "-p", default="Project", help='Project name (e.g., "Open Journal Systems")')
    ap.add_argument("--output", "-o", required=True, help="Output README.md path")
    args = ap.parse_args()

    # Security: Validate and resolve paths to prevent directory traversal
    try:
        output_path = Path(args.output).resolve()
    except (ValueError, OSError) as e:
        logger.error(f"✗ Error: Invalid path: {e}")
        raise SystemExit(1)

    # Security: Check for directory traversal attempts
    if '..' in Path(args.output).parts:
        logger.error("✗ Error: Invalid output path - directory traversal detected")
        raise SystemExit(1)

    # Update args with validated path
    args.output = str(output_path)

    logger.info("="*70)
    logger.info("Master Index Generator")
    logger.info("="*70)
    logger.info(f"Project: {args.project}")
    logger.info(f"Output : {args.output}\n")

    start = time.time()
    try:
        out_dir = output_path.parent
        md = generate_master_index(args.project, out_dir)
    except FileNotFoundError as e:
        logger.error(f"✗ Error: {e}")
        logger.error("\nEnsure architecture-review.md exists before generating master index.")
        logger.error("Run: export OPENROUTER_API_KEY=<key> && python3 c4-architecture-review.py --project <name> --domain <domain> --output-dir <dir>")
        raise SystemExit(1)
    except Exception as e:
        logger.error(f"✗ Error generating master index: {e}")
        raise SystemExit(1)

    try:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8")
        logger.info(f"✓ Generated: {out_path}")
    except Exception as e:
        logger.error(f"✗ Error writing output: {e}")
        raise SystemExit(1)

    elapsed = time.time() - start
    logger.info("\n" + "="*70)
    logger.info("✓ Master Index Created Successfully!")
    logger.info("="*70)
    logger.info(f"Project      : {args.project}")
    logger.info("Documentation: C4 L1, L2, L3, L4 + Architecture Review")
    logger.info(f"Time         : {elapsed:.1f}s")
    logger.info(f"\nOpen {out_path} to start exploring!\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
