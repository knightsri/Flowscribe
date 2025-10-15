#!/usr/bin/env python3
"""
Flowscribe - Automated C4 Architecture Documentation Generator

Fully automated pipeline from GitHub URL to complete C4 documentation (L1-L4).

Usage:
    python3 flowscribe-analyze.py https://github.com/pkp/ojs

Features:
    - Auto-detects project name and domain
    - Checks for manually cloned repository
    - Generates deptrac.yaml dynamically with LLM
    - Generates C4 L1, L2, L3 (all layers), L4
    - Tracks and reports total costs
    - Creates master index
"""

import argparse
import json
import os
import sys
import subprocess
import re
import time
from pathlib import Path
from datetime import datetime
from pathlib import Path

# Import shared utilities
from flowscribe_utils import LLMClient, CostTracker, parse_llm_json, format_cost, format_duration
from sanitize_output_files import sanitize_output_dir

def get_directory_tree(path, max_depth=3, current_depth=0, ignore_dirs={'.git', 'node_modules', 'vendor', '.venv', '__pycache__'}):
    """
    Get directory structure as formatted text for LLM analysis.
    
    Args:
        path: Root directory path
        max_depth: Maximum depth to traverse
        current_depth: Current recursion depth
        ignore_dirs: Set of directory names to skip
    
    Returns:
        String representation of directory tree
    """
    if current_depth >= max_depth:
        return ""
    
    tree = []
    try:
        items = sorted(os.listdir(path))
        for item in items:
            # Skip hidden files and ignored directories
            if item.startswith('.') and item not in {'.github', '.gitlab'}:
                continue
            
            item_path = os.path.join(path, item)
            indent = "  " * current_depth
            
            if os.path.isdir(item_path):
                if item in ignore_dirs:
                    tree.append(f"{indent}{item}/ (skipped)")
                    continue
                    
                tree.append(f"{indent}{item}/")
                # Recurse into subdirectory
                subtree = get_directory_tree(item_path, max_depth, current_depth + 1, ignore_dirs)
                if subtree:
                    tree.append(subtree)
            else:
                # Only show PHP files for brevity
                if item.endswith('.php'):
                    tree.append(f"{indent}{item}")
    except PermissionError:
        pass
    
    return "\n".join(tree)


def generate_deptrac_config_with_llm(project_dir, project_name, domain, repo_url, llm_client):
    """
    Generate deptrac.yaml configuration using LLM based on actual project structure.
    
    Args:
        project_dir: Path to project directory
        project_name: Detected project name
        domain: Detected project domain
        repo_url: GitHub repository URL
        llm_client: Initialized LLM client
    
    Returns:
        Tuple of (success: bool, yaml_content: str, metrics: dict)
    """
    print("\n📊 Analyzing project structure...")
    
    # Get directory structure
    structure = get_directory_tree(project_dir, max_depth=3)
    
    # Count PHP files for context
    php_files = []
    for root, dirs, files in os.walk(project_dir):
        # Skip common directories
        dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', 'vendor', '.venv'}]
        for file in files:
            if file.endswith('.php'):
                php_files.append(os.path.join(root, file))
    
    print(f"  Found {len(php_files)} PHP files")
    
    prompt = f"""Analyze this PHP project and generate a deptrac.yaml configuration file.

PROJECT INFORMATION:
- Name: {project_name}
- Domain: {domain}
- Repository: {repo_url}
- PHP Files: {len(php_files)}

DIRECTORY STRUCTURE:
{structure}

TASK:
Generate a valid deptrac.yaml configuration that:

1. **Identifies main code directories**: Look for where the actual PHP code lives
   - Common patterns: src/, app/, lib/, wp-includes/, wp-admin/, etc.
   
2. **Defines logical layers**: Based on the actual structure, create 3-5 architectural layers
   - Examples: Presentation, Application, Domain, Infrastructure, Core, Admin, etc.
   - Use the actual directory names found in this project
   
3. **Sets dependency rules**: Define which layers can depend on which
   - Higher layers can depend on lower layers
   - Core/Domain should have minimal dependencies
   
4. **Uses actual paths**: Use the real directory paths from the structure above

REQUIREMENTS:
- Must be valid YAML syntax
- Use actual directory paths found in the structure
- Define at least 3 layers
- Include reasonable dependency rules
- Use directory collectors (type: directory, value: pattern)

IMPORTANT:
- Return ONLY the YAML content
- No markdown code blocks
- No explanations or comments outside the YAML
- Start directly with "deptrac:"

CRITICAL REGEX PATTERNS:
- For paths: Use format './directory-name' (with ./ prefix)
- For collectors: Use format 'directory-name/.*' (NO ./ prefix, NO trailing slash)
- CORRECT: value: wp-admin/.*     (matches ALL files in wp-admin/)
- WRONG:   value: wp-admin/.*/    (only matches nested subdirectories)
- WRONG:   value: ./wp-admin/.*   (./ prefix in collector breaks matching)

CRITICAL COLLECTOR TYPES:
- For directories: Use type "directory" with pattern "dirname/.*"
- For root-level files: Use type "glob" with pattern "*.php"
- NEVER use type "file" - it does not exist in Deptrac!

Example for root-level PHP files:
    - name: RootFiles
      collectors:
        - type: glob
          value: "*.php"

Example format:
deptrac:
  paths:
    - ./wp-includes
    - ./wp-admin
  layers:
    - name: Core
      collectors:
        - type: directory
          value: wp-includes/.*
    - name: Admin
      collectors:
        - type: directory
          value: wp-admin/.*
  ruleset:
    Core: []
    Admin:
      - Core
"""

    try:
        # Call LLM using the correct method
        result = llm_client.call(prompt)
        
        if not result:
            return False, None, {}
        
        # Extract YAML content from result
        yaml_content = result['content'].strip()
        
        # Remove markdown code blocks if LLM added them
        if yaml_content.startswith('```'):
            lines = yaml_content.split('\n')
            # Remove first line (```yaml or ```)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            yaml_content = '\n'.join(lines)
        
        # Validate it's valid YAML
        try:
            import yaml
            parsed = yaml.safe_load(yaml_content)
            if not isinstance(parsed, dict) or 'deptrac' not in parsed:
                raise ValueError("Generated YAML doesn't contain 'deptrac' key")

            # Validate paths exist            
            valid_paths = []
            paths = parsed.get('deptrac', {}).get('paths', [])
            for path in paths:
                clean_path = path.lstrip('./')
                full_path = Path(project_dir) / clean_path
                if full_path.exists():
                    valid_paths.append(path)
                else:
                    print(f"  ⚠ Removing non-existent path: {path}")
                    
            # Update with only valid paths
            parsed['deptrac']['paths'] = valid_paths
            yaml_content = yaml.dump(parsed, default_flow_style=False)

        except Exception as e:
            print(f"\n⚠ Warning: Generated YAML may be invalid: {e}")
            print("Proceeding anyway...")
        
        # Build metrics dict from result
        metrics = {
            'cost': result.get('cost', 0),
            'duration': result.get('duration', 0),
            'input_tokens': result.get('input_tokens', 0),
            'output_tokens': result.get('output_tokens', 0),
            'total_tokens': result.get('total_tokens', 0)
        }
        
        return True, yaml_content, metrics
        
    except Exception as e:
        print(f"\n✗ Failed to generate deptrac config: {e}")
        import traceback
        traceback.print_exc()
        return False, None, {}


class FlowscribeAnalyzer:
    def __init__(self, github_url, workspace_dir, output_base_dir, api_key, model):
        self.github_url = github_url
        self.workspace_dir = Path(workspace_dir)
        self.output_base_dir = Path(output_base_dir)
        self.api_key = api_key
        self.model = model
        
        # Parse GitHub URL
        self.repo_owner, self.repo_name = self.parse_github_url(github_url)
        self.project_dir = self.workspace_dir / self.repo_name
        self.output_dir = self.output_base_dir / self.repo_name
        
        # Cost tracking
        self.costs = {
            'metadata_detection': {'cost': 0.0, 'time': 0.0, 'tokens': 0},
            'deptrac_generation': {'cost': 0.0, 'time': 0.0, 'tokens': 0},
            'architecture_review': {'cost': 0.0, 'time': 0.0, 'tokens': 0},
            'level1': {'cost': 0.0, 'time': 0.0, 'tokens': 0},
            'level2': {'cost': 0.0, 'time': 0.0, 'tokens': 0},
            'level3_presentation': {'cost': 0.0, 'time': 0.0, 'tokens': 0},
            'level3_infrastructure': {'cost': 0.0, 'time': 0.0, 'tokens': 0},
            'level3_persistence': {'cost': 0.0, 'time': 0.0, 'tokens': 0},
            'level3_domain': {'cost': 0.0, 'time': 0.0, 'tokens': 0},
            'level4': {'cost': 0.0, 'time': 0.0, 'tokens': 0}
        }
        
        # Total time tracking
        self.start_time = None
        self.end_time = None
        
        # Project metadata (to be detected)
        self.project_name = None
        self.project_domain = None
    
    def parse_github_url(self, url):
        """Parse GitHub URL to extract owner and repo name"""
        # Remove .git suffix if present
        url = url.rstrip('/')
        if url.endswith('.git'):
            url = url[:-4]
        
        # Extract owner and repo
        # Supports: https://github.com/owner/repo or git@github.com:owner/repo
        patterns = [
            r'github\.com[:/]([^/]+)/([^/]+)$',
            r'github\.com[:/]([^/]+)/([^/]+)\.git$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2)
        
        raise ValueError(f"Invalid GitHub URL: {url}")
    
    def print_header(self, text):
        """Print a formatted header"""
        print(f"\n{'='*70}")
        print(f"{text}")
        print(f"{'='*70}\n")
    
    def print_step(self, step_num, total_steps, text):
        """Print a step indicator"""
        print(f"\n{'='*70}")
        print(f"[Step {step_num}/{total_steps}] {text}")
        print('-' * 70)
    
    def run_command(self, cmd, cwd=None, capture_output=True):
        """Run a shell command and return output"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                timeout=1800
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def check_project_exists(self):
        """Check if project directory exists (user should clone manually)"""
        if self.project_dir.exists():
            print(f"✓ Found project directory: {self.project_dir}")
            return True
        else:
            print(f"✗ Project directory not found: {self.project_dir}")
            print(f"\n⚠️  Please clone the repository manually first:")
            print(f"   cd {self.workspace_dir}")
            print(f"   git clone {self.github_url}")
            print(f"\n   Then run this script again.")
            return False
    
    def detect_project_metadata(self):
        """Use LLM to detect project name and domain from repository"""
        print("Analyzing repository to detect project name and domain...")
        
        step_start = time.time()
        
        # Initialize LLM client
        tracker = CostTracker(self.model)
        llm = LLMClient(self.api_key, self.model, tracker)
        
        # Read README if exists
        readme_content = ""
        for readme_name in ['README.md', 'README.txt', 'README']:
            readme_path = self.project_dir / readme_name
            if readme_path.exists():
                try:
                    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                        readme_content = f.read()[:5000]  # First 5000 chars
                    break
                except:
                    pass
        
        # Read composer.json if exists (PHP projects)
        composer_content = ""
        composer_path = self.project_dir / 'composer.json'
        if composer_path.exists():
            try:
                with open(composer_path, 'r', encoding='utf-8') as f:
                    composer_content = f.read()
            except:
                pass
        
        # Build prompt
        prompt = f"""Analyze this repository and provide metadata in JSON format.

Repository: {self.github_url}
Owner: {self.repo_owner}
Name: {self.repo_name}

README.md:
```
{readme_content if readme_content else "Not found"}
```

composer.json:
```
{composer_content if composer_content else "Not found"}
```

Based on the above, provide:

```json
{{
  "project_name": "Full project name (e.g., 'Open Journal Systems')",
  "project_domain": "Domain/industry (e.g., 'scholarly publishing', 'e-commerce', 'content management')",
  "description": "Brief 1-sentence description"
}}
```

Guidelines:
- project_name should be the official project name, not the repo slug
- project_domain should be a 2-4 word industry/domain descriptor
- If README has the name, use it; otherwise infer from repo name and description

Provide ONLY the JSON, no other text."""

        # Call LLM
        result = llm.call(prompt)
        
        step_time = time.time() - step_start
        
        if not result:
            # Fallback to repo name
            self.project_name = self.repo_name.replace('-', ' ').title()
            self.project_domain = "software"
            print(f"⚠️  Using fallback: {self.project_name} / {self.project_domain}")
            return True
        
        # Parse response
        data = parse_llm_json(result['content'])
        
        if data:
            raw_name = data.get('project_name', self.repo_name.title())
            # Keep only alphanumeric, spaces, hyphens, underscores
            self.project_name = re.sub(r'[^a-zA-Z0-9 _-]', '', raw_name)
            self.project_domain = data.get('project_domain', 'software')
            description = data.get('description', 'N/A')
            
            print(f"✓ Detected project: {self.project_name}")
            print(f"✓ Domain: {self.project_domain}")
            print(f"✓ Description: {description}")
            print(f"✓ Cost: {format_cost(result['cost'])} | Time: {format_duration(result['duration'])} | Tokens: {result['total_tokens']:,}")
            
            # Track cost
            self.costs['metadata_detection']['cost'] = result['cost']
            self.costs['metadata_detection']['time'] = result['duration']
            self.costs['metadata_detection']['tokens'] = result['total_tokens']
            
            return True
        else:
            print(f"⚠️  Could not parse LLM response, using fallback")
            self.project_name = self.repo_name.replace('-', ' ').title()
            self.project_domain = "software"
            return True
    
    def check_deptrac_config(self):
        """Generate deptrac configuration using LLM"""
        print("Analyzing project structure and generating deptrac.yaml...")
        
        step_start = time.time()
        
        # Initialize LLM client
        tracker = CostTracker(self.model)
        llm = LLMClient(self.api_key, self.model, tracker)
        
        # Generate config with LLM
        success, yaml_content, gen_metrics = generate_deptrac_config_with_llm(
            project_dir=str(self.project_dir),
            project_name=self.project_name,
            domain=self.project_domain,
            repo_url=self.github_url,
            llm_client=llm
        )
            
        if not success or not yaml_content:
            print("✗ Failed to generate deptrac.yaml")
            print("  Cannot proceed without deptrac configuration")
            return False
        
        # Save generated config
        deptrac_config_path = self.project_dir / "deptrac.yaml"
        with open(deptrac_config_path, 'w') as f:
            f.write(yaml_content)
        
        print(f"✓ Generated deptrac.yaml for {self.project_name}")
        print(f"✓ Saved to {deptrac_config_path}")
        
        step_time = time.time() - step_start
        
        # Track metrics
        self.costs['deptrac_generation']['cost'] = gen_metrics.get('cost', 0)
        self.costs['deptrac_generation']['time'] = gen_metrics.get('duration', 0)
        self.costs['deptrac_generation']['tokens'] = gen_metrics.get('total_tokens', 0)
        
        print(f"✓ Cost: ${gen_metrics.get('cost', 0):.5f} | Time: {gen_metrics.get('duration', 0):.1f}s | Tokens: {gen_metrics.get('total_tokens', 0):,}")
        
        return True
    
    def detect_code_directories(self):
        """Detect code directories in the project"""
        potential_dirs = [
            'src', 'app', 'lib', 'classes', 'controllers', 
            'models', 'pages', 'api', 'services', 'domain',
            'entities', 'repositories', 'dao', 'infrastructure',
            'mail', 'notification', 'components', 'modules'
        ]
        
        found_dirs = []
        for dir_name in potential_dirs:
            dir_path = self.project_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                # Check if it contains PHP files
                php_files = list(dir_path.glob('**/*.php'))
                if php_files:
                    found_dirs.append(dir_name)
        
        # Default if nothing found
        if not found_dirs:
            found_dirs = ['src', 'app', 'lib']
        
        print(f"  Detected code directories: {', '.join(found_dirs)}")
        return found_dirs
    
    def run_deptrac_analysis(self):
        """Run deptrac analysis"""
        print("Running deptrac dependency analysis...")
        
        deptrac_output = self.output_dir / 'deptrac-report.json'
        deptrac_config = self.project_dir / 'deptrac.yaml'
        
        # Explicitly specify config file path
        cmd = f"deptrac analyze --config-file={deptrac_config} --formatter=json --output={deptrac_output}"
        success, stdout, stderr = self.run_command(cmd, cwd=self.project_dir)
        
        # Deptrac returns non-zero exit code when violations exist
        # So check if output file exists instead of just exit code
        if deptrac_output.exists():
            # Verify it's valid JSON
            try:
                with open(deptrac_output, 'r') as f:
                    data = json.load(f)
                print(f"✓ Deptrac analysis complete: {deptrac_output}")
                print(f"  Found {len(data.get('files', {}))} files with violations")
                return True
            except json.JSONDecodeError:
                print(f"✗ Deptrac report exists but is invalid JSON")
                return False
        else:
            print(f"✗ Deptrac analysis failed: {stderr}")
            return False
    
    def generate_architecture_review(self):
        """Generate architectural review"""
        # Get review model from environment or fall back to main model
        review_model = os.environ.get('LLM_ARCH_REVIEW_MODEL', self.model)
        
        args = [
            "--project", self.project_name,
            "--domain", self.project_domain,
            "--output-dir", str(self.output_dir),
            "--api-key", self.api_key,
            "--model", review_model
        ]
        
        return self.run_script("c4-architecture-review.py", args, "Architecture review")

    def run_script(self, script_name, args, step_name):
        """Run a Python script and capture output"""
        scripts_dir = Path(__file__).parent
        script_path = scripts_dir / script_name
        
        if not script_path.exists():
            print(f"✗ Script not found: {script_path}")
            return False
        
        # Build command as list (no shell quoting needed)
        cmd_list = [
            "python3",
            str(script_path)
        ] + [str(arg) for arg in args]
        
        print(f"Running: {script_name}")
        #print(f"Command: {' '.join(cmd_list)}")  # Just for display
        # Better display with proper quoting
        import shlex
        print(f"Command: {' '.join(shlex.quote(str(x)) for x in cmd_list)}")

        try:
            result = subprocess.run(
                cmd_list,  # Pass as list, not string!
                capture_output=True,
                text=True,
                timeout=1800
            )
            
            if result.returncode == 0:
                print(f"✓ {step_name} complete")
                return True
            else:
                print(f"✗ {step_name} failed")
                print(f"STDOUT: {result.stdout}")  
                print(f"STDERR: {result.stderr}")  
                if result.stderr:
                    print(f"Error: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print(f"✗ {step_name} timed out")
            return False
        except Exception as e:
            print(f"✗ {step_name} error: {e}")
            return False
    
    def generate_level1(self):
        """Generate C4 Level 1"""
        args = [
            str(self.project_dir),
            "--project", self.project_name,
            "--domain", self.project_domain,
            "--api-key", self.api_key,
            "--model", self.model,
            "--output", str(self.output_dir / "c4-level1.md")
        ]
        
        return self.run_script("c4-level1-generator.py", args, "Level 1 generation")
    
    def generate_level2(self):
        """Generate C4 Level 2"""
        args = [
            str(self.output_dir / "deptrac-report.json"),
            "--project", self.project_name,
            "--output", str(self.output_dir / "c4-level2.md")
        ]
        
        return self.run_script("c4-level2-generator.py", args, "Level 2 generation")
    
    def generate_level3(self, layer_name):
        """Generate C4 Level 3 for a specific layer"""
        args = [
            str(self.output_dir / "deptrac-report.json"),
            "--project", self.project_name,
            "--project-dir", str(self.project_dir),  # ADD THIS LINE
            "--layer", layer_name,
            "--output", str(self.output_dir / f"c4-level3-{layer_name.lower()}.md")
        ]
        
        return self.run_script("c4-level3-generator.py", args, f"Level 3 ({layer_name})")
    
    def generate_level4(self):
        """Generate C4 Level 4"""
        args = [
            str(self.project_dir),
            str(self.output_dir / "deptrac-report.json"),
            "--project", self.project_name,
            "--domain", self.project_domain,
            "--api-key", self.api_key,
            "--model", self.model,
            "--output-dir", str(self.output_dir),
            "--max-components", "12"
        ]
        
        return self.run_script("c4-level4-generator.py", args, "Level 4 generation")
    
    def generate_master_index(self):
        """Generate master index"""
        # Don't pass cost - script doesn't accept it
        args = [
            "--project", self.project_name,
            "--output", str(self.output_dir / "README.md")
        ]
        
        return self.run_script("create-master-index.py", args, "Master index generation")
    
    def print_summary(self):
        """Print analysis summary"""
        self.end_time = time.time()
        total_time = self.end_time - self.start_time if self.start_time else 0
        
        total_cost = sum(step['cost'] for step in self.costs.values())
        total_tokens = sum(step['tokens'] for step in self.costs.values())
        
        self.print_header("Analysis Complete!")
        
        print(f"Project: {self.project_name}")
        print(f"Domain: {self.project_domain}")
        print(f"Repository: {self.github_url}")
        print(f"Output Directory: {self.output_dir}")
        print()
        
        print("Generated Documentation:")
        print(f"  ✓ C4 Level 1 (System Context)")
        print(f"  ✓ C4 Level 2 (Containers)")
        print(f"  ✓ C4 Level 3 (Components - all layers)")
        print(f"  ✓ C4 Level 4 (Code - selective)")
        print(f"  ✓ Master Index (README.md)")
        print()
        
        print("Performance Metrics:")
        print(f"  Total Time:    {total_time/60:.1f} minutes ({total_time:.1f}s)")
        print(f"  Total Cost:    ${total_cost:.4f}")
        print(f"  Total Tokens:  {total_tokens:,}")
        print(f"  Model:         {self.model}")
        print()
        
        print("Cost & Time Breakdown:")
        print(f"  {'Step':<25s} {'Cost':>10s} {'Time':>10s} {'Tokens':>10s}")
        print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*10}")
        for step, metrics in self.costs.items():
            if metrics['cost'] > 0 or metrics['time'] > 0:
                step_name = step.replace('_', ' ').title()
                print(f"  {step_name:<25s} ${metrics['cost']:>9.4f} {metrics['time']:>9.1f}s {metrics['tokens']:>10,d}")
        print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*10}")
        print(f"  {'TOTAL':<25s} ${total_cost:>9.4f} {total_time:>9.1f}s {total_tokens:>10,d}")
        print()
        
        print("Next Steps:")
        print(f"  1. Open {self.output_dir / 'README.md'}")
        print(f"  2. Review the complete C4 documentation")
        print(f"  3. Share with your team!")
        print()
        
        # Save metrics to file
        metrics_file = self.output_dir / '.flowscribe-metrics.json'
        metrics_data = {
            'project': self.project_name,
            'domain': self.project_domain,
            'repository': self.github_url,
            'analysis_date': datetime.now().isoformat(),
            'total_time_seconds': total_time,
            'total_cost_usd': total_cost,
            'total_tokens': total_tokens,
            'model': self.model,
            'breakdown': self.costs
        }
        
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        print(f"Metrics saved to: {metrics_file}")
        print()
    
    def run(self):
        """Run the complete analysis pipeline"""
        self.print_header(f"Flowscribe: Automated C4 Documentation Generator")
        
        print(f"Repository: {self.github_url}")
        print(f"Project Directory: {self.project_dir}")
        print(f"Output: {self.output_dir}")
        print()
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Start timing
        self.start_time = time.time()
        
        # Step 1: Check Project Exists
        self.print_step(1, 8, "Check Project Directory")
        if not self.check_project_exists():
            return False
        
        # Step 2: Detect Project Metadata
        self.print_step(2, 8, "Detect Project Metadata")
        if not self.detect_project_metadata():
            return False
        
        # Step 3: Generate Deptrac Config
        self.print_step(3, 8, "Generate Deptrac Configuration")
        if not self.check_deptrac_config():
            return False
        
        # Step 4: Run Deptrac Analysis
        self.print_step(4, 8, "Run Deptrac Analysis")
        if not self.run_deptrac_analysis():
            return False
        
        # Step 5: Generate C4 Level 1
        self.print_step(5, 8, "Generate C4 Level 1 (System Context)")
        if not self.generate_level1():
            print("⚠️  Level 1 generation failed, but continuing...")
        
        # Step 6: Generate C4 Level 2
        self.print_step(6, 8, "Generate C4 Level 2 (Containers)")
        if not self.generate_level2():
            return False
        
        # Step 7: Generate C4 Level 3 (all layers)
        self.print_step(7, 8, "Generate C4 Level 3 (Components)")

        # First, Check which layers actually have components
        print("\nChecking which layers have components...")
        deptrac_json = self.output_dir / "deptrac-report.json"
        deptrac_yaml = self.project_dir / "deptrac.yaml"
        layers_to_generate = []

        try:
            # Read the deptrac config to get layer definitions
            import yaml
            with open(deptrac_yaml, 'r') as f:
                deptrac_config = yaml.safe_load(f)
            
            all_layers = [layer['name'] for layer in deptrac_config.get('deptrac', {}).get('layers', [])]
            print(f"Layers defined: {', '.join(all_layers)}")
            
            # For each layer, count PHP files matching its collectors
            layer_counts = {}
            for layer_def in deptrac_config.get('deptrac', {}).get('layers', []):
                layer_name = layer_def['name']
                count = 0
                
                # Get directory patterns from collectors
                for collector in layer_def.get('collectors', []):
                    if collector.get('type') == 'directory':
                        pattern = collector.get('value', '')
                        # Convert deptrac pattern to glob pattern
                        # e.g., 'wp-admin/.*' -> 'wp-admin/**/*.php'
                        dir_pattern = pattern.replace('/.*', '/**/*.php').replace('.*', '**/*.php')
                        
                        # Count PHP files matching this pattern
                        from pathlib import Path
                        for php_file in Path(self.project_dir).glob(dir_pattern):
                            if php_file.is_file() and 'vendor' not in str(php_file) and 'test' not in str(php_file).lower():
                                count += 1
                
                layer_counts[layer_name] = count
                if count > 0:
                    layers_to_generate.append(layer_name)
                    print(f"  ✓ {layer_name}: {count} PHP files")
                else:
                    print(f"  ⊘ {layer_name}: 0 PHP files (skipping)")
            
        except Exception as e:
            print(f"⚠️  Could not analyze layers: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: generate all layers
            layers_to_generate = all_layers if 'all_layers' in locals() else ['Presentation', 'Infrastructure', 'Persistence', 'Domain']

        print(f"\nGenerating {len(layers_to_generate)} layers...")

        for layer in layers_to_generate:
            print(f"\nGenerating {layer} layer...")
            if not self.generate_level3(layer):
                print(f"⚠️  {layer} layer generation failed, but continuing...")
        
        # Step 8: Generate C4 Level 4
        self.print_step(8, 8, "Generate C4 Level 4 (Code)")
        if not self.generate_level4():
            print("⚠️  Level 4 generation failed, but continuing...")
        
        # Step 9: Generate Architecture Review
        self.print_step(9, 9, "Generate Architecture Review")
        if not self.generate_architecture_review():
            print("⚠️  Architecture review failed, but continuing...")
        
        # Step 10: Generate Master Index
        print("\nGenerating Master Index...")
        if not self.generate_master_index():
            print("⚠️  Master index generation failed")



        # Post-process: sanitize filenames and fix links (no spaces)
        try:
            print('\nSanitizing output filenames and fixing links...')
            summary = sanitize_output_dir(str(self.output_dir))
            print(f"✓ Sanitization complete: renamed {summary['renamed']} file(s)")
        except Exception as e:
            print(f"⚠️  Sanitization skipped due to error: {e}")

        # Summary
        self.print_summary()
        
        return True


def main():
    parser = argparse.ArgumentParser(
        description='Flowscribe: Automated C4 Architecture Documentation Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # First, manually clone the repository
  cd /workspace/projects
  git clone https://github.com/pkp/ojs
  
  # Then analyze it
  python3 flowscribe-analyze.py https://github.com/pkp/ojs
  
  # Specify custom workspace and output
  python3 flowscribe-analyze.py https://github.com/pkp/ojs \\
      --workspace /custom/workspace \\
      --output /custom/output

Environment Variables:
  OPENROUTER_API_KEY    OpenRouter API key (required)
  OPENROUTER_MODEL      Model to use (default: anthropic/claude-sonnet-4-20250514)

Prerequisites:
  - Repository must be manually cloned to workspace directory first
  - Git operations are NOT performed by this script
"""
    )
    
    parser.add_argument(
        'github_url',
        help='GitHub repository URL (e.g., https://github.com/owner/repo)'
    )
    
    parser.add_argument(
        '--workspace',
        default='/workspace/projects',
        help='Workspace directory for cloned repos (default: /workspace/projects)'
    )
    
    parser.add_argument(
        '--output',
        default='/workspace/output',
        help='Base output directory (default: /workspace/output)'
    )
    
    parser.add_argument(
        '--api-key',
        default=os.environ.get('OPENROUTER_API_KEY'),
        help='OpenRouter API key (or set OPENROUTER_API_KEY env var)'
    )
    
    parser.add_argument(
        '--model',
        default=os.environ.get('OPENROUTER_MODEL', 'anthropic/claude-sonnet-4-20250514'),
        help='Model to use (default: claude-sonnet-4-20250514)'
    )
    
    args = parser.parse_args()
    
    # Validate
    if not args.api_key:
        print("✗ Error: OpenRouter API key required")
        print("Set OPENROUTER_API_KEY environment variable or use --api-key")
        sys.exit(1)
    
    # Create analyzer
    analyzer = FlowscribeAnalyzer(
        github_url=args.github_url,
        workspace_dir=args.workspace,
        output_base_dir=args.output,
        api_key=args.api_key,
        model=args.model
    )
    
    # Run analysis
    success = analyzer.run()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()