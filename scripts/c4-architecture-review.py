#!/usr/bin/env python3
"""
C4 Architecture Review Generator (Metrics v1.0)

- Generates an architectural review from C4 docs using an LLM.
- Emits canonical metrics JSON (version 1.0):
  repo{name,url?,commit_sha?,deptrac_config_sha256?,analysis_utc}, levels{architecture_review{...}}, totals{...}
- Source of truth for cost: OpenRouter `usage.cost` (if available); otherwise falls back to provided cost.

Usage:
    # Set API key via environment variable
    export OPENROUTER_API_KEY=<your-key>

    python3 c4-architecture-review.py \
        --project "WordPress" \
        --domain "content management" \
        --output-dir /workspace/output/WordPress \
        --model anthropic/claude-sonnet-4-5-20241022
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Import shared utilities
from flowscribe_utils import LLMClient, CostTracker, format_cost, format_duration
from logger import setup_logger

logger = setup_logger(__name__)

LEVEL_KEY = "architecture_review"
SCHEMA_VERSION = "1.0"

def read_c4_documentation(output_dir):
    """Read all generated C4 documentation files

    Args:
        output_dir: Path to output directory (validated for security)

    Returns:
        Dictionary of documentation files and content
    """
    # Security: Use resolved absolute path (already validated in main)
    output_path = Path(output_dir).resolve()
    docs = {}
    
    # Files to read
    # Level 3 is a set of files matched by glob
    level1 = output_path / 'c4-level1.md'
    if level1.exists():
        with open(level1, 'r', encoding='utf-8') as f:
            docs['level1'] = f.read()
    
    level2 = output_path / 'c4-level2.md'
    if level2.exists():
        with open(level2, 'r', encoding='utf-8') as f:
            docs['level2'] = f.read()
    
    docs['level3_layers'] = []
    for level3_file in output_path.glob('c4-level3-*.md'):
        with open(level3_file, 'r', encoding='utf-8') as f:
            docs['level3_layers'].append({
                'file': level3_file.name,
                'content': f.read()
            })
    
    level4 = output_path / 'c4-level4.md'
    if level4.exists():
        with open(level4, 'r', encoding='utf-8') as f:
            docs['level4'] = f.read()
    
    return docs


def read_deptrac_report(output_dir):
    """Read deptrac analysis report (optional)"""
    report_path = Path(output_dir) / 'deptrac-report.json'
    if not report_path.exists():
        return None
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def build_review_prompt(project_name, domain, docs, deptrac_report, model):
    """Build comprehensive architectural review prompt"""
    # Extract violation summary from deptrac (best-effort)
    violation_summary = "No Deptrac data available"
    if deptrac_report:
        report_data = deptrac_report.get('Report', {})
        violation_summary = f"""
Violation Summary:
- Total Violations: {report_data.get('Violations', 0)}
- Skipped Violations: {report_data.get('Skipped violations', 0)}
- Uncovered Dependencies: {report_data.get('Uncovered', 0)}
- Allowed Dependencies: {report_data.get('Allowed', 0)}
- Warnings: {report_data.get('Warnings', 0)}
- Errors: {report_data.get('Errors', 0)}
"""
    # Build the prompt
    prompt = f"""You are a Senior Software Architect with 20+ years of experience. Conduct a thorough architectural review of this software project.

PROJECT INFORMATION:
- Name: {project_name}
- Domain: {domain}
- Analysis Date: {datetime.now().strftime('%Y-%m-%d')}

AVAILABLE DOCUMENTATION:
Below are the complete C4 architecture diagrams (Levels 1-4) and dependency analysis for this project.

═══════════════════════════════════════════════════════════════════
C4 LEVEL 1: SYSTEM CONTEXT
═══════════════════════════════════════════════════════════════════

{docs.get('level1', 'Not available')}

═══════════════════════════════════════════════════════════════════
C4 LEVEL 2: CONTAINER ARCHITECTURE
═══════════════════════════════════════════════════════════════════

{docs.get('level2', 'Not available')}

═══════════════════════════════════════════════════════════════════
C4 LEVEL 3: COMPONENT DETAILS
═══════════════════════════════════════════════════════════════════
"""
    for layer_doc in docs.get('level3_layers', []):
        prompt += f"\n--- {layer_doc['file']} ---\n"
        prompt += layer_doc['content']
        prompt += "\n"
    prompt += f"""
═══════════════════════════════════════════════════════════════════
C4 LEVEL 4: CODE ANALYSIS
═══════════════════════════════════════════════════════════════════

{docs.get('level4', 'Not available')}

═══════════════════════════════════════════════════════════════════
DEPENDENCY ANALYSIS
═══════════════════════════════════════════════════════════════════

{violation_summary}

═══════════════════════════════════════════════════════════════════
YOUR TASK: ARCHITECTURAL REVIEW
═══════════════════════════════════════════════════════════════════

Provide a comprehensive, critical, and constructive architectural review. Be honest and direct about issues, but always provide actionable recommendations.

Structure your review as follows:

# Architectural Review: {project_name}

**Reviewed:** {datetime.now().strftime('%B %d, %Y')}  
**Review Model:** {model}  
**Reviewer:** Senior Software Architect (AI)  
**Overall Grade:** [A/B/C/D/F]

## Executive Summary
[2-3 paragraph overview]

## 1. Architecture Pattern Assessment (Grade: ?)
...

## 2. Layer Design Quality (Grade: ?)
...

## 3. Component Organization (Grade: ?)
...

## 4. Technical Debt Assessment
...

## 5. Refactoring Roadmap
...

## 6. Overall Assessment
...
"""
    return prompt


def _extract_usage_calls(result, default_model):
    """
    Build calls[] from the LLM result, preferring OpenRouter usage fields.
    Expected shapes (best-effort):
      - result['usage'] = { cost, prompt_tokens, completion_tokens, total_tokens, ... }
      - result['calls'] = [ {...} ]
      - fallback to single-call using {cost, input_tokens, output_tokens, total_tokens}
    """
    calls = []
    # Direct OpenRouter-style single usage object
    usage = result.get('usage') if isinstance(result, dict) else None
    if isinstance(usage, dict):
        calls.append({
            "id": result.get("id"),
            "model": result.get("model", default_model),
            "cost_usd": float(usage.get("cost", 0.0)),
            "prompt_tokens": int(usage.get("prompt_tokens", 0)),
            "completion_tokens": int(usage.get("completion_tokens", 0)),
            "total_tokens": int(usage.get("total_tokens", 0)),
            "cached_prompt_tokens": int((usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)),
            "reasoning_tokens": int((usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)),
            "started_at": result.get("started_at"),
            "finished_at": result.get("finished_at"),
        })
        return calls

    # Pre-collected list of calls (already usage-first)
    if isinstance(result.get("calls"), list):
        for c in result["calls"]:
            calls.append({
                "id": c.get("id") or c.get("request_id"),
                "model": c.get("model", default_model),
                "cost_usd": float(c.get("cost_usd") or (c.get("usage") or {}).get("cost", 0.0)),
                "prompt_tokens": int(c.get("prompt_tokens") or (c.get("usage") or {}).get("prompt_tokens", 0)),
                "completion_tokens": int(c.get("completion_tokens") or (c.get("usage") or {}).get("completion_tokens", 0)),
                "total_tokens": int(c.get("total_tokens") or (c.get("usage") or {}).get("total_tokens", 0)),
                "cached_prompt_tokens": int((c.get("usage") or {}).get("prompt_tokens_details", {}).get("cached_tokens", 0)),
                "reasoning_tokens": int((c.get("usage") or {}).get("completion_tokens_details", {}).get("reasoning_tokens", 0)),
                "started_at": c.get("started_at") or c.get("start_time"),
                "finished_at": c.get("finished_at") or c.get("end_time"),
            })
        return calls

    # Fallback — single call using aggregate fields
    calls.append({
        "id": result.get("id"),
        "model": result.get("model", default_model),
        "cost_usd": float(result.get("cost", 0.0)),
        "prompt_tokens": int(result.get("input_tokens", 0)),
        "completion_tokens": int(result.get("output_tokens", 0)),
        "total_tokens": int(result.get("total_tokens", (result.get("input_tokens", 0) + result.get("output_tokens", 0)))),
        "cached_prompt_tokens": 0,
        "reasoning_tokens": 0,
        "started_at": None,
        "finished_at": None,
    })
    return calls


def generate_review(project_name, domain, output_dir, api_key, model):
    """Generate architectural review and canonical metrics"""
    logger.info("="*70)
    logger.info("C4 Architecture Review Generator")
    logger.info("="*70)
    logger.info(f"Project: {project_name}")
    logger.info(f"Domain: {domain}")
    logger.info(f"Model: {model}")
    logger.info(f"Output Directory: {output_dir}")
    logger.info("")

    # Step 1: Read documentation
    logger.info("Step 1: Reading generated C4 documentation...")
    docs = read_c4_documentation(output_dir)
    doc_count = (1 if docs.get('level1') else 0) + (1 if docs.get('level2') else 0) + len(docs.get('level3_layers', [])) + (1 if docs.get('level4') else 0)
    if doc_count == 0:
        logger.error("✗ Error: No C4 documentation found")
        return None
    logger.info(f"✓ Found {doc_count} documentation files\n")

    # Step 2: Deptrac report (optional)
    logger.info("Step 2: Reading dependency analysis...")
    deptrac_report = read_deptrac_report(output_dir)
    logger.info("✓ Deptrac report loaded\n" if deptrac_report else "⚠ No deptrac report found (review will be limited)\n")

    # Step 3: Build prompt
    logger.info("Step 3: Building architectural review prompt...")
    prompt = build_review_prompt(project_name, domain, docs, deptrac_report, model)
    logger.info(f"✓ Prompt ready ({len(prompt):,} characters)\n")

    # Step 4: Call LLM
    logger.info("Step 4: Generating architectural review with premium model...\n")
    tracker = CostTracker(model)
    llm = LLMClient(api_key, model, tracker)
    t0 = time.time()
    result = llm.call(prompt)
    duration = time.time() - t0
    if not result:
        logger.error("✗ Error: Failed to generate review")
        return None

    review_content = result.get('content', '')
    logger.info("✓ Review generated")
    # Prefer usage.cost if available
    calls = _extract_usage_calls(result, default_model=model)
    cost_usd = sum(c.get("cost_usd", 0.0) for c in calls)
    tokens_in = sum(c.get("prompt_tokens", 0) for c in calls)
    tokens_out = sum(c.get("completion_tokens", 0) for c in calls)
    total_tokens = sum(c.get("total_tokens", 0) for c in calls) or (tokens_in + tokens_out)
    logger.info(f"  Cost: {format_cost(cost_usd)}")
    logger.info(f"  Time: {format_duration(duration)}")
    logger.info(f"  Tokens: in={tokens_in:,}, out={tokens_out:,}, total={total_tokens:,}")
    logger.info(f"  Output: {len(review_content):,} characters\n")

    # Step 5: Save review
    logger.info("Step 5: Saving architectural review...")
    output_file = Path(output_dir) / 'architecture-review.md'
    output_file.write_text(review_content, encoding='utf-8')
    logger.info(f"✓ Saved to: {output_file}\n")

    # Step 6: Save canonical metrics (v1.0)
    logger.info("Step 6: Writing metrics (v1.0)...")
    metrics = {
        "version": SCHEMA_VERSION,
        "repo": {
            "name": project_name,
            "analysis_utc": datetime.utcnow().isoformat() + "Z"
        },
        "levels": {
            LEVEL_KEY: {
                "cost_usd": round(float(cost_usd), 6),
                "time_seconds": round(float(duration), 3),
                "tokens_in": int(tokens_in),
                "tokens_out": int(tokens_out),
                "model": model or "none",
                "calls": calls
            }
        },
        "totals": {
            "cost_usd": round(float(cost_usd), 6),
            "time_seconds": round(float(duration), 3),
            "tokens_in": int(tokens_in),
            "tokens_out": int(tokens_out)
        },
        # Legacy block for backward compatibility (optional)
        "legacy": {
            "project": project_name,
            "domain": domain,
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "cost_usd": float(result.get("cost", cost_usd)),
            "duration_seconds": float(duration),
            "input_tokens": int(result.get("input_tokens", tokens_in)),
            "output_tokens": int(result.get("output_tokens", tokens_out)),
            "total_tokens": int(result.get("total_tokens", total_tokens))
        }
    }
    metrics_file = Path(output_dir) / '.architecture-review-metrics.json'
    metrics_file.write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    logger.info(f"✓ Metrics saved to: {metrics_file}")

    return metrics


def main():
    parser = argparse.ArgumentParser(
        description='Generate architectural review from C4 documentation',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--domain', required=True, help='Project domain')
    parser.add_argument('--output-dir', required=True, help='Output directory with C4 docs')
    parser.add_argument(
        '--model',
        default='anthropic/claude-sonnet-4.5',
        help='Model to use for review (default: Claude Sonnet 4.5)'
    )
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    if args.debug:
        from logger import set_debug_mode
        set_debug_mode(logger, debug=True)

    # Get API key from environment only
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        logger.error("✗ Error: OpenRouter API key required")
        logger.error("Set OPENROUTER_API_KEY environment variable")
        return 1

    # Security: Validate and resolve paths to prevent directory traversal
    try:
        output_dir = Path(args.output_dir).resolve()
    except (ValueError, OSError) as e:
        logger.error(f"✗ Error: Invalid path: {e}")
        return 1

    # Security: Check for directory traversal attempts
    if '..' in Path(args.output_dir).parts:
        logger.error("✗ Error: Invalid output directory - directory traversal detected")
        return 1

    # Check output directory exists
    if not output_dir.exists():
        logger.error(f"✗ Error: Output directory not found: {output_dir}")
        logger.error("Make sure to run the C4 generators first")
        return 1

    # Update args with validated path
    args.output_dir = str(output_dir)

    metrics = generate_review(
        args.project,
        args.domain,
        args.output_dir,
        api_key,
        args.model
    )
    if metrics:
        logger.info("="*70)
        logger.info("Architectural Review Complete!")
        logger.info("="*70)
        logger.info(f"Review: {args.output_dir}/architecture-review.md")
        logger.info(f"Cost: {format_cost(metrics['levels'][LEVEL_KEY]['cost_usd'])}")
        logger.info(f"Time: {format_duration(metrics['levels'][LEVEL_KEY]['time_seconds'])}")
        logger.info("")
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
