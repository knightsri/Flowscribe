#!/usr/bin/env python3
"""
sanitize_output_files.py  (v5)
- Recursively scans an output directory
- Renames Markdown files (spaces → hyphens), rewrites internal links
- Sanitizes Mermaid diagrams (safe IDs, edges, quotes labels, graph→flowchart)
- Ensures each Markdown has YAML front matter so Jekyll applies the layout
- NEW: Optional conversion of ```mermaid fences into <div class="mermaid"> ... </div>

Usage:
  python3 sanitize_output_files.py --dir /workspace/output/WordPress
  python3 sanitize_output_files.py --dir /workspace/output --to-div   # convert fences to <div>
"""
from pathlib import Path
import argparse
import re
import sys
import shutil
import hashlib
from typing import Dict, List

def slugify_filename(name: str) -> str:
    p = Path(name)
    stem, ext = p.stem, p.suffix
    stem = stem.replace(" ", "-")
    stem = re.sub(r"[^A-Za-z0-9._-]", "-", stem)
    stem = re.sub(r"-{2,}", "-", stem).strip("-")
    return f"{stem}{ext}"

def find_markdown_files(output_dir: Path, recursive: bool = True) -> List[Path]:
    pattern = "**/*.md" if recursive else "*.md"
    return [p for p in output_dir.glob(pattern) if p.is_file()]

def build_rename_map(files: List[Path]) -> Dict[str, str]:
    mapping = {}
    for f in files:
        if any(ch in f.name for ch in [" ", "%20"]):
            new_name = slugify_filename(f.name)
            if new_name != f.name:
                mapping[f.name] = new_name
    return mapping

def apply_renames(files: List[Path], mapping: Dict[str, str]):
    by_dir: Dict[Path, List[Path]] = {}
    for f in files:
        by_dir.setdefault(f.parent, []).append(f)
    for folder, flist in by_dir.items():
        for src in flist:
            old = src.name
            if old not in mapping:
                continue
            new = mapping[old]
            dst = folder / new
            if dst.exists():
                shutil.move(str(dst), str(folder / (new + ".bak")))
            shutil.move(str(src), str(dst))

def rewrite_links_in_file(p: Path, mapping: Dict[str, str]) -> bool:
    text = p.read_text(encoding="utf-8", errors="ignore")
    before = text
    for old, new in mapping.items():
        patterns = [
            rf"\((\./)?{re.escape(old)}\)",
            rf"\((\./)?{re.escape(old.replace(' ', '%20'))}\)",
        ]
        for pat in patterns:
            text = re.sub(pat, f"({new})", text)
        text = text.replace(f"]({old})", f"]({new})")
        text = text.replace(f"](./{old})", f"]({new})")
    if text != before:
        p.write_text(text, encoding="utf-8")
        return True
    return False

def rewrite_links(files: List[Path], mapping: Dict[str, str]) -> int:
    count = 0
    if not mapping:
        return count
    for md in files:
        if rewrite_links_in_file(md, mapping):
            count += 1
    return count

# Mermaid normalization
def mermaid_safe_id(name: str) -> str:
    base = re.sub(r'[^A-Za-z0-9_]', '_', str(name or ''))
    if not base or base[0].isdigit():
        base = 'n_' + base
    return base

def quote_node_labels(line: str) -> str:
    # Square bracket
    def repl_square(m):
        before, openb, content, closeb = m.groups()
        c = content.strip()
        if len(c) >= 2 and ((c[0] == '"' and c[-1] == '"') or (c[0] == "'" and c[-1] == "'")):
            return f"{before}{openb}{content}{closeb}"
        c = c.replace('"', r'\"')
        return f'{before}{openb}"{c}"{closeb}'
    line = re.sub(r'^(\s*[A-Za-z0-9_]+)\s*(\[\s*)(.*?)(\s*\])', repl_square, line)

    # Round
    def repl_round(m):
        before, openp, content, closep = m.groups()
        c = content.strip()
        if len(c) >= 2 and ((c[0] == '"' and c[-1] == '"') or (c[0] == "'" and c[-1] == "'")):
            return f"{before}{openp}{content}{closep}"
        c = c.replace('"', r'\"')
        return f'{before}{openp}"{c}"{closep}'
    line = re.sub(r'^(\s*[A-Za-z0-9_]+)\s*(\(\s*)(.*?)(\s*\))', repl_round, line)
    return line

def normalize_mermaid_block(block: str) -> str:
    id_map: Dict[str, str] = {}
    used_ids = set()
    block = re.sub(r'^\s*graph\s+(TB|LR|RL|BT)\b', r'flowchart \1', block, flags=re.M)

    def unique_id(raw: str) -> str:
        if raw in id_map:
            return id_map[raw]
        sid = mermaid_safe_id(raw)
        if sid in used_ids:
            h = hashlib.md5(raw.encode("utf-8")).hexdigest()[:6]
            sid = f"{sid}_{h}"
        used_ids.add(sid)
        id_map[raw] = sid
        return sid

    out_lines = []
    for line in block.splitlines():
        m = re.match(r"\s*([A-Za-z0-9_.:-]+)\s*([\[\(])", line)
        if m:
            raw = m.group(1)
            safe = unique_id(raw)
            line = line.replace(raw + m.group(2), safe + m.group(2), 1)
        m2 = re.match(r"\s*([A-Za-z0-9_.:-]+)\s*([-\.]+>)\s*([A-Za-z0-9_.:-]+)", line)
        if m2:
            src_raw, arrow, dst_raw = m2.groups()
            src_safe = unique_id(src_raw)
            dst_safe = unique_id(dst_raw)
            line = re.sub(r"^\s*([A-Za-z0-9_.:-]+)", src_safe, line, count=1)
            line = re.sub(r"([-\.]+>\s*)([A-Za-z0-9_.:-]+)", r"\1" + dst_safe, line, count=1)
        line = quote_node_labels(line)
        out_lines.append(line)
    return "\n".join(out_lines)

def sanitize_mermaid_in_markdown_fences(text: str) -> str:
    def repl(m):
        block = m.group(1)
        fixed = normalize_mermaid_block(block)
        return f"```mermaid\n{fixed}\n```"
    return re.sub(r"```mermaid\s*\r?\n(.*?)```", repl, text, flags=re.S)

def convert_fences_to_divs(text: str) -> str:
    def repl(m):
        block = m.group(1).strip()
        return f'<div class="mermaid">\n{block}\n</div>'
    return re.sub(r"```mermaid\s*\r?\n(.*?)```", repl, text, flags=re.S)

def sanitize_mermaid_in_files(files: List[Path], to_div: bool = False) -> int:
    changed = 0
    for md in files:
        txt = md.read_text(encoding="utf-8", errors="ignore")
        fixed = sanitize_mermaid_in_markdown_fences(txt)
        if to_div:
            fixed = convert_fences_to_divs(fixed)
        if fixed != txt:
            md.write_text(fixed, encoding="utf-8")
            changed += 1
    return changed

# Front matter
def ensure_front_matter_for_file(md_path: Path) -> bool:
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    if text.lstrip().startswith("---"):
        return False
    m = re.search(r"^\s*#\s+(.+)$", text, flags=re.M)
    title = m.group(1).strip() if m else md_path.stem.replace("-", " ").title()
    fm = f"---\nlayout: default\ntitle: {title}\n---\n\n"
    md_path.write_text(fm + text, encoding="utf-8")
    return True

def ensure_front_matter(files: List[Path]) -> int:
    changed = 0
    for md in files:
        try:
            if ensure_front_matter_for_file(md):
                changed += 1
        except Exception:
            pass
    return changed

def sanitize_output_dir(output_dir: str, recursive: bool = True, to_div: bool = False) -> dict:
    od = Path(output_dir).resolve()  # Resolve to absolute path

    # Security: Prevent directory traversal attacks
    if not od.exists():
        raise FileNotFoundError(output_dir)

    # Security: Ensure path is absolute and doesn't contain parent directory references
    if '..' in od.parts:
        raise ValueError(f"Invalid path: directory traversal detected in {output_dir}")

    files = find_markdown_files(od, recursive=recursive)
    if not files:
        return {"renamed": 0, "mapping": {}, "link_rewrites": 0, "diagrams_sanitized": 0, "files_found": 0, "front_matter_added": 0}

    fm_changed = ensure_front_matter(files)
    mapping = build_rename_map(files)
    renamed = 0
    if mapping:
        apply_renames(files, mapping)
        renamed = len(mapping)
        files = find_markdown_files(od, recursive=recursive)

    rewrites = rewrite_links(files, mapping)
    diagrams_fixed = sanitize_mermaid_in_files(files, to_div=to_div)

    return {
        "files_found": len(files),
        "front_matter_added": fm_changed,
        "renamed": renamed,
        "mapping": mapping,
        "link_rewrites": rewrites,
        "diagrams_sanitized": diagrams_fixed,
    }

def main():
    ap = argparse.ArgumentParser(description="Sanitize Flowscribe output filenames, links, Mermaid diagrams, and add front matter for GitHub Pages.")
    ap.add_argument("--dir", required=True, help="Directory (e.g., /workspace/output/WordPress or /workspace/output)")
    ap.add_argument("--no-recursive", action="store_true", help="Do not recurse into subfolders")
    ap.add_argument("--to-div", action="store_true", help="Convert ```mermaid fences into <div class=\"mermaid\"> blocks")
    args = ap.parse_args()

    summary = sanitize_output_dir(args.dir, recursive=(not args.no_recursive), to_div=args.to_div)
    print("Sanitization Summary:")
    print(f"  Markdown files found: {summary['files_found']}")
    print(f"  Front matter added:   {summary['front_matter_added']} files")
    print(f"  Renamed files:        {summary['renamed']}")
    print(f"  Link rewrites:        {summary['link_rewrites']} files")
    print(f"  Mermaid sanitized:    {summary['diagrams_sanitized']} files")
    if summary['mapping']:
        print("  Mapping:")
        for k, v in summary['mapping'].items():
            print(f"    {k} -> {v}")

if __name__ == "__main__":
    sys.exit(main())
