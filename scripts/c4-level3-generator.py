#!/usr/bin/env python3
"""
Generate C4 Level 3 (Component) diagrams from Deptrac analysis

Usage:
    python3 c4-level3-generator.py /workspace/output/ojs/deptrac-report.json \
        --layer Presentation \
        --project "Open Journal Systems" \
        --output /workspace/output/ojs/c4-level3-presentation.md
"""

import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Import shared utilities
from flowscribe_utils import CostTracker, format_duration
from flowscribe_utils import MermaidIdRegistry, mermaid_safe_id
from logger import setup_logger

logger = setup_logger(__name__)


class C4Level3Generator:
    """Generate C4 Level 3 component diagrams"""
    
    def __init__(self, deptrac_report_path, project_dir=None, model="none"):
        # Security: Resolve paths to absolute and validate
        self.report_path = Path(deptrac_report_path).resolve()

        if project_dir:
            proj_path = Path(project_dir).resolve()
            # Security: Check for directory traversal
            if '..' in Path(project_dir).parts:
                raise ValueError("Invalid project directory: directory traversal detected")
            self.project_dir = proj_path
        else:
            self.project_dir = self.report_path.parent.parent / 'projects' / self.report_path.parent.name
        
        # Cost tracker (no LLM calls in basic mode, but tracks time)
        self.tracker = CostTracker(model)
        
        # Load report
        load_start = time.time()
        try:
            with open(self.report_path, 'r') as f:
                self.report = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"✗ Error: Invalid JSON in Deptrac report: {e}")
            raise
        except FileNotFoundError:
            logger.error(f"✗ Error: Deptrac report not found: {self.report_path}")
            raise
        except Exception as e:
            logger.error(f"✗ Error loading Deptrac report: {e}")
            raise
        
        load_time = time.time() - load_start
        
        # Validate report structure
        if not isinstance(self.report, dict):
            raise ValueError("Deptrac report must be a JSON object")
        if 'files' not in self.report:
            logger.warning("⚠️  Warning: Deptrac report missing 'files' field")
        
        self.layer_components = defaultdict(lambda: defaultdict(list))
        self.component_dependencies = []
        
        # Parse report
        parse_start = time.time()
        self._parse_components_from_filesystem()  # NEW METHOD
        parse_time = time.time() - parse_start
        
        # Record timing (no tokens/cost since no LLM)
        self.tracker.record_call(0, 0, load_time + parse_time)


    def _parse_components(self):
        """Extract components and their dependencies"""
        if 'files' not in self.report:
            return
        
        for file_path, file_data in self.report['files'].items():
            # Extract component name from file path
            component_name = self._extract_component_name(file_path)
            
            for message_data in file_data.get('messages', []):
                msg = message_data.get('message', '')
                
                # Parse layer information
                if ' on ' in msg and '(' in msg:
                    parts = msg.split('(')
                    if len(parts) >= 2:
                        layer_part = parts[-1].strip(')')
                        if ' on ' in layer_part:
                            source_layer, target_layer = layer_part.split(' on ')
                            source_layer = source_layer.strip()
                            target_layer = target_layer.strip()
                            
                            # Store component in its layer
                            self.layer_components[source_layer][component_name].append({
                                'file': file_path,
                                'message': msg,
                                'line': message_data.get('line')
                            })
                            
                            # Extract target component if possible
                            if 'depend on' in msg:
                                target_parts = msg.split('depend on')
                                if len(target_parts) >= 2:
                                    target_class = target_parts[1].split('(')[0].strip()
                                    target_component = self._simplify_class_name(target_class)
                                    
                                    self.component_dependencies.append({
                                        'from': component_name,
                                        'to': target_component,
                                        'from_layer': source_layer,
                                        'to_layer': target_layer
                                    })
        
        # Check if we found anything
        if not self.layer_components:
            logger.warning("⚠️  Warning: No components found in Deptrac report")
            logger.warning("   This may indicate:")
            logger.warning("   - No violations in the report")
            logger.warning("   - Unexpected report format")

    def _parse_components_from_filesystem(self):
        """Extract components by scanning filesystem using deptrac.yaml layer definitions"""
        # Try to read deptrac.yaml
        deptrac_yaml = self.project_dir / 'deptrac.yaml'

        if not deptrac_yaml.exists():
            logger.warning(f"⚠️  Warning: deptrac.yaml not found at {deptrac_yaml}")
            logger.warning("   Falling back to violation-based parsing")
            self._parse_components()  # Fallback to old method
            return
        
        try:
            import yaml
            with open(deptrac_yaml, 'r') as f:
                config = yaml.safe_load(f)
            
            # For each layer, scan files matching its patterns
            for layer_def in config.get('deptrac', {}).get('layers', []):
                layer_name = layer_def['name']
                
                for collector in layer_def.get('collectors', []):
                    collector_type = collector.get('type')
                    pattern = collector.get('value', '')
                    
                    if collector_type == 'directory':
                        # Convert 'wp-admin/.*' to 'wp-admin/**/*.php'
                        dir_pattern = pattern.replace('/.*', '/**/*.php')
                        
                        # Scan for PHP files
                        for php_file in self.project_dir.glob(dir_pattern):
                            if php_file.is_file() and 'vendor' not in str(php_file) and 'test' not in str(php_file).lower():
                                component_name = self._extract_component_name(str(php_file))
                                rel_path = php_file.relative_to(self.project_dir)
                                
                                # Add to layer components
                                self.layer_components[layer_name][component_name].append({
                                    'file': str(rel_path),
                                    'message': None,
                                    'line': None
                                })
                    
                    elif collector_type == 'glob':
                        # Direct glob pattern like '*.php'
                        for php_file in self.project_dir.glob(pattern):
                            if php_file.is_file() and 'vendor' not in str(php_file):
                                component_name = self._extract_component_name(str(php_file))
                                rel_path = php_file.relative_to(self.project_dir)
                                
                                self.layer_components[layer_name][component_name].append({
                                    'file': str(rel_path),
                                    'message': None,
                                    'line': None
                                })
            
            # Also parse violations for dependency information
            self._parse_violations_for_dependencies()

            logger.info(f"✓ Loaded components from filesystem")
            logger.info(f"  Found {len(self.layer_components)} layers")

        except Exception as e:
            logger.warning(f"⚠️  Error parsing deptrac.yaml: {e}")
            import traceback
            traceback.print_exc()
            logger.warning("   Falling back to violation-based parsing")
            self._parse_components()  # Fallback
    

    def _parse_violations_for_dependencies(self):
        """Parse violation messages to extract dependency relationships"""
        if 'files' not in self.report:
            return
        
        for file_path, file_data in self.report['files'].items():
            component_name = self._extract_component_name(file_path)
            
            for message_data in file_data.get('messages', []):
                msg = message_data.get('message', '')
                
                # Parse dependency relationships
                if 'depend on' in msg and '(' in msg:
                    parts = msg.split('(')
                    if len(parts) >= 2:
                        layer_part = parts[-1].strip(')')
                        if ' on ' in layer_part:
                            source_layer, target_layer = layer_part.split(' on ')
                            source_layer = source_layer.strip()
                            target_layer = target_layer.strip()
                            
                            # Extract target component
                            target_parts = msg.split('depend on')
                            if len(target_parts) >= 2:
                                target_class = target_parts[1].split('(')[0].strip()
                                target_component = self._simplify_class_name(target_class)
                                
                                self.component_dependencies.append({
                                    'from': component_name,
                                    'to': target_component,
                                    'from_layer': source_layer,
                                    'to_layer': target_layer
                                })

    def _extract_component_name(self, file_path):
        """Extract component name from file path"""
        # Get filename without extension
        filename = file_path.split('/')[-1]
        component = filename.replace('.php', '')
        return component
    
    def _simplify_class_name(self, class_name):
        """Simplify fully qualified class name to component name"""
        # Extract last part of namespace
        if '\\' in class_name:
            return class_name.split('\\')[-1]
        return class_name
    
    def generate_layer_component_diagram(self, layer_name):
        """Generate C4 L3 component diagram for a specific layer"""
        
        if layer_name not in self.layer_components:
            return f"*Layer '{layer_name}' not found in analysis*"
        
        components = self.layer_components[layer_name]
        
        if not components:
            return f"*No components found in {layer_name} layer*"
        
        mermaid = ["```mermaid", "graph TB"]
        
        # Add layer boundary
        mermaid.append(f'    subgraph "{layer_name} Layer"')
        
        # Group components by type/category
        categorized = self._categorize_components(layer_name, components)
        
        for category, comps in categorized.items():
            if comps:
                mermaid.append(f'        subgraph "{category}"')
                for comp_name in comps:
                    # Sanitize name for Mermaid
                    node_id = comp_name.replace(' ', '_').replace('-', '_')
                    mermaid.append(f'            {node_id}[{comp_name}]')
                mermaid.append('        end')
        
        mermaid.append('    end')
        
        # Add dependencies between components in this layer
        mermaid.append("")
        mermaid.append("    %% Component Dependencies")
        
        internal_deps = []
        for dep in self.component_dependencies:
            if dep['from_layer'] == layer_name and dep['to_layer'] == layer_name:
                from_id = dep['from'].replace(' ', '_').replace('-', '_')
                to_id = dep['to'].replace(' ', '_').replace('-', '_')
                internal_deps.append(f"    {from_id} --> {to_id}")
        
        if internal_deps:
            for dep in internal_deps[:20]:  # Limit to avoid clutter
                mermaid.append(dep)
            if len(internal_deps) > 20:
                mermaid.append(f"    %% ... and {len(internal_deps) - 20} more internal dependencies")
        
        # Add external dependencies
        mermaid.append("")
        mermaid.append("    %% External Layer Dependencies")
        
        external_layers = set()
        for dep in self.component_dependencies:
            if dep['from_layer'] == layer_name and dep['to_layer'] != layer_name:
                external_layers.add(dep['to_layer'])
        
        for ext_layer in external_layers:
            ext_id = ext_layer.replace(' ', '_')
            mermaid.append(f"    {ext_id}[{ext_layer} Layer]")
        
        external_deps = []
        for dep in self.component_dependencies:
            if dep['from_layer'] == layer_name and dep['to_layer'] != layer_name:
                from_id = dep['from'].replace(' ', '_').replace('-', '_')
                to_id = dep['to_layer'].replace(' ', '_')
                external_deps.append(f"    {from_id} -.-> {to_id}")
        
        if external_deps:
            for dep in external_deps[:10]:  # Limit external deps shown
                mermaid.append(dep)
            if len(external_deps) > 10:
                mermaid.append(f"    %% ... and {len(external_deps) - 10} more external dependencies")
        
        mermaid.append("```")
        
        return "\n".join(mermaid)
    
    def _categorize_components(self, layer_name, components):
        """Categorize components by type"""
        categories = defaultdict(list)
        
        # Layer-specific categorization
        if layer_name == "Presentation":
            for comp_name in components.keys():
                if 'Handler' in comp_name:
                    categories['Request Handlers'].append(comp_name)
                elif 'Controller' in comp_name:
                    categories['Controllers'].append(comp_name)
                elif 'Form' in comp_name:
                    categories['Forms'].append(comp_name)
                else:
                    categories['Other UI Components'].append(comp_name)
        
        elif layer_name == "Infrastructure":
            for comp_name in components.keys():
                if 'DOI' in comp_name or 'Doi' in comp_name:
                    categories['DOI Services'].append(comp_name)
                elif 'ORCID' in comp_name or 'Orcid' in comp_name:
                    categories['ORCID Integration'].append(comp_name)
                elif 'Mail' in comp_name or 'Email' in comp_name or 'Notif' in comp_name:
                    categories['Notification Services'].append(comp_name)
                elif 'Payment' in comp_name:
                    categories['Payment Services'].append(comp_name)
                elif 'File' in comp_name:
                    categories['File Management'].append(comp_name)
                else:
                    categories['Other Infrastructure'].append(comp_name)
        
        elif layer_name == "Persistence":
            for comp_name in components.keys():
                if 'DAO' in comp_name:
                    categories['Data Access Objects'].append(comp_name)
                else:
                    categories['Repository Components'].append(comp_name)
        
        elif layer_name == "Domain":
            categories['Domain Entities'] = list(components.keys())
        
        else:
            categories['Components'] = list(components.keys())
        
        return categories
    
    def generate_component_list(self, layer_name):
        """Generate detailed component list with descriptions"""
        if layer_name not in self.layer_components:
            return []
        
        components = self.layer_components[layer_name]
        component_list = []
        
        for comp_name, details in components.items():
            # Infer purpose from name (basic heuristics)
            purpose = self._infer_purpose(comp_name, layer_name)
            
            component_list.append({
                'name': comp_name,
                'purpose': purpose,
                'violation_count': len(details),
                'file': details[0]['file'] if details else 'Unknown'
            })
        
        return sorted(component_list, key=lambda x: x['name'])
    
    def _infer_purpose(self, component_name, layer_name):
        """Infer component purpose (basic heuristics)"""
        # Basic inference - could be enhanced with LLM
        
        if 'Handler' in component_name:
            return f"Handles requests for {component_name.replace('Handler', '').replace('Grid', 'grid')}"
        elif 'Controller' in component_name:
            return f"Controls {component_name.replace('Controller', '')} operations"
        elif 'DAO' in component_name:
            return f"Database access for {component_name.replace('DAO', '')}"
        elif 'Form' in component_name:
            return f"Form handling for {component_name.replace('Form', '')}"
        elif 'Manager' in component_name:
            return f"Manages {component_name.replace('Manager', '')} operations"
        elif 'Service' in component_name:
            return f"Service for {component_name.replace('Service', '')}"
        else:
            return f"{component_name} component"
    
    def generate_markdown(self, layer_name, project_name="Project"):
        """Generate complete C4 Level 3 markdown for a layer"""
        
        if layer_name not in self.layer_components:
            available = ', '.join(self.layer_components.keys()) if self.layer_components else 'None'
            return f"""# Layer '{layer_name}' Not Found

**Available layers:** {available}

---

*Please check the layer name and try again.*
"""
        
        component_list = self.generate_component_list(layer_name)
        
        doc = f"""# {project_name} - {layer_name} Layer (C4 Level 3)

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Layer:** {layer_name}  
**Components:** {len(component_list)}  
**Source:** Deptrac dependency analysis

---

## Component Diagram

{self.generate_layer_component_diagram(layer_name)}

---

## Component List

"""
        
        # Group components by category
        categorized = self._categorize_components(layer_name, self.layer_components[layer_name])
        
        for category, comp_names in categorized.items():
            if comp_names:
                doc += f"### {category}\n\n"
                
                for comp_name in sorted(comp_names):
                    comp_detail = next((c for c in component_list if c['name'] == comp_name), None)
                    if comp_detail:
                        doc += f"#### {comp_detail['name']}\n\n"
                        doc += f"**Purpose:** {comp_detail['purpose']}\n\n"
                        doc += f"**File:** `{comp_detail['file'].split('/')[-1]}`\n\n"
                        
                        if comp_detail['violation_count'] > 0:
                            doc += f"**Architectural Issues:** {comp_detail['violation_count']} violations detected\n\n"
                        
                        doc += "---\n\n"
        
        doc += f"""
## Statistics

- **Total Components:** {len(component_list)}
- **Component Categories:** {len(categorized)}
- **Internal Dependencies:** {sum(1 for d in self.component_dependencies if d['from_layer'] == layer_name and d['to_layer'] == layer_name)}
- **External Dependencies:** {sum(1 for d in self.component_dependencies if d['from_layer'] == layer_name and d['to_layer'] != layer_name)}

---

## Analysis Notes

⚠️ **Basic Component Analysis**

This is a basic component-level analysis extracted from Deptrac violations. For enhanced analysis with:
- Better component descriptions
- Intelligent grouping
- Architectural pattern detection
- Business context
- Refactoring recommendations

Use the LLM-enhanced version: `llm-enhancer.py --enhance-components`

---

*Component diagram generated from Deptrac dependency analysis*
"""
        
        return doc


def main():
    parser = argparse.ArgumentParser(
        description='Generate C4 Level 3 component diagrams from Deptrac analysis'
    )
    
    parser.add_argument(
        'deptrac_report',
        help='Path to deptrac-report.json'
    )
    
    parser.add_argument(
        '--layer', '-l',
        required=True,
        help='Layer to generate diagram for (Presentation, Infrastructure, Persistence, Domain, etc.)'
    )
    
    parser.add_argument(
        '--project', '-p',
        default='Project',
        help='Project name (e.g., "Open Journal Systems")'
    )
    
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output markdown file path'
    )
    
    parser.add_argument(
        '--model',
        default='none',
        help='Model name for metrics (default: none, since no LLM used)'
    )
    
    parser.add_argument(
        '--project-dir',
        help='Project directory path'
    )
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        from logger import set_debug_mode
        set_debug_mode(logger, debug=True)

    # Security: Validate and resolve paths to prevent directory traversal
    try:
        deptrac_report = Path(args.deptrac_report).resolve()
        output_path = Path(args.output).resolve()

        # Validate project_dir if provided
        if args.project_dir:
            project_dir = Path(args.project_dir).resolve()
        else:
            project_dir = None
    except (ValueError, OSError) as e:
        logger.error(f"✗ Error: Invalid path: {e}")
        return 1

    # Security: Check for directory traversal attempts
    if '..' in Path(args.deptrac_report).parts:
        logger.error("✗ Error: Invalid deptrac report path - directory traversal detected")
        return 1

    if '..' in Path(args.output).parts:
        logger.error("✗ Error: Invalid output path - directory traversal detected")
        return 1

    if args.project_dir and '..' in Path(args.project_dir).parts:
        logger.error("✗ Error: Invalid project directory - directory traversal detected")
        return 1

    # Check deptrac report exists
    if not deptrac_report.exists():
        logger.error(f"✗ Error: Deptrac report not found: {deptrac_report}")
        logger.error(f"\n⚠️  Make sure you've run deptrac analysis first")
        return 1

    # Update args with validated paths
    args.deptrac_report = str(deptrac_report)
    args.output = str(output_path)
    if project_dir:
        args.project_dir = str(project_dir)

    logger.info(f"\n{'='*60}")
    logger.info(f"C4 Level 3 Generator - Component Diagram")
    logger.info(f"{'='*60}\n")
    logger.info(f"Project: {args.project}")
    logger.info(f"Layer: {args.layer}")
    logger.info(f"Deptrac Report: {args.deptrac_report}")
    logger.info(f"Output: {args.output}\n")

    # Step 1: Load and parse
    logger.info(f"Step 1: Loading Deptrac report and extracting {args.layer} components...")
    start_time = time.time()
    
    try:
        generator = C4Level3Generator(args.deptrac_report, project_dir=args.project_dir, model='none')
    except Exception as e:
        logger.error(f"✗ Error: Failed to load Deptrac report: {e}")
        return 1

    load_time = time.time() - start_time

    # Check if layer exists
    if args.layer not in generator.layer_components:
        available = ', '.join(generator.layer_components.keys()) if generator.layer_components else 'None'
        logger.error(f"✗ Error: Layer '{args.layer}' not found")
        logger.error(f"  Available layers: {available}")
        return 1

    component_count = len(generator.layer_components[args.layer])

    logger.info(f"✓ Loaded and parsed report")
    logger.info(f"  Components in {args.layer}: {component_count}")
    logger.info(f"  Time: {format_duration(load_time)}\n")

    # Step 2: Generate markdown
    logger.info("Step 2: Generating C4 Level 3 markdown...")
    gen_start = time.time()

    markdown = generator.generate_markdown(args.layer, args.project)

    gen_time = time.time() - gen_start
    logger.info(f"✓ Generated markdown")
    logger.info(f"  Time: {format_duration(gen_time)}\n")

    # Step 3: Write output
    logger.info("Step 3: Writing output file...")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        logger.info(f"✓ Written to {args.output}\n")
    except Exception as e:
        logger.error(f"✗ Error writing output file: {e}")
        return 1

    # Step 4: Save canonical metrics (v1.0; no LLM usage here)
    logger.info("Step 4: Saving metrics (v1.0)...")
    
    total_time = time.time() - start_time
    generator.tracker.total_time = total_time
    
    # Print summary (optional)
    generator.tracker.print_summary()
    
    # Canonical metrics output: one file per layer
    metrics = {
        "version": "1.0",
        "repo": {
            "name": args.project,
            "analysis_utc": datetime.utcnow().isoformat() + "Z"
        },
        "levels": {
            f"level3_{args.layer.lower()}": {
                "cost_usd": 0.0,
                "time_seconds": round(float(total_time), 3),
                "tokens_in": 0,
                "tokens_out": 0,
                "model": "none"
            }
        },
        "totals": {
            "cost_usd": 0.0,
            "time_seconds": round(float(total_time), 3),
            "tokens_in": 0,
            "tokens_out": 0
        },
        "legacy": {
            "model": "none",
            "total_cost_usd": 0.0,
            "total_time_seconds": round(float(total_time), 3),
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "layer": args.layer,
            "component_count": int(component_count)
        }
    }
    metrics_path = output_path.parent / f'.c4-level3-{args.layer.lower()}-metrics.json'
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    logger.info(f"✓ Metrics saved to {metrics_path}")

    logger.info(f"\n{'='*60}")
    logger.info(f"✓ C4 Level 3 ({args.layer}) documentation generated!")
    logger.info(f"{'='*60}\n")

    return 0


if __name__ == '__main__':
    exit(main())
