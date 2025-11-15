#!/usr/bin/env python3
"""
C4 Level 1 (System Context) Generator — Metrics v1.0

- Reads key project files for context
- Calls LLM (OpenRouter) to produce structured JSON describing System Context
- Renders a Level 1 markdown document
- Writes canonical metrics (v1.0) using OpenRouter usage-first costing
"""

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path
import json

# Import shared utilities
from flowscribe_utils import LLMClient, CostTracker, parse_llm_json, format_cost, format_duration

LEVEL_KEY = "level1"
SCHEMA_VERSION = "1.0"


def read_project_files(project_dir, max_file_size=50000):
    """Read relevant project files for context analysis

    Args:
        project_dir: Path to project directory (validated for security)
        max_file_size: Maximum file size to read

    Returns:
        Dictionary of filename -> content
    """
    files_content = {}

    target_patterns = [
        'readme.*',
        'composer.json',
        'package.json',
        'requirements.txt',
        'Gemfile',
        'go.mod',
        'docker-compose.y*ml',
        'Dockerfile',
        'Dockerfile.*',
        '.env.example',
        '.env.sample',
        'config.example.php',
        'wp-config-sample.php',
        'config/app.php',
        'app.config.js',
    ]

    # Security: Use resolved absolute path (already validated in main)
    project_path = Path(project_dir).resolve()

    for pattern in target_patterns:
        for filepath in project_path.glob(pattern):
            if filepath.is_file():
                try:
                    txt = filepath.read_text(encoding='utf-8', errors='ignore')
                    if len(txt) > max_file_size:
                        txt = txt[:max_file_size] + "\n... [truncated]"
                    files_content[filepath.name] = txt
                    print(f"✓ Read {filepath.name} ({len(txt)} chars)")
                except Exception as e:
                    print(f"✗ Error reading {filepath.name}: {e}")

    # Additional docs
    docs_dir = project_path / 'docs'
    if docs_dir.exists():
        for doc_file in docs_dir.glob('*.md'):
            if doc_file.name.lower() in ['architecture.md', 'overview.md', 'introduction.md']:
                try:
                    txt = doc_file.read_text(encoding='utf-8', errors='ignore')
                    if len(txt) > max_file_size:
                        txt = txt[:max_file_size] + "\n... [truncated]"
                    files_content[f'docs/{doc_file.name}'] = txt
                    print(f"✓ Read docs/{doc_file.name} ({len(txt)} chars)")
                except Exception as e:
                    print(f"✗ Error reading docs/{doc_file.name}: {e}")

    return files_content


def build_analysis_prompt(project_name, domain, files_content):
    """Build the LLM prompt for system context analysis"""
    files_section = ""
    for filename, content in files_content.items():
        files_section += f"\n### File: {filename}\n```\n{content}\n```\n"

    return f"""You are a software architect analyzing the **{project_name}** project in the **{domain}** domain.

Your task is to create a C4 Level 1 (System Context) diagram by analyzing the project files provided below.

## C4 Level 1 Requirements

A System Context diagram shows:
1. **The System** - The software system being documented
2. **Users/Actors** - Who uses the system (personas, user types, roles)
3. **External Systems** - What external systems/services it integrates with
4. **Relationships** - How users and external systems interact with the main system

## Project Files
{files_section}

## Your Task

Analyze these files and provide a structured JSON response with the following:

{{
  "system_description": "Brief description (2-3 sentences)",
  "system_purpose": "The main purpose (1 sentence)",
  "users": [
    {{
      "name": "User Type Name",
      "description": "What this user does with the system",
      "primary_actions": ["action1", "action2", "action3"]
    }}
  ],
  "external_systems": [
    {{
      "name": "External System Name",
      "purpose": "Why the system integrates with this",
      "integration_type": "API/Database/File/Protocol/etc",
      "data_flow": "What data is exchanged"
    }}
  ],
  "key_features": [
    "Feature 1",
    "Feature 2",
    "Feature 3"
  ]
}}

Provide ONLY the JSON response, no additional text.
"""


def generate_markdown(project_name, domain, analysis_json_text):
    """Generate C4 Level 1 markdown from LLM analysis"""
    data = parse_llm_json(analysis_json_text)
    if not data:
        print("✗ Error: Failed to parse LLM JSON response")
        print(f"Response preview: {analysis_json_text[:500]}")
        return None

    required_fields = ['system_description', 'system_purpose', 'users', 'external_systems']
    for f in required_fields:
        data.setdefault(f, [] if f.endswith('s') else 'N/A')
    data.setdefault('key_features', [])

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md = []
    md.append(f"# {project_name} - C4 Level 1: System Context\n")
    md.append(f"\n**Generated:** {timestamp}  ")
    md.append(f"\n**Domain:** {domain}  ")
    md.append("\n**Diagram Level:** C4 Level 1 (System Context)\n")
    md.append("\n---\n\n## System Overview\n")
    md.append("\n### Description\n")
    md.append(f"{data.get('system_description','N/A')}\n")
    md.append("\n### Purpose\n")
    md.append(f"{data.get('system_purpose','N/A')}\n")
    md.append("\n### Key Features\n")
    for feat in data.get('key_features', []):
        md.append(f"- {feat}\n")

    md.append("\n---\n\n## Users and Actors\n\n")
    users = data.get('users', [])
    if users:
        for user in users:
            md.append(f"### {user.get('name','Unknown')}\n\n")
            md.append(f"**Role:** {user.get('description','N/A')}\n\n")
            md.append("**Primary Actions:**\n")
            for act in user.get('primary_actions', []):
                md.append(f"- {act}\n")
            md.append("\n")
    else:
        md.append("*No users identified in the analysis*\n\n")

    md.append("---\n\n## External Systems and Integrations\n\n")
    exts = data.get('external_systems', [])
    if exts:
        for s in exts:
            md.append(f"### {s.get('name','Unknown')}\n\n")
            md.append(f"**Purpose:** {s.get('purpose','N/A')}\n\n")
            md.append(f"**Integration Type:** {s.get('integration_type','N/A')}\n\n")
            md.append(f"**Data Flow:** {s.get('data_flow','N/A')}\n\n")
    else:
        md.append("*No external systems identified in the analysis*\n\n")

    # Mermaid diagram
    md.append("""---

## System Context Diagram
```mermaid
graph TB
""")
    # Nodes
    md.append("    User[👤 Users<br/>Various user types]\n")
    system_label = f'{project_name}<br/>{data.get("system_purpose","Main system")}'
    md.append(f'    System["🏛️ {system_label}"]\n')
    # External systems (cap at 5)
    for i, ext in enumerate(exts[:5]):
        sid = f"Ext{i}"
        ext_label = f'{ext.get("name","External")}<br/>{ext.get("purpose","External system")}'
        md.append(f'    {sid}["🔗 {ext_label}"]\n')
    # Edges
    md.append("    User -->|Uses| System\n")
    for i, ext in enumerate(exts[:5]):
        sid = f"Ext{i}"
        integ = ext.get("integration_type","Integrates")
        md.append(f"    System -->|{integ}| {sid}\n")
    md.append("```\n")
    return "".join(md)


def _extract_usage_calls_from_result(result, default_model):
    """Return calls[] using OpenRouter usage when available."""
    calls = []
    if not isinstance(result, dict):
        return calls
    usage = result.get('usage')
    if isinstance(usage, dict):
        calls.append({
            "id": result.get("id") or result.get("generation_id"),
            "model": result.get("model") or default_model,
            "cost_usd": float(usage.get("cost", 0.0) or 0.0),
            "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
            "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
            "total_tokens": int(usage.get("total_tokens", (int(usage.get("prompt_tokens", 0) or 0) + int(usage.get("completion_tokens", 0) or 0)))),
            "cached_prompt_tokens": int((usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0) or 0),
            "reasoning_tokens": int((usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0) or 0),
            "started_at": result.get("started_at"),
            "finished_at": result.get("finished_at"),
        })
        return calls
    if isinstance(result.get("calls"), list):
        for c in result["calls"]:
            u = c.get("usage") or {}
            calls.append({
                "id": c.get("id") or c.get("request_id"),
                "model": c.get("model", default_model),
                "cost_usd": float(c.get("cost_usd") or u.get("cost", 0.0) or 0.0),
                "prompt_tokens": int(c.get("prompt_tokens") or u.get("prompt_tokens", 0) or 0),
                "completion_tokens": int(c.get("completion_tokens") or u.get("completion_tokens", 0) or 0),
                "total_tokens": int(c.get("total_tokens") or u.get("total_tokens", 0) or (int(c.get("prompt_tokens") or 0) + int(c.get("completion_tokens") or 0))),
                "cached_prompt_tokens": int((u.get("prompt_tokens_details") or {}).get("cached_tokens", 0) or 0),
                "reasoning_tokens": int((u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0) or 0),
                "started_at": c.get("started_at") or c.get("start_time"),
                "finished_at": c.get("finished_at") or c.get("end_time"),
            })
        return calls
    calls.append({
        "id": result.get("id"),
        "model": result.get("model") or default_model,
        "cost_usd": float(result.get("cost", 0.0) or 0.0),
        "prompt_tokens": int(result.get("input_tokens", 0) or 0),
        "completion_tokens": int(result.get("output_tokens", 0) or 0),
        "total_tokens": int(result.get("total_tokens", (int(result.get("input_tokens", 0) or 0) + int(result.get("output_tokens", 0) or 0)))),
        "cached_prompt_tokens": 0,
        "reasoning_tokens": 0,
        "started_at": result.get("started_at"),
        "finished_at": result.get("finished_at"),
    })
    return calls


def main():
    parser = argparse.ArgumentParser(description='Generate C4 Level 1 (System Context) documentation')
    parser.add_argument('project_dir', help='Path to the project directory')
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--domain', required=True, help='Project domain')
    parser.add_argument('--api-key', default=os.environ.get('OPENROUTER_API_KEY'), help='OpenRouter API key')
    parser.add_argument('--model', default=os.environ.get('OPENROUTER_MODEL', 'anthropic/claude-sonnet-4.5'), help='Model to use')
    parser.add_argument('--output', required=True, help='Output markdown file path')
    parser.add_argument('--max-file-size', type=int, default=50000, help='Max file size to read')
    args = parser.parse_args()

    if not args.api_key:
        print("✗ Error: OpenRouter API key required (--api-key or OPENROUTER_API_KEY)")
        sys.exit(1)

    # Security: Validate and resolve paths to prevent directory traversal
    try:
        project_dir = Path(args.project_dir).resolve()
        output_path = Path(args.output).resolve()
    except (ValueError, OSError) as e:
        print(f"✗ Error: Invalid path: {e}")
        sys.exit(1)

    # Security: Check for directory traversal attempts
    if '..' in Path(args.project_dir).parts:
        print("✗ Error: Invalid project directory - directory traversal detected")
        sys.exit(1)

    if '..' in Path(args.output).parts:
        print("✗ Error: Invalid output path - directory traversal detected")
        sys.exit(1)

    # Check project directory exists
    if not project_dir.exists():
        print(f"✗ Error: Project directory not found: {project_dir}")
        sys.exit(1)

    # Update args with validated paths
    args.project_dir = str(project_dir)
    args.output = str(output_path)

    print("\n" + "="*60)
    print("C4 Level 1 Generator - System Context Analysis")
    print("="*60 + "\n")
    print(f"Project: {args.project}")
    print(f"Domain: {args.domain}")
    print(f"Model: {args.model}")
    print(f"Project Directory: {args.project_dir}")
    print(f"Output: {args.output}\n")

    tracker = CostTracker(args.model)
    llm = LLMClient(args.api_key, args.model, tracker)

    # Step 1: Read project files
    print("Step 1: Reading project files...")
    files_content = read_project_files(args.project_dir, args.max_file_size)
    if not files_content:
        print("✗ Error: No relevant project files found")
        sys.exit(1)
    print(f"✓ Found {len(files_content)} relevant files\n")

    # Step 2: Build prompt
    print("Step 2: Building analysis prompt...")
    prompt = build_analysis_prompt(args.project, args.domain, files_content)
    print(f"✓ Prompt ready ({len(prompt)} chars)\n")

    # Step 3: Call LLM
    print("Step 3: Analyzing with LLM...\n")
    t0 = time.time()
    result = llm.call(prompt)
    duration = time.time() - t0

    if not result:
        print("✗ Error: LLM analysis failed")
        sys.exit(1)

    print("✓ Analysis complete")
    print(f"  Cost: {format_cost(result['cost'])}")
    print(f"  Time: {format_duration(result['duration'])}")
    print(f"  Tokens: {result['total_tokens']:,} ({result['input_tokens']:,} in / {result['output_tokens']:,} out)\n")

    # Step 4: Generate markdown
    print("Step 4: Generating C4 Level 1 markdown...")
    markdown = generate_markdown(args.project, args.domain, result['content'])
    if not markdown:
        print("✗ Error: Failed to generate markdown")
        sys.exit(1)

    # Step 5: Write output
    print("Step 5: Writing output file...")
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding='utf-8')
    print(f"✓ Written to {args.output}\n")

    # Print tracker summary (optional)
    tracker.print_summary()

    # Canonical metrics v1.0 (usage-first)
    calls = _extract_usage_calls_from_result(result, default_model=args.model)
    cost_usd = sum(c.get("cost_usd", 0.0) for c in calls)
    tokens_in = sum(c.get("prompt_tokens", 0) for c in calls) or int(result.get("input_tokens", 0) or 0)
    tokens_out = sum(c.get("completion_tokens", 0) for c in calls) or int(result.get("output_tokens", 0) or 0)
    model_used = result.get("model") or args.model
    duration = float(result.get("duration", 0.0) or 0.0)

    metrics = {
        "version": SCHEMA_VERSION,
        "repo": { "name": args.project, "analysis_utc": datetime.utcnow().isoformat() + "Z" },
        "levels": {
            LEVEL_KEY: {
                "cost_usd": round(float(cost_usd if cost_usd else result.get("cost", 0.0)), 6),
                "time_seconds": round(duration, 3),
                "tokens_in": int(tokens_in),
                "tokens_out": int(tokens_out),
                "model": model_used or "none",
                "calls": calls
            }
        },
        "totals": {
            "cost_usd": round(float(cost_usd if cost_usd else result.get("cost", 0.0)), 6),
            "time_seconds": round(duration, 3),
            "tokens_in": int(tokens_in),
            "tokens_out": int(tokens_out)
        },
        "legacy": {
            "model": args.model,
            "duration_seconds": duration,
            "input_tokens": int(result.get("input_tokens", tokens_in)),
            "output_tokens": int(result.get("output_tokens", tokens_out)),
            "total_tokens": int(result.get("total_tokens", (tokens_in + tokens_out))),
            "cost_usd": float(result.get("cost", cost_usd))
        }
    }
    metrics_path = out_path.parent / '.c4-level1-metrics.json'
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    print(f"✓ Metrics saved to {metrics_path}")

    print("\n" + "="*60)
    print("✓ C4 Level 1 documentation generated successfully!")
    print("="*60 + "\n")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
