#!/usr/bin/env python3
"""
C4 Level 2 (Containers) generator with integrated Violations Summary.

- Reads a Deptrac JSON report (supports both common shapes)
- Produces a Level 2 Markdown document (Mermaid) + a JSON sidecar for violations
- Emits canonical metrics v1.0 (no LLM): cost_usd=0, tokens=0, time from wall clock
"""

import json
import time
import argparse
from pathlib import Path
from datetime import datetime
import collections

SCHEMA_VERSION = "1.0"
LEVEL_KEY = "level2"

# -----------------------------
# Utilities
# -----------------------------

def format_duration(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s" if m else f"{s}s"


# -----------------------------
# Converter
# -----------------------------

class DeptracToC4Converter:
    LAYER_ORDER = [
        "Presentation", "API", "Application", "Domain",
        "Infrastructure", "Persistence", "BackgroundJobs"
    ]

    LAYER_DESCRIPTIONS = {
        "Presentation": "Handles HTTP requests, renders UI, manages user sessions",
        "API": "Provides RESTful API endpoints for external integrations",
        "Application": "Orchestrates business workflows and use cases",
        "Domain": "Business rules, entities, and domain services",
        "Infrastructure": "External services (mail, storage, cache) and adapters",
        "Persistence": "Database access, repositories, and mappers",
        "BackgroundJobs": "Queues, schedulers, and async workers",
    }

    def __init__(self, deptrac_json_path: str, project_name: str, model: str = "none"):
        self.project_name = project_name
        self.model = model
        self.violations = []
        self.layers = collections.defaultdict(set)  # layer -> set(class/file)
        self.dependencies = collections.Counter()   # (from_layer, to_layer) -> count
        self.violations_sidecar = None
        self._load(Path(deptrac_json_path))

    # -------- Deptrac parsing --------
    def _load(self, path: Path) -> None:
        obj = json.loads(path.read_text(encoding="utf-8"))
        # format 1: {"violations":[ ... {"rule": "...", "depender": {"layer": "...", "file": "...", "line": n}, "dependent": {"layer": "...", ...}} ]}
        if isinstance(obj, dict) and "violations" in obj and isinstance(obj["violations"], list):
            for v in obj["violations"]:
                rule = v.get("rule", "unknown")
                depender = v.get("depender", {}) or {}
                dependent = v.get("dependent", {}) or {}
                f_layer = depender.get("layer") or "Unknown"
                t_layer = dependent.get("layer") or "Unknown"
                f_file = depender.get("file") or ""
                f_line = depender.get("line")
                self.violations.append({
                    "rule": rule,
                    "from_layer": f_layer,
                    "to_layer": t_layer,
                    "file": f_file,
                    "line": f_line,
                })
                self.layers[f_layer].add(f_file or f_layer)
                self.layers[t_layer].add(dependent.get("file") or t_layer)
                self.dependencies[(f_layer, t_layer)] += 1

        # format 2: {"files": {"path.php": {"messages":[{"message":"... (A on B)", "rule":"...", "line":123, "dependency":{"depender":{"layer":"A"},"dependent":{"layer":"B"}}}]}}}
        files = obj.get("files")
        if isinstance(files, dict):
            for file_path, file_data in files.items():
                for m in file_data.get("messages", []):
                    rule = m.get("rule", "unknown")
                    dep = m.get("dependency") or {}
                    frm = dep.get("depender") or {}
                    to  = dep.get("dependent") or {}
                    f_layer = frm.get("layer")
                    t_layer = to.get("layer")
                    # If layers missing, try parse from message " (X on Y)"
                    if not (f_layer and t_layer):
                        msg = m.get("message") or ""
                        if "(" in msg and " on " in msg:
                            tail = msg.split("(")[-1].rstrip(")")
                            if " on " in tail:
                                f_layer, t_layer = [x.strip() for x in tail.split(" on ", 1)]
                    f_layer = f_layer or "Unknown"
                    t_layer = t_layer or "Unknown"
                    self.violations.append({
                        "rule": rule,
                        "from_layer": f_layer,
                        "to_layer": t_layer,
                        "file": file_path,
                        "line": m.get("line"),
                    })
                    self.layers[f_layer].add(file_path)
                    self.layers[t_layer].add(file_path)
                    self.dependencies[(f_layer, t_layer)] += 1

        # remove empty layers
        self.layers = {k: v for k, v in self.layers.items() if v}

    # -------- Violations aggregation --------
    def _iter_violations(self):
        for v in self.violations:
            yield {
                "from_layer": v.get("from_layer") or "Unknown",
                "to_layer": v.get("to_layer") or "Unknown",
                "rule": v.get("rule", "unknown"),
                "file": self._normalize_path(v.get("file", "")),
                "line": v.get("line"),
            }

    def _build_violation_summary(self, max_rows=100, max_files_per_cell=3):
        rows = list(self._iter_violations())
        by_pair = collections.Counter((r["from_layer"], r["to_layer"]) for r in rows)
        by_rule = collections.Counter(r["rule"] for r in rows)

        files_by_pair = collections.defaultdict(lambda: collections.Counter())
        for r in rows:
            if r["file"]:
                files_by_pair[(r["from_layer"], r["to_layer"])][r["file"]] += 1

        matrix = []
        for (frm, to), cnt in by_pair.most_common():
            topfiles = [f"{fn} ×{c}" for fn, c in files_by_pair[(frm, to)].most_common(max_files_per_cell)]
            matrix.append({"from": frm, "to": to, "count": cnt, "top_files": topfiles})

        sidecar = {
            "version": 1,
            "total": len(rows),
            "by_pair": [{"from": f, "to": t, "count": c} for (f, t), c in by_pair.most_common()],
            "by_rule": [{"rule": r, "count": c} for r, c in by_rule.most_common()],
            "hotspots": [
                {"file": fn, "from": f, "to": t, "count": c}
                for (f, t), files in files_by_pair.items()
                for fn, c in files.most_common()
            ],
        }

        # Markdown table
        header = "| From Layer | To Layer | Count | Top files (sample) |\n|---|---|---:|---|\n"
        rows_md = []
        for i, row in enumerate(matrix):
            if i >= max_rows:
                break
            rows_md.append(f"| {row['from']} | {row['to']} | {row['count']} | {', '.join(row['top_files'])} |")
        table_md = header + "\n".join(rows_md) if rows_md else "_No violations found._"

        summary = {
            "total": len(rows),
            "unique_pairs": len(by_pair),
            "by_rule": by_rule.most_common(10),
            "table_md": table_md,
            "sidecar": sidecar,
        }
        return summary

    def _render_violation_section(self, outdir: Path, max_rows=100, max_files_per_cell=3) -> str:
        outdir.mkdir(parents=True, exist_ok=True)
        summary = self._build_violation_summary(max_rows, max_files_per_cell)
        self.violations_sidecar = summary["sidecar"]
        # write sidecar now
        (outdir / "c4-level2-violations.json").write_text(json.dumps(self.violations_sidecar, indent=2), encoding="utf-8")

        total = summary["total"]
        pairs = summary["unique_pairs"]
        by_rule_line = ", ".join([f"{r} ×{c}" for r, c in summary["by_rule"]])
        md = []
        md.append("## Architectural Violations ⚠️")
        md.append(f"- **Total**: {total}  •  **Unique layer pairs**: {pairs}  •  **By rule (top)**: {by_rule_line}")
        if total > max_rows:
            md.append(f"_Showing top {max_rows} rows by count (of {total} total). See `c4-level2-violations.json` for the full index._")
        md.append("")
        md.append(summary["table_md"])
        md.append("")
        return "\n".join(md)

    # -------- Outputs --------
    def generate_mermaid(self) -> str:
        mermaid = ["```mermaid", "graph TB", ""]
        mermaid.append("    %% External Actors")
        mermaid.append("    User[User]")
        mermaid.append("")
        mermaid.append(f"    %% {self.project_name}")
        mermaid.append(f'    subgraph System["{self.project_name}"]')

        for layer_name in self.LAYER_ORDER:
            if layer_name in self.layers:
                class_count = len(self.layers[layer_name])
                desc = self.LAYER_DESCRIPTIONS.get(layer_name, f"{class_count} classes")
                mermaid.append(f'        {layer_name}["{layer_name}<br/>{desc}"]')

        mermaid.append("    end")
        mermaid.append("")
        mermaid.append("    %% Internal Dependencies (from Deptrac)")
        added = set()
        for (frm, to), cnt in self.dependencies.items():
            if (frm, to) not in added and frm in self.layers and to in self.layers:
                mermaid.append(f"    {frm} -->|{cnt} refs| {to}")
                added.add((frm, to))

        mermaid.append("```")
        return "\n".join(mermaid)

    def _normalize_path(self, path_str: str) -> str:
        """
        Trim machine-local prefixes (like /workspace/projects/) from file paths.
        Keeps only the part starting from the repo name onward.
        """
        if not path_str:
            return path_str
        # Generic cleanup: strip /workspace/projects/, /home/..., or similar
        path_str = path_str.replace("\\", "/")
        if "/workspace/projects/" in path_str:
            path_str = path_str.split("/workspace/projects/")[-1]
        elif "/projects/" in path_str:
            path_str = path_str.split("/projects/")[-1]
        # Optional: remove leading slashes
        return path_str.lstrip("/")

    def generate_markdown_report(self, outdir: Path, max_rows=100, max_files_per_cell=3) -> str:
        doc = []
        doc.append(f"# {self.project_name} - C4 Level 2: Container Architecture")
        doc.append("")
        doc.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
        doc.append(f"**Source:** Deptrac dependency analysis  ")
        doc.append("**Diagram Level:** C4 Level 2 (Containers)")
        doc.append("")
        doc.append("---")
        doc.append("")
        doc.append("## Container Diagram")
        doc.append("")
        doc.append(self.generate_mermaid())
        doc.append("")
        doc.append("---")
        doc.append("")
        # Violations summary (with sidecar)
        doc.append(self._render_violation_section(outdir, max_rows=max_rows, max_files_per_cell=max_files_per_cell))
        doc.append("")
        doc.append("---")
        doc.append("")
        doc.append("## Next Steps")
        doc.append("1. **Review L3 (Component View)** - Detailed component analysis per layer")
        doc.append("2. **Address Violations** - Fix architectural rule violations")
        doc.append("3. **Refactor** - Improve layer separation based on findings")
        doc.append("4. **Document** - Keep architecture documentation updated")
        doc.append("")
        doc.append("*Generated by Flowscribe - Automated C4 Architecture Documentation*")
        return "\n".join(doc)


# -----------------------------
# CLI
# -----------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate C4 Level 2 (Containers) from Deptrac analysis")
    parser.add_argument("deptrac_json", help="Path to deptrac-report.json")
    parser.add_argument("--project", required=True, help='Project name (e.g., "WordPress")')
    parser.add_argument("--output", "-o", required=True, help="Markdown output path")
    parser.add_argument("--model", default="none", help="Model name for metrics (default: none, since no LLM used)")
    parser.add_argument("--max-violations-table", type=int, default=100, help="Max rows in the violations table")
    parser.add_argument("--max-files-per-cell", type=int, default=3, help="Max file samples per table cell")
    args = parser.parse_args()

    if not Path(args.deptrac_json).exists():
        print(f"✗ Error: Deptrac report not found: {args.deptrac_json}")
        return 1

    print("Step 1: Loading and parsing Deptrac report...")
    t0 = time.time()
    converter = DeptracToC4Converter(args.deptrac_json, args.project, args.model)
    parse_time = time.time() - t0
    print(f"✓ Parsed in {format_duration(parse_time)}")

    print("Step 2: Generating markdown...")
    t1 = time.time()
    out_path = Path(args.output)
    outdir = out_path.parent
    outdir.mkdir(parents=True, exist_ok=True)
    markdown = converter.generate_markdown_report(outdir, args.max_violations_table, args.max_files_per_cell)
    gen_time = time.time() - t1
    print(f"✓ Generated in {format_duration(gen_time)}")

    print("Step 3: Writing output...")
    out_path.write_text(markdown, encoding="utf-8")
    print(f"✓ Written to {out_path}")

    # Canonical metrics (no LLM usage here)
    total_time = round(parse_time + gen_time, 3)
    metrics = {
        "version": SCHEMA_VERSION,
        "repo": {
            "name": args.project,
            "analysis_utc": datetime.utcnow().isoformat() + "Z"
        },
        "levels": {
            LEVEL_KEY: {
                "cost_usd": 0.0,
                "time_seconds": total_time,
                "tokens_in": 0,
                "tokens_out": 0,
                "model": "none"
            }
        },
        "totals": {
            "cost_usd": 0.0,
            "time_seconds": total_time,
            "tokens_in": 0,
            "tokens_out": 0
        },
        # Legacy block for backward compatibility with earlier analyzers
        "legacy": {
            "model": "none",
            "total_cost_usd": 0.0,
            "total_time_seconds": total_time,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
    }
    (outdir / ".c4-level2-metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"✓ Metrics (v{SCHEMA_VERSION}) saved to {outdir / '.c4-level2-metrics.json'}")

    print("All done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
