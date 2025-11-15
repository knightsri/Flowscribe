"""
Async/Parallel Processing for C4 Diagram Generation

Provides asynchronous and parallel processing capabilities for generating
multiple C4 diagrams concurrently to improve overall performance.
"""

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import shlex


class AsyncC4Generator:
    """Async wrapper for C4 diagram generation."""

    def __init__(self, max_workers: int = 4):
        """
        Initialize async generator.

        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers

    async def run_script_async(self, script_path: Path, args: List[str]) -> Tuple[int, str, str]:
        """
        Run a Python script asynchronously.

        Args:
            script_path: Path to the Python script
            args: Command-line arguments

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        cmd = [sys.executable, str(script_path)] + args

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        return (
            process.returncode,
            stdout.decode('utf-8'),
            stderr.decode('utf-8')
        )

    async def generate_level1_async(self, workspace: Path, api_key: str,
                                   model: str, **kwargs) -> Dict[str, Any]:
        """
        Generate C4 Level 1 diagram asynchronously.

        Args:
            workspace: Project workspace path
            api_key: OpenRouter API key
            model: Model name
            **kwargs: Additional arguments

        Returns:
            Result dictionary with status and output
        """
        script_path = Path(__file__).parent / 'c4-level1-generator.py'
        args = [
            '--workspace', str(workspace),
            '--api-key', api_key,
            '--model', model
        ]

        returncode, stdout, stderr = await self.run_script_async(script_path, args)

        return {
            'level': 1,
            'success': returncode == 0,
            'stdout': stdout,
            'stderr': stderr,
            'returncode': returncode
        }

    async def generate_level2_async(self, workspace: Path, api_key: str,
                                   model: str, **kwargs) -> Dict[str, Any]:
        """
        Generate C4 Level 2 diagram asynchronously.

        Args:
            workspace: Project workspace path
            api_key: OpenRouter API key
            model: Model name
            **kwargs: Additional arguments

        Returns:
            Result dictionary with status and output
        """
        script_path = Path(__file__).parent / 'c4-level2-generator.py'
        args = [
            '--workspace', str(workspace),
            '--api-key', api_key,
            '--model', model
        ]

        returncode, stdout, stderr = await self.run_script_async(script_path, args)

        return {
            'level': 2,
            'success': returncode == 0,
            'stdout': stdout,
            'stderr': stderr,
            'returncode': returncode
        }

    async def generate_level3_async(self, workspace: Path, api_key: str,
                                   model: str, **kwargs) -> Dict[str, Any]:
        """
        Generate C4 Level 3 diagram asynchronously.

        Args:
            workspace: Project workspace path
            api_key: OpenRouter API key
            model: Model name
            **kwargs: Additional arguments

        Returns:
            Result dictionary with status and output
        """
        script_path = Path(__file__).parent / 'c4-level3-generator.py'
        args = [
            '--workspace', str(workspace),
            '--api-key', api_key,
            '--model', model
        ]

        returncode, stdout, stderr = await self.run_script_async(script_path, args)

        return {
            'level': 3,
            'success': returncode == 0,
            'stdout': stdout,
            'stderr': stderr,
            'returncode': returncode
        }

    async def generate_level4_async(self, workspace: Path, api_key: str,
                                   model: str, **kwargs) -> Dict[str, Any]:
        """
        Generate C4 Level 4 diagram asynchronously.

        Args:
            workspace: Project workspace path
            api_key: OpenRouter API key
            model: Model name
            **kwargs: Additional arguments

        Returns:
            Result dictionary with status and output
        """
        script_path = Path(__file__).parent / 'c4-level4-generator.py'
        args = [
            '--workspace', str(workspace),
            '--api-key', api_key,
            '--model', model
        ]

        returncode, stdout, stderr = await self.run_script_async(script_path, args)

        return {
            'level': 4,
            'success': returncode == 0,
            'stdout': stdout,
            'stderr': stderr,
            'returncode': returncode
        }

    async def generate_all_levels(self, workspace: Path, api_key: str,
                                  model: str, levels: Optional[List[int]] = None,
                                  **kwargs) -> List[Dict[str, Any]]:
        """
        Generate multiple C4 levels in parallel.

        Args:
            workspace: Project workspace path
            api_key: OpenRouter API key
            model: Model name
            levels: List of levels to generate (default: [1, 2, 3, 4])
            **kwargs: Additional arguments

        Returns:
            List of result dictionaries
        """
        if levels is None:
            levels = [1, 2, 3, 4]

        tasks = []

        if 1 in levels:
            tasks.append(self.generate_level1_async(workspace, api_key, model, **kwargs))
        if 2 in levels:
            tasks.append(self.generate_level2_async(workspace, api_key, model, **kwargs))
        if 3 in levels:
            tasks.append(self.generate_level3_async(workspace, api_key, model, **kwargs))
        if 4 in levels:
            tasks.append(self.generate_level4_async(workspace, api_key, model, **kwargs))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'level': levels[i] if i < len(levels) else 0,
                    'success': False,
                    'stdout': '',
                    'stderr': str(result),
                    'returncode': -1
                })
            else:
                processed_results.append(result)

        return processed_results

    def generate_all_levels_sync(self, workspace: Path, api_key: str,
                                 model: str, levels: Optional[List[int]] = None,
                                 **kwargs) -> List[Dict[str, Any]]:
        """
        Synchronous wrapper for generate_all_levels.

        Args:
            workspace: Project workspace path
            api_key: OpenRouter API key
            model: Model name
            levels: List of levels to generate (default: [1, 2, 3, 4])
            **kwargs: Additional arguments

        Returns:
            List of result dictionaries
        """
        return asyncio.run(
            self.generate_all_levels(workspace, api_key, model, levels, **kwargs)
        )


class ParallelTaskRunner:
    """Run multiple independent tasks in parallel using thread or process pools."""

    def __init__(self, max_workers: int = 4, use_processes: bool = False):
        """
        Initialize parallel task runner.

        Args:
            max_workers: Maximum number of concurrent workers
            use_processes: Use ProcessPoolExecutor instead of ThreadPoolExecutor
        """
        self.max_workers = max_workers
        self.use_processes = use_processes

    def run_parallel(self, tasks: List[callable], *args, **kwargs) -> List[Any]:
        """
        Run multiple tasks in parallel.

        Args:
            tasks: List of callable functions to execute
            *args: Positional arguments passed to each task
            **kwargs: Keyword arguments passed to each task

        Returns:
            List of results from each task
        """
        executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor

        with executor_class(max_workers=self.max_workers) as executor:
            futures = [executor.submit(task, *args, **kwargs) for task in tasks]
            results = [future.result() for future in futures]

        return results


# Example usage function
async def example_generate_all():
    """Example of how to use the async generator."""
    generator = AsyncC4Generator(max_workers=4)

    workspace = Path('/path/to/workspace')
    api_key = 'your-api-key'
    model = 'anthropic/claude-sonnet-4-20250514'

    # Generate all levels in parallel
    results = await generator.generate_all_levels(
        workspace=workspace,
        api_key=api_key,
        model=model,
        levels=[1, 2, 3, 4]
    )

    # Check results
    for result in results:
        level = result['level']
        success = result['success']
        print(f"Level {level}: {'Success' if success else 'Failed'}")

    return results


if __name__ == '__main__':
    # Example: Run all levels in parallel
    print("Async C4 Generator - Example Usage")
    print("=" * 50)

    # This would need actual workspace and API key to run
    # asyncio.run(example_generate_all())

    print("Module loaded successfully. Import to use in your scripts.")
