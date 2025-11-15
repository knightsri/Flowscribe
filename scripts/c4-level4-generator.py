#!/usr/bin/env python3
"""
C4 Level 4 (Code Level) Generator - Intelligent Component Selection
Uses LLM to identify the most architecturally significant components
and generates detailed code-level documentation for them.

Metrics: Emits canonical metrics v1.0 with OpenRouter usage-first costing.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Import shared utilities
from flowscribe_utils import LLMClient, CostTracker, parse_llm_json, format_cost, format_duration
from logger import setup_logger

logger = setup_logger(__name__)


def load_deptrac_report(deptrac_json_path):
    """Load and parse deptrac report"""
    try:
        with open(deptrac_json_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"✗ Error: Invalid JSON in deptrac report: {e}")
        return None
    except FileNotFoundError:
        logger.error(f"✗ Error: Deptrac report not found: {deptrac_json_path}")
        return None
    except Exception as e:
        logger.error(f"✗ Error loading deptrac report: {e}")
        return None


def scan_codebase_structure(project_dir):
    """Scan the codebase to find PHP files and their basic structure

    Args:
        project_dir: Path to project directory (validated for security)

    Returns:
        List of PHP file metadata dictionaries
    """
    php_files = []
    # Security: Use resolved absolute path (already validated in main)
    project_path = Path(project_dir).resolve()
    
    # Try to read directories from deptrac.yaml
    search_dirs = []
    deptrac_yaml = project_path / 'deptrac.yaml'
    
    if deptrac_yaml.exists():
        try:
            import yaml
            with open(deptrac_yaml, 'r') as f:
                config = yaml.safe_load(f)
            # Extract paths from deptrac config
            paths = config.get('deptrac', {}).get('paths', [])
            # Remove ./ prefix and add to search_dirs
            search_dirs = [p.lstrip('./') for p in paths]
            logger.info(f"  Using directories from deptrac.yaml: {', '.join(search_dirs)}")
        except Exception as e:
            logger.warning(f"  ⚠ Could not read deptrac.yaml: {e}")
    
    # Fallback to common directories if deptrac.yaml not found or failed
    if not search_dirs:
        search_dirs = ['classes', 'controllers', 'pages', 'api', 'lib', 'src', 'app', 'system']
        logger.info(f"  Using default search directories")
    
    for search_dir in search_dirs:
        dir_path = project_path / search_dir
        if dir_path.exists():
            for php_file in dir_path.rglob('*.php'):
                # Skip tests and vendor
                if 'test' in str(php_file).lower() or 'vendor' in str(php_file):
                    continue
                rel_path = php_file.relative_to(project_path)
                php_files.append({
                    'path': str(rel_path),
                    'name': php_file.stem,
                    'size': php_file.stat().st_size
                })
    
    return php_files


def build_selection_prompt(project_name, domain, deptrac_data, php_files):
    """Build prompt for LLM to select most important components"""
    
    # Extract layer information from deptrac
    layers_summary = {}
    if deptrac_data and 'violations' in deptrac_data:
        for violation in deptrac_data['violations']:
            layer = violation.get('dependerLayer', 'Unknown')
            if layer not in layers_summary:
                layers_summary[layer] = []
            layers_summary[layer].append(violation.get('depender', 'Unknown'))
    
    # Get file statistics
    total_files = len(php_files)
    largest_files = sorted(php_files, key=lambda x: x['size'], reverse=True)[:20]
    
    prompt = f"""You are a software architect analyzing the **{project_name}** project in the **{domain}** domain.

## Your Task

Identify the **10-12 most architecturally significant components** that deserve detailed C4 Level 4 (code-level) documentation.

## Selection Criteria

Choose components that are:
1. **Core Domain Logic** - Central business entities and workflows
2. **Critical Infrastructure** - Key technical components that enable the system
3. **Complex Algorithms** - Non-trivial logic that benefits from detailed explanation
4. **Integration Points** - Components that connect to external systems
5. **High Impact** - Changes here affect many other parts of the system
6. **Pedagogical Value** - Good examples for understanding the architecture

## Project Context

**Domain:** {domain}
**Total PHP Files:** {total_files}

**Architectural Layers from Deptrac:**
"""
    
    for layer, components in list(layers_summary.items())[:5]:
        unique_components = list(set(components))[:10]
        prompt += f"\n- **{layer}:** {len(unique_components)} components (e.g., {', '.join(unique_components[:3])})"
    
    prompt += f"""

**Largest Components (by file size):**
"""
    
    for i, file_info in enumerate(largest_files[:10], 1):
        prompt += f"\n{i}. {file_info['path']} ({file_info['size']:,} bytes)"
    
    prompt += """

## Response Format

Provide your response as JSON:

```json
{
  "selected_components": [
    {
      "name": "ComponentName",
      "file_path": "relative/path/to/Component.php",
      "category": "Core Domain Logic|Infrastructure|Algorithm|Integration|Other",
      "importance": "Why this component is architecturally significant (1-2 sentences)",
      "key_concepts": ["concept1", "concept2", "concept3"]
    }
  ],
  "honorable_mentions": [
    {
      "name": "ComponentName",
      "file_path": "relative/path/to/Component.php",
      "reason": "Why it's worth mentioning but not in top 12"
    }
  ],
  "selection_rationale": "Brief explanation of your overall selection strategy (2-3 sentences)"
}
```

## Important Notes

- Select exactly 10-12 components for `selected_components`
- Include 5-10 components in `honorable_mentions`
- Focus on components that reveal architectural patterns and design decisions
- For {domain} domain, prioritize components related to the core business workflows
- Consider both technical complexity and business importance

Provide ONLY the JSON response, no additional text.
"""
    
    return prompt


def read_component_code(project_dir, file_path):
    """Read the actual PHP code for a component

    Args:
        project_dir: Path to project directory (validated for security)
        file_path: Relative path to component file

    Returns:
        String content of the file or None if not found
    """
    # Security: Use resolved absolute paths (already validated in main)
    full_path = Path(project_dir).resolve() / file_path
    
    if not full_path.exists():
        return None
    
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
            # Limit to reasonable size
            if len(code) > 30000:
                code = code[:30000] + "\n... [truncated - file too large]"
            return code
    except Exception as e:
        logger.error(f"✗ Error reading {file_path}: {e}")
        return None


def build_component_analysis_prompt(project_name, component_info, code):
    """Build prompt for detailed component analysis"""
    
    prompt = f"""You are a software architect creating detailed C4 Level 4 (code-level) documentation for a component in **{project_name}**.

## Component Information

**Name:** {component_info['name']}
**File:** {component_info['file_path']}
**Category:** {component_info['category']}
**Importance:** {component_info['importance']}

## Source Code

```php
{code}
```

## Your Task

Analyze this component and provide detailed architectural documentation in JSON format:

```json
{{
  "component_name": "{component_info['name']}",
  "purpose": "What this component does (1-2 sentences)",
  "responsibility": "Its single responsibility in the architecture",
  "class_type": "Entity|DAO|Service|Controller|Handler|Factory|Strategy|Other",
  "design_patterns": ["Pattern1", "Pattern2"],
  "key_methods": [
    {{
      "name": "methodName",
      "purpose": "What it does",
      "parameters": "param types",
      "returns": "return type",
      "complexity": "Simple|Moderate|Complex"
    }}
  ],
  "dependencies": [
    {{
      "type": "class|interface|trait",
      "name": "DependencyName",
      "relationship": "extends|implements|uses|injects"
    }}
  ],
  "public_interface": [
    "method1()",
    "method2()",
    "method3()"
  ],
  "internal_state": [
    "property1: type - description",
    "property2: type - description"
  ],
  "key_algorithms": [
    {{
      "name": "Algorithm name",
      "description": "What it does and why it's important"
    }}
  ],
  "integration_points": [
    "External system or component it integrates with"
  ],
  "architectural_notes": "Any important architectural decisions, patterns, or constraints (2-3 sentences)"
}}
```

## Analysis Guidelines

1. **Focus on architecture, not implementation details**
2. **Identify design patterns** (Factory, Strategy, Repository, etc.)
3. **Highlight public interface** vs internal implementation
4. **Note integration points** with other components or external systems
5. **Explain key algorithms** if any
6. **Document dependencies** and their nature

Provide ONLY the JSON response, no additional text.
"""
    
    return prompt


def generate_component_markdown(component_data, project_name):
    """Generate markdown documentation for a single component"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    md = f"""# {project_name} - C4 Level 4: {component_data['component_name']}

**Generated:** {timestamp}  
**Type:** {component_data.get('class_type', 'N/A')}  
**File:** `{component_data.get('file_path', 'N/A')}`

---

## Component Overview

### Purpose
{component_data.get('purpose', 'N/A')}

### Responsibility
{component_data.get('responsibility', 'N/A')}

### Design Patterns
"""
    
    patterns = component_data.get('design_patterns', [])
    if patterns:
        for pattern in patterns:
            md += f"- {pattern}\n"
    else:
        md += "*No specific patterns identified*\n"
    
    md += "\n---\n\n## Public Interface\n\n"
    
    public_interface = component_data.get('public_interface', [])
    if public_interface:
        md += "```php\n"
        for method in public_interface:
            md += f"public {method}\n"
        md += "```\n"
    else:
        md += "*No public interface documented*\n"
    
    md += "\n---\n\n## Key Methods\n\n"
    
    key_methods = component_data.get('key_methods', [])
    if key_methods:
        for method in key_methods:
            md += f"### `{method.get('name', 'unknown')}()`\n\n"
            md += f"**Purpose:** {method.get('purpose', 'N/A')}\n\n"
            md += f"**Parameters:** `{method.get('parameters', 'none')}`\n\n"
            md += f"**Returns:** `{method.get('returns', 'void')}`\n\n"
            md += f"**Complexity:** {method.get('complexity', 'Unknown')}\n\n"
    else:
        md += "*No key methods documented*\n\n"
    
    md += "---\n\n## Dependencies\n\n"
    
    dependencies = component_data.get('dependencies', [])
    if dependencies:
        md += "```mermaid\nclassDiagram\n"
        md += f"    class {component_data['component_name']}\n"
        
        for dep in dependencies[:10]:  # Limit to 10 for readability
            dep_name = dep.get('name', 'Unknown')
            relationship = dep.get('relationship', 'uses')
            
            if relationship == 'extends':
                md += f"    {dep_name} <|-- {component_data['component_name']}\n"
            elif relationship == 'implements':
                md += f"    {dep_name} <|.. {component_data['component_name']}\n"
            else:
                md += f"    {component_data['component_name']} ..> {dep_name}\n"
        
        md += "```\n\n"
        
        md += "**Dependency Details:**\n\n"
        for dep in dependencies:
            md += f"- **{dep.get('name', 'Unknown')}** ({dep.get('type', 'unknown')}) - {dep.get('relationship', 'uses')}\n"
    else:
        md += "*No dependencies identified*\n"
    
    md += "\n---\n\n## Internal State\n\n"
    
    internal_state = component_data.get('internal_state', [])
    if internal_state:
        for state in internal_state:
            md += f"- `{state}`\n"
    else:
        md += "*No internal state documented*\n"
    
    md += "\n---\n\n## Key Algorithms\n\n"
    
    algorithms = component_data.get('key_algorithms', [])
    if algorithms:
        for algo in algorithms:
            md += f"### {algo.get('name', 'Unknown')}\n\n"
            md += f"{algo.get('description', 'N/A')}\n\n"
    else:
        md += "*No complex algorithms identified*\n"
    
    md += "\n---\n\n## Integration Points\n\n"
    
    integrations = component_data.get('integration_points', [])
    if integrations:
        for integration in integrations:
            md += f"- {integration}\n"
    else:
        md += "*No external integration points*\n"
    
    md += "\n---\n\n## Architectural Notes\n\n"
    md += f"{component_data.get('architectural_notes', 'N/A')}\n\n"
    
    md += "---\n\n*Generated by Flowscribe - Automated C4 Architecture Documentation*\n"
    
    return md


def generate_hub_markdown(project_name, domain, selected_components, honorable_mentions, rationale):
    """Generate the main hub document that links to all component docs"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    md = f"""# {project_name} - C4 Level 4: Code-Level Architecture

**Generated:** {timestamp}  
**Domain:** {domain}  
**Diagram Level:** C4 Level 4 (Code - Selective)

---

## Overview

This document presents **detailed code-level architecture** for the most significant components in {project_name}.

Unlike a comprehensive code documentation (which would be overwhelming), this focuses on the **10-12 most architecturally important components** that reveal:
- Core domain logic and business workflows
- Critical infrastructure patterns
- Complex algorithms and design decisions
- Key integration points

---

## Selection Rationale

{rationale}

---

## Documented Components

The following components have detailed C4 Level 4 documentation:

| # | Component | Category | Documentation |
|---|-----------|----------|---------------|
"""
    
    for i, comp in enumerate(selected_components, 1):
        doc_filename = f"c4-level4-{comp['name']}.md"
        md += f"| {i} | **{comp['name']}** | {comp['category']} | [View Details](./{doc_filename}) |\n"
    
    md += f"\n**Total Components Documented:** {len(selected_components)}\n\n"
    
    md += "---\n\n## Component Details\n\n"
    
    for comp in selected_components:
        doc_filename = f"c4-level4-{comp['name']}.md"
        md += f"### {comp['name']}\n\n"
        md += f"**File:** `{comp['file_path']}`\n\n"
        md += f"**Category:** {comp['category']}\n\n"
        md += f"**Why Important:** {comp['importance']}\n\n"
        
        if 'key_concepts' in comp and comp['key_concepts']:
            md += "**Key Concepts:** "
            md += ", ".join(comp['key_concepts'])
            md += "\n\n"
        
        md += f"**[→ Read Full Documentation](./{doc_filename})**\n\n"
    
    md += "---\n\n## Honorable Mentions\n\n"
    md += "These components are also architecturally significant but not included in the top 12:\n\n"
    
    if honorable_mentions:
        for mention in honorable_mentions:
            md += f"### {mention['name']}\n"
            md += f"**File:** `{mention['file_path']}`\n\n"
            md += f"**Why Notable:** {mention['reason']}\n\n"
    else:
        md += "*No honorable mentions identified*\n\n"
    
    md += "---\n\n## Generating Additional Component Documentation\n\n"
    md += "To generate Level 4 documentation for other components:\n\n"
    md += "```bash\n"
    md += "# Generate for a specific component\n"
    md += f"python3 /workspace/scripts/c4-level4-generator.py \\\n"
    md += f"    /workspace/projects/[project-dir] \\\n"
    md += f"    /workspace/output/[project]/deptrac-report.json \\\n"
    md += f"    --project \"{project_name}\" \\\n"
    md += f"    --domain \"{domain}\" \\\n"
    md += f"    --component \"ComponentName\" \\\n"
    md += f"    --file \"path/to/Component.php\" \\\n"
    md += f"    --output /workspace/output/[project]/c4-level4-ComponentName.md\n"
    md += "```\n\n"
    
    md += "---\n\n## Architecture Insights\n\n"
    md += "### Component Categories\n\n"
    
    categories = {}
    for comp in selected_components:
        cat = comp['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(comp['name'])
    
    for cat, comps in categories.items():
        md += f"**{cat}:** {len(comps)} component{'s' if len(comps) > 1 else ''}\n"
        for comp_name in comps:
            md += f"- {comp_name}\n"
        md += "\n"
    
    md += "---\n\n## Next Steps\n\n"
    md += "1. **Review Component Details** - Read the linked documentation for each component\n"
    md += "2. **Understand Patterns** - Note the design patterns used across components\n"
    md += "3. **Trace Dependencies** - Follow dependency chains to understand coupling\n"
    md += "4. **Compare with L2/L3** - See how these components fit into higher-level architecture\n"
    md += "5. **Identify Refactoring Opportunities** - Use insights to improve architecture\n\n"
    
    md += "---\n\n*Generated by Flowscribe - Automated C4 Architecture Documentation*\n"
    
    return md


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
    parser = argparse.ArgumentParser(
        description='Generate C4 Level 4 (Code) documentation for architecturally significant components'
    )
    
    parser.add_argument(
        'project_dir',
        help='Path to the project directory'
    )
    
    parser.add_argument(
        'deptrac_json',
        help='Path to deptrac JSON report'
    )
    
    parser.add_argument(
        '--project',
        required=True,
        help='Project name (e.g., "Open Journal Systems")'
    )
    
    parser.add_argument(
        '--domain',
        required=True,
        help='Project domain (e.g., "scholarly publishing")'
    )

    parser.add_argument(
        '--model',
        default=os.environ.get('OPENROUTER_MODEL', 'anthropic/claude-sonnet-4-20250514'),
        help='Model to use'
    )

    parser.add_argument(
        '--output-dir',
        required=True,
        help='Output directory for generated documentation'
    )

    parser.add_argument(
        '--max-components',
        type=int,
        default=12,
        help='Maximum number of components to document (default: 12)'
    )

    args = parser.parse_args()

    # Get API key from environment only
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        logger.error("✗ Error: OpenRouter API key required")
        logger.error("Set OPENROUTER_API_KEY environment variable")
        return 1

    # Security: Validate and resolve paths to prevent directory traversal
    try:
        project_dir = Path(args.project_dir).resolve()
        deptrac_json = Path(args.deptrac_json).resolve()
        output_dir = Path(args.output_dir).resolve()
    except (ValueError, OSError) as e:
        logger.error(f"✗ Error: Invalid path: {e}")
        return 1

    # Security: Check for directory traversal attempts
    if '..' in Path(args.project_dir).parts:
        logger.error("✗ Error: Invalid project directory - directory traversal detected")
        return 1

    if '..' in Path(args.deptrac_json).parts:
        logger.error("✗ Error: Invalid deptrac json path - directory traversal detected")
        return 1

    if '..' in Path(args.output_dir).parts:
        logger.error("✗ Error: Invalid output directory - directory traversal detected")
        return 1

    # Check paths exist
    if not project_dir.exists():
        logger.error(f"✗ Error: Project directory not found: {project_dir}")
        return 1

    if not deptrac_json.exists():
        logger.error(f"✗ Error: Deptrac report not found: {deptrac_json}")
        return 1

    # Update args with validated paths
    args.project_dir = str(project_dir)
    args.deptrac_json = str(deptrac_json)
    args.output_dir = str(output_dir)

    logger.info(f"\n{'='*70}")
    logger.info(f"C4 Level 4 Generator - Intelligent Component Selection")
    logger.info(f"{'='*70}\n")
    logger.info(f"Project: {args.project}")
    logger.info(f"Domain: {args.domain}")
    logger.info(f"Model: {args.model}")
    logger.info(f"Max Components: {args.max_components}\n")
    
    # Initialize cost tracker and LLM client
    tracker = CostTracker(args.model)
    llm = LLMClient(api_key, args.model, tracker)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Track overall time
    start_time = time.time()
    
    # Phase 1: Component Selection
    logger.info("=" * 70)
    logger.info("PHASE 1: Intelligent Component Selection")
    logger.info("=" * 70 + "\n")

    logger.info("Step 1: Loading deptrac analysis...")
    phase1_start = time.time()

    deptrac_data = load_deptrac_report(args.deptrac_json)
    if deptrac_data:
        logger.info("✓ Deptrac data loaded\n")
    else:
        logger.warning("⚠ Warning: Could not load deptrac data, continuing anyway\n")

    logger.info("Step 2: Scanning codebase structure...")
    php_files = scan_codebase_structure(args.project_dir)
    logger.info(f"✓ Found {len(php_files)} PHP files\n")

    if not php_files:
        logger.error("✗ Error: No PHP files found in project")
        return 1

    logger.info("Step 3: Building component selection prompt...")
    selection_prompt = build_selection_prompt(args.project, args.domain, deptrac_data, php_files)
    logger.info(f"✓ Prompt ready ({len(selection_prompt)} chars)\n")

    logger.info("Step 4: Asking LLM to select most important components...")
    logger.info("(This may take 30-90 seconds...)\n")
    
    selection_result = llm.call(selection_prompt)

    if not selection_result:
        logger.error("✗ Error: Component selection failed")
        return 1

    logger.info(f"✓ Selection complete")
    logger.info(f"  Cost: {format_cost(selection_result['cost'])}")
    logger.info(f"  Time: {format_duration(selection_result['duration'])}")
    logger.info(f"  Tokens: {selection_result['total_tokens']:,}\n")
    
    # Parse selection
    selection_data = parse_llm_json(selection_result['content'])

    if not selection_data:
        logger.error("✗ Error: Could not parse LLM selection response")
        return 1

    selected_components = selection_data.get('selected_components', [])[:args.max_components]
    honorable_mentions = selection_data.get('honorable_mentions', [])
    rationale = selection_data.get('selection_rationale', 'N/A')

    if not selected_components:
        logger.error("✗ Error: No components selected by LLM")
        return 1

    logger.info(f"✓ Selected {len(selected_components)} components for detailed documentation\n")

    for i, comp in enumerate(selected_components, 1):
        logger.info(f"  {i}. {comp['name']} ({comp['category']})")

    logger.info(f"\n  + {len(honorable_mentions)} honorable mentions\n")

    phase1_time = time.time() - phase1_start
    logger.info(f"Phase 1 complete: {format_duration(phase1_time)}\n")
    
    # Phase 2: Generate Component Documentation
    logger.info("=" * 70)
    logger.info("PHASE 2: Generating Component Documentation")
    logger.info("=" * 70 + "\n")
    
    phase2_start = time.time()
    documented_components = []
    analysis_results = []  # collect per-component LLM results for metrics
    
    for i, comp in enumerate(selected_components, 1):
        logger.info(f"Component {i}/{len(selected_components)}: {comp['name']}")
        logger.info(f"  File: {comp['file_path']}")

        comp_start = time.time()

        # Read component code
        logger.info("  → Reading source code...")
        code = read_component_code(args.project_dir, comp['file_path'])

        if not code:
            logger.error(f"  ✗ Could not read source code, skipping\n")
            continue

        logger.info(f"  ✓ Source code loaded ({len(code)} chars)")

        # Analyze component
        logger.info("  → Analyzing with LLM...")
        analysis_prompt = build_component_analysis_prompt(args.project, comp, code)
        analysis_result = llm.call(analysis_prompt)

        if not analysis_result:
            logger.error("  ✗ Analysis failed, skipping\n")
            continue

        # Parse analysis
        component_data = parse_llm_json(analysis_result['content'])

        if not component_data:
            logger.error("  ✗ Parse error, skipping\n")
            continue

        component_data['file_path'] = comp['file_path']

        # Generate markdown
        logger.info("  → Generating markdown...")
        component_md = generate_component_markdown(component_data, args.project)

        # Write file
        output_filename = f"c4-level4-{comp['name']}.md"
        output_path = output_dir / output_filename

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(component_md)
        except Exception as e:
            logger.error(f"  ✗ Write error: {e}, skipping\n")
            continue

        comp_time = time.time() - comp_start

        logger.info(f"  ✓ Written to {output_filename}")
        logger.info(f"  Cost: {format_cost(analysis_result['cost'])} | Time: {format_duration(comp_time)}\n")

        documented_components.append(comp)
        analysis_results.append(analysis_result)
    
    phase2_time = time.time() - phase2_start

    if not documented_components:
        logger.error("✗ Error: No components were successfully documented")
        return 1

    logger.info(f"Phase 2 complete: {format_duration(phase2_time)}")
    logger.info(f"Successfully documented {len(documented_components)}/{len(selected_components)} components\n")

    # Generate hub document
    logger.info("Generating hub document...")
    hub_md = generate_hub_markdown(
        args.project,
        args.domain,
        documented_components,
        honorable_mentions,
        rationale
    )

    hub_path = output_dir / "c4-level4.md"
    try:
        with open(hub_path, 'w', encoding='utf-8') as f:
            f.write(hub_md)
        logger.info(f"✓ Hub document written to c4-level4.md\n")
    except Exception as e:
        logger.error(f"✗ Error writing hub document: {e}")
        return 1
    
    # === Canonical metrics v1.0 (usage-first) ===
    total_time = time.time() - start_time
    tracker.total_time = total_time  # keep tracker consistent for legacy print

    logger.info("=" * 70)
    logger.info("Summary")
    logger.info("=" * 70 + "\n")

    logger.info(f"Generated Files:")
    logger.info(f"  - c4-level4.md (hub document)")
    for comp in documented_components:
        logger.info(f"  - c4-level4-{comp['name']}.md")
    logger.info(f"\nTotal: {len(documented_components) + 1} files\n")
    
    # Print cost summary (legacy, still useful in console)
    tracker.print_summary()
    
    # Build canonical calls[] from selection + analysis
    calls = []
    calls.extend(_extract_usage_calls_from_result(selection_result, default_model=args.model))
    for ar in analysis_results:
        calls.extend(_extract_usage_calls_from_result(ar, default_model=args.model))
    
    cost_usd = round(sum(c.get("cost_usd", 0.0) for c in calls), 6)
    tokens_in = sum(c.get("prompt_tokens", 0) for c in calls)
    tokens_out = sum(c.get("completion_tokens", 0) for c in calls)
    
    canonical_metrics = {
        "version": "1.0",
        "repo": {
            "name": args.project,
            "analysis_utc": datetime.utcnow().isoformat() + "Z"
        },
        "levels": {
            "level4": {
                "cost_usd": cost_usd,
                "time_seconds": round(float(total_time), 3),
                "tokens_in": int(tokens_in),
                "tokens_out": int(tokens_out),
                "model": args.model if calls else "none",
                "calls": calls
            }
        },
        "totals": {
            "cost_usd": cost_usd,
            "time_seconds": round(float(total_time), 3),
            "tokens_in": int(tokens_in),
            "tokens_out": int(tokens_out)
        },
        # Legacy block for backward compatibility with prior analyzer
        "legacy": {
            "model": args.model,
            "total_cost_usd": float(cost_usd),
            "total_time_seconds": round(float(total_time), 3),
            "total_input_tokens": int(tokens_in),
            "total_output_tokens": int(tokens_out),
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "components_documented": int(len(documented_components))
        }
    }
    
    metrics_file = output_dir / '.c4-level4-metrics.json'
    try:
        metrics_file.write_text(json.dumps(canonical_metrics, indent=2), encoding='utf-8')
        logger.info(f"✓ Metrics (v1.0) saved to {metrics_file}")
    except Exception as e:
        logger.warning(f"⚠ Warning: Could not save metrics: {e}")

    logger.info(f"\n{'='*70}")
    logger.info(f"✓ C4 Level 4 documentation generated successfully!")
    logger.info(f"{'='*70}\n")
    
    return 0


if __name__ == '__main__':
    exit(main())
