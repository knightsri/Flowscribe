#!/usr/bin/env python3
"""
Configuration Schema

Defines dataclasses for Flowscribe configuration to ensure type safety
and provide a clear structure for configuration management.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
import os


@dataclass
class APIConfig:
    """OpenRouter API configuration"""
    api_key: str
    model: str = "anthropic/claude-sonnet-4-20250514"
    timeout: int = 180  # seconds
    max_retries: int = 3
    retry_delay: int = 5  # seconds

    @classmethod
    def from_env(cls) -> "APIConfig":
        """
        Create APIConfig from environment variables

        Returns:
            APIConfig instance

        Raises:
            ValueError: If required environment variables are not set
        """
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")

        model = os.environ.get('OPENROUTER_MODEL', 'anthropic/claude-sonnet-4-20250514')

        return cls(
            api_key=api_key,
            model=model,
            timeout=int(os.environ.get('OPENROUTER_TIMEOUT', '180')),
            max_retries=int(os.environ.get('OPENROUTER_MAX_RETRIES', '3')),
            retry_delay=int(os.environ.get('OPENROUTER_RETRY_DELAY', '5'))
        )


@dataclass
class CostTrackingConfig:
    """Cost tracking configuration"""
    enable_tracking: bool = True
    usage_first: bool = True  # Use OpenRouter usage data as source of truth
    fallback_input_cost_per_1m: float = 3.0  # USD
    fallback_output_cost_per_1m: float = 15.0  # USD
    save_metrics: bool = True
    metrics_format: str = "json"  # json, csv, both

    @classmethod
    def from_env(cls) -> "CostTrackingConfig":
        """Create CostTrackingConfig from environment variables"""
        return cls(
            enable_tracking=os.environ.get('COST_TRACKING_ENABLED', 'true').lower() == 'true',
            usage_first=os.environ.get('COST_USAGE_FIRST', 'true').lower() == 'true',
            fallback_input_cost_per_1m=float(os.environ.get('FALLBACK_INPUT_COST_PER_1M', '3.0')),
            fallback_output_cost_per_1m=float(os.environ.get('FALLBACK_OUTPUT_COST_PER_1M', '15.0')),
            save_metrics=os.environ.get('SAVE_METRICS', 'true').lower() == 'true',
            metrics_format=os.environ.get('METRICS_FORMAT', 'json')
        )


@dataclass
class FileProcessingConfig:
    """File processing configuration"""
    max_file_size: int = 50_000  # bytes
    max_files_to_analyze: int = 25
    excluded_dirs: list[str] = field(default_factory=lambda: [
        '.git', 'node_modules', 'vendor', '.venv', '__pycache__',
        'build', 'dist', '.cache', 'coverage'
    ])
    included_patterns: list[str] = field(default_factory=lambda: [
        'readme.*', 'composer.json', 'package.json', 'requirements.txt',
        'Gemfile', 'go.mod', 'docker-compose.y*ml', 'Dockerfile*',
        '.env.example', 'config.example.*'
    ])

    @classmethod
    def from_env(cls) -> "FileProcessingConfig":
        """Create FileProcessingConfig from environment variables"""
        return cls(
            max_file_size=int(os.environ.get('MAX_FILE_SIZE', '50000')),
            max_files_to_analyze=int(os.environ.get('MAX_FILES_TO_ANALYZE', '25'))
        )


@dataclass
class ProjectConfig:
    """Project-specific configuration"""
    name: str
    domain: str
    github_url: Optional[str] = None
    project_dir: Optional[Path] = None
    description: Optional[str] = None

    def __post_init__(self):
        """Validate and convert project_dir to Path"""
        if self.project_dir and not isinstance(self.project_dir, Path):
            self.project_dir = Path(self.project_dir)


@dataclass
class OutputConfig:
    """Output configuration"""
    output_dir: Path
    format: str = "markdown"  # markdown, html, pdf
    include_mermaid: bool = True
    include_metrics: bool = True
    sanitize_paths: bool = True
    create_master_index: bool = True

    def __post_init__(self):
        """Validate and convert output_dir to Path"""
        if not isinstance(self.output_dir, Path):
            self.output_dir = Path(self.output_dir)

    @classmethod
    def from_args(cls, output_dir: str, **kwargs) -> "OutputConfig":
        """
        Create OutputConfig from arguments

        Args:
            output_dir: Output directory path
            **kwargs: Additional configuration options

        Returns:
            OutputConfig instance
        """
        return cls(
            output_dir=Path(output_dir),
            format=kwargs.get('format', 'markdown'),
            include_mermaid=kwargs.get('include_mermaid', True),
            include_metrics=kwargs.get('include_metrics', True),
            sanitize_paths=kwargs.get('sanitize_paths', True),
            create_master_index=kwargs.get('create_master_index', True)
        )


@dataclass
class C4GenerationConfig:
    """C4 diagram generation configuration"""
    generate_level1: bool = True
    generate_level2: bool = True
    generate_level3: bool = True
    generate_level4: bool = True
    generate_architecture_review: bool = True

    max_components_level4: int = 12
    max_layers_level3: int = 10

    level1_model: Optional[str] = None
    level2_model: Optional[str] = None
    level3_model: Optional[str] = None
    level4_model: Optional[str] = None
    review_model: Optional[str] = None

    @classmethod
    def from_env(cls) -> "C4GenerationConfig":
        """Create C4GenerationConfig from environment variables"""
        base_model = os.environ.get('OPENROUTER_MODEL', 'anthropic/claude-sonnet-4-20250514')

        return cls(
            generate_level1=os.environ.get('GENERATE_LEVEL1', 'true').lower() == 'true',
            generate_level2=os.environ.get('GENERATE_LEVEL2', 'true').lower() == 'true',
            generate_level3=os.environ.get('GENERATE_LEVEL3', 'true').lower() == 'true',
            generate_level4=os.environ.get('GENERATE_LEVEL4', 'true').lower() == 'true',
            generate_architecture_review=os.environ.get('GENERATE_REVIEW', 'true').lower() == 'true',
            max_components_level4=int(os.environ.get('MAX_COMPONENTS_LEVEL4', '12')),
            max_layers_level3=int(os.environ.get('MAX_LAYERS_LEVEL3', '10')),
            level1_model=os.environ.get('LLM_LEVEL1_MODEL', base_model),
            level2_model=os.environ.get('LLM_LEVEL2_MODEL', base_model),
            level3_model=os.environ.get('LLM_LEVEL3_MODEL', base_model),
            level4_model=os.environ.get('LLM_LEVEL4_MODEL', base_model),
            review_model=os.environ.get('LLM_ARCH_REVIEW_MODEL', base_model)
        )


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    log_to_file: bool = False
    log_file_path: Optional[Path] = None
    sanitize_errors: bool = True

    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """Create LoggingConfig from environment variables"""
        log_file = os.environ.get('LOG_FILE_PATH')
        return cls(
            level=os.environ.get('LOG_LEVEL', 'INFO').upper(),
            log_to_file=os.environ.get('LOG_TO_FILE', 'false').lower() == 'true',
            log_file_path=Path(log_file) if log_file else None,
            sanitize_errors=os.environ.get('SANITIZE_ERRORS', 'true').lower() == 'true'
        )


@dataclass
class FlowscribeConfig:
    """Complete Flowscribe configuration"""
    api: APIConfig
    project: ProjectConfig
    output: OutputConfig
    cost_tracking: CostTrackingConfig = field(default_factory=CostTrackingConfig)
    file_processing: FileProcessingConfig = field(default_factory=FileProcessingConfig)
    c4_generation: C4GenerationConfig = field(default_factory=C4GenerationConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def from_env_and_args(
        cls,
        project_name: str,
        project_domain: str,
        output_dir: str,
        project_dir: Optional[str] = None,
        github_url: Optional[str] = None
    ) -> "FlowscribeConfig":
        """
        Create FlowscribeConfig from environment variables and command-line arguments

        Args:
            project_name: Name of the project being analyzed
            project_domain: Domain/category of the project
            output_dir: Output directory for generated documentation
            project_dir: Project directory path (optional)
            github_url: GitHub repository URL (optional)

        Returns:
            FlowscribeConfig instance

        Raises:
            ValueError: If required configuration is missing
        """
        return cls(
            api=APIConfig.from_env(),
            project=ProjectConfig(
                name=project_name,
                domain=project_domain,
                github_url=github_url,
                project_dir=Path(project_dir) if project_dir else None
            ),
            output=OutputConfig.from_args(output_dir),
            cost_tracking=CostTrackingConfig.from_env(),
            file_processing=FileProcessingConfig.from_env(),
            c4_generation=C4GenerationConfig.from_env(),
            logging=LoggingConfig.from_env()
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary

        Returns:
            Dictionary representation of configuration
        """
        return {
            'api': {
                'model': self.api.model,
                'timeout': self.api.timeout,
                'max_retries': self.api.max_retries,
                'retry_delay': self.api.retry_delay,
            },
            'project': {
                'name': self.project.name,
                'domain': self.project.domain,
                'github_url': self.project.github_url,
                'project_dir': str(self.project.project_dir) if self.project.project_dir else None,
            },
            'output': {
                'output_dir': str(self.output.output_dir),
                'format': self.output.format,
                'include_mermaid': self.output.include_mermaid,
                'include_metrics': self.output.include_metrics,
            },
            'cost_tracking': {
                'enable_tracking': self.cost_tracking.enable_tracking,
                'usage_first': self.cost_tracking.usage_first,
                'save_metrics': self.cost_tracking.save_metrics,
            },
            'c4_generation': {
                'generate_level1': self.c4_generation.generate_level1,
                'generate_level2': self.c4_generation.generate_level2,
                'generate_level3': self.c4_generation.generate_level3,
                'generate_level4': self.c4_generation.generate_level4,
                'generate_architecture_review': self.c4_generation.generate_architecture_review,
            }
        }
