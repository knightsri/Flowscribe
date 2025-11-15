#!/usr/bin/env python3
"""
Health Check Script for Flowscribe

Verifies that all dependencies, configurations, and services are working correctly.
Can be used for Docker health checks, monitoring, and debugging.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json
import argparse


class HealthCheck:
    """Comprehensive health check for Flowscribe."""

    def __init__(self, verbose: bool = False):
        """
        Initialize health check.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.results: Dict[str, Any] = {}

    def check_python_version(self) -> Tuple[bool, str]:
        """
        Check Python version.

        Returns:
            Tuple of (success, message)
        """
        version = sys.version_info
        required_major = 3
        required_minor = 8

        if version.major >= required_major and version.minor >= required_minor:
            return True, f"Python {version.major}.{version.minor}.{version.micro}"
        else:
            return False, f"Python {version.major}.{version.minor}.{version.micro} (requires >= 3.8)"

    def check_api_key(self) -> Tuple[bool, str]:
        """
        Check if API key is configured.

        Returns:
            Tuple of (success, message)
        """
        api_key = os.getenv('OPENROUTER_API_KEY')

        if not api_key:
            return False, "OPENROUTER_API_KEY not set"

        if not api_key.startswith('sk-or-v1-'):
            return False, "Invalid API key format"

        # Mask most of the key
        masked_key = api_key[:12] + '...' + api_key[-4:] if len(api_key) > 16 else 'set'
        return True, f"API key configured ({masked_key})"

    def check_workspace(self) -> Tuple[bool, str]:
        """
        Check if workspace directory is accessible.

        Returns:
            Tuple of (success, message)
        """
        # Check common workspace locations
        possible_workspaces = [
            os.getenv('FLOWSCRIBE_WORKSPACE'),
            '/workspace',
            './projects',
            './workspace'
        ]

        for workspace in possible_workspaces:
            if workspace and Path(workspace).exists():
                workspace_path = Path(workspace)
                if os.access(workspace_path, os.R_OK | os.W_OK):
                    return True, f"Workspace accessible: {workspace_path}"

        return False, "No accessible workspace found"

    def check_output_directory(self) -> Tuple[bool, str]:
        """
        Check if output directory exists and is writable.

        Returns:
            Tuple of (success, message)
        """
        output_dir = Path('./output')

        if not output_dir.exists():
            return False, f"Output directory does not exist: {output_dir}"

        if not os.access(output_dir, os.W_OK):
            return False, f"Output directory not writable: {output_dir}"

        return True, f"Output directory accessible: {output_dir}"

    def check_dependencies(self) -> Tuple[bool, str]:
        """
        Check if required Python packages are installed.

        Returns:
            Tuple of (success, message)
        """
        required_packages = [
            'yaml',      # pyyaml
            'requests',  # requests
        ]

        optional_packages = [
            'pyan',      # pyan3
            'pylint',    # pylint
            'networkx',  # networkx
            'matplotlib' # matplotlib
        ]

        missing = []
        missing_optional = []

        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)

        for package in optional_packages:
            try:
                __import__(package)
            except ImportError:
                missing_optional.append(package)

        if missing:
            return False, f"Missing required packages: {', '.join(missing)}"

        if missing_optional:
            msg = f"All required packages installed (optional missing: {', '.join(missing_optional)})"
        else:
            msg = "All packages installed"

        return True, msg

    def check_scripts(self) -> Tuple[bool, str]:
        """
        Check if core scripts exist.

        Returns:
            Tuple of (success, message)
        """
        scripts_dir = Path(__file__).parent
        required_scripts = [
            'flowscribe_utils.py',
            'c4-level1-generator.py',
            'c4-level2-generator.py',
            'c4-level3-generator.py',
            'c4-level4-generator.py',
        ]

        missing = []
        for script in required_scripts:
            script_path = scripts_dir / script
            if not script_path.exists():
                missing.append(script)

        if missing:
            return False, f"Missing scripts: {', '.join(missing)}"

        return True, f"All core scripts present ({len(required_scripts)} scripts)"

    def check_prompts(self) -> Tuple[bool, str]:
        """
        Check if prompt templates exist.

        Returns:
            Tuple of (success, message)
        """
        prompts_dir = Path('./docs/prompts')

        if not prompts_dir.exists():
            return False, f"Prompts directory not found: {prompts_dir}"

        prompt_files = list(prompts_dir.glob('*.md'))

        if not prompt_files:
            return False, "No prompt templates found"

        return True, f"Found {len(prompt_files)} prompt templates"

    def check_docker_env(self) -> Tuple[bool, str]:
        """
        Check if running in Docker environment.

        Returns:
            Tuple of (success, message)
        """
        # Check for common Docker indicators
        docker_indicators = [
            Path('/.dockerenv').exists(),
            os.getenv('DOCKER_CONTAINER') == 'true',
            Path('/proc/1/cgroup').exists() and 'docker' in Path('/proc/1/cgroup').read_text()
        ]

        in_docker = any(docker_indicators)

        if in_docker:
            return True, "Running in Docker container"
        else:
            return True, "Not running in Docker (OK for local development)"

    def check_disk_space(self) -> Tuple[bool, str]:
        """
        Check available disk space.

        Returns:
            Tuple of (success, message)
        """
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')

            free_gb = free / (1024 ** 3)
            total_gb = total / (1024 ** 3)
            percent_free = (free / total) * 100

            if free_gb < 1:
                return False, f"Low disk space: {free_gb:.2f} GB free ({percent_free:.1f}%)"

            return True, f"Disk space OK: {free_gb:.2f} GB free of {total_gb:.2f} GB ({percent_free:.1f}%)"
        except Exception as e:
            return False, f"Failed to check disk space: {e}"

    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all health checks.

        Returns:
            Dictionary with check results
        """
        checks = [
            ('python_version', self.check_python_version),
            ('api_key', self.check_api_key),
            ('workspace', self.check_workspace),
            ('output_directory', self.check_output_directory),
            ('dependencies', self.check_dependencies),
            ('scripts', self.check_scripts),
            ('prompts', self.check_prompts),
            ('docker_env', self.check_docker_env),
            ('disk_space', self.check_disk_space),
        ]

        results = {}
        all_passed = True

        for check_name, check_func in checks:
            try:
                success, message = check_func()
                results[check_name] = {
                    'status': 'pass' if success else 'fail',
                    'message': message
                }
                if not success:
                    all_passed = False
            except Exception as e:
                results[check_name] = {
                    'status': 'error',
                    'message': f"Check failed with error: {e}"
                }
                all_passed = False

        self.results = {
            'overall_status': 'healthy' if all_passed else 'unhealthy',
            'timestamp': self._get_timestamp(),
            'checks': results
        }

        return self.results

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()

    def print_results(self, json_output: bool = False) -> None:
        """
        Print health check results.

        Args:
            json_output: Output as JSON instead of formatted text
        """
        if json_output:
            print(json.dumps(self.results, indent=2))
            return

        print("=" * 60)
        print("Flowscribe Health Check")
        print("=" * 60)
        print()

        for check_name, result in self.results['checks'].items():
            status = result['status']
            message = result['message']

            # Status indicator
            if status == 'pass':
                indicator = "✓"
                color = '\033[92m'  # Green
            elif status == 'fail':
                indicator = "✗"
                color = '\033[91m'  # Red
            else:
                indicator = "!"
                color = '\033[93m'  # Yellow

            reset = '\033[0m'

            print(f"{color}{indicator}{reset} {check_name.replace('_', ' ').title()}")
            if self.verbose or status != 'pass':
                print(f"  {message}")

        print()
        print("=" * 60)
        overall = self.results['overall_status']
        if overall == 'healthy':
            print(f"\033[92m✓ Overall Status: HEALTHY\033[0m")
        else:
            print(f"\033[91m✗ Overall Status: UNHEALTHY\033[0m")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Health check for Flowscribe'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--exit-code',
        action='store_true',
        help='Exit with non-zero code if unhealthy'
    )

    args = parser.parse_args()

    health = HealthCheck(verbose=args.verbose)
    results = health.run_all_checks()
    health.print_results(json_output=args.json)

    # Exit with appropriate code
    if args.exit_code:
        sys.exit(0 if results['overall_status'] == 'healthy' else 1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
