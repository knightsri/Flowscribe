#!/usr/bin/env python3
"""
LLM Model Definitions

Centralized model names and pricing information for Flowscribe.
"""

from enum import Enum
from typing import Dict, NamedTuple


class ModelPricing(NamedTuple):
    """Pricing information for an LLM model"""
    input_cost_per_1m: float  # Cost per 1M input tokens in USD
    output_cost_per_1m: float  # Cost per 1M output tokens in USD
    context_window: int  # Maximum context window size in tokens


class LLMModel(str, Enum):
    """
    Enumeration of supported LLM models.

    Each model is identified by its OpenRouter model identifier.
    """

    # Anthropic Claude Models
    CLAUDE_SONNET_4_5 = "anthropic/claude-sonnet-4-5-20241022"
    CLAUDE_SONNET_4 = "anthropic/claude-sonnet-4-20250514"
    CLAUDE_OPUS_4 = "anthropic/claude-opus-4"
    CLAUDE_SONNET_3_5 = "anthropic/claude-3.5-sonnet"
    CLAUDE_HAIKU_3_5 = "anthropic/claude-3.5-haiku"

    # OpenAI GPT Models
    GPT_4_TURBO = "openai/gpt-4-turbo"
    GPT_4 = "openai/gpt-4"
    GPT_4O = "openai/gpt-4o"
    GPT_4O_MINI = "openai/gpt-4o-mini"

    # X.AI Models
    GROK_2 = "x-ai/grok-2"
    GROK_CODE_FAST = "x-ai/grok-code-fast-1"

    # Google Models
    GEMINI_PRO_1_5 = "google/gemini-pro-1.5"
    GEMINI_FLASH_1_5 = "google/gemini-flash-1.5"

    # Meta Models
    LLAMA_3_1_70B = "meta-llama/llama-3.1-70b-instruct"
    LLAMA_3_1_8B = "meta-llama/llama-3.1-8b-instruct"

    def __str__(self) -> str:
        """Return the model identifier string"""
        return self.value


# Model pricing database (as of October 2025)
# Note: These are fallback prices. Actual costs are retrieved from OpenRouter API usage data.
MODEL_PRICING: Dict[LLMModel, ModelPricing] = {
    # Anthropic Claude Models
    LLMModel.CLAUDE_SONNET_4_5: ModelPricing(3.0, 15.0, 200_000),
    LLMModel.CLAUDE_SONNET_4: ModelPricing(3.0, 15.0, 200_000),
    LLMModel.CLAUDE_OPUS_4: ModelPricing(15.0, 75.0, 200_000),
    LLMModel.CLAUDE_SONNET_3_5: ModelPricing(3.0, 15.0, 200_000),
    LLMModel.CLAUDE_HAIKU_3_5: ModelPricing(0.25, 1.25, 200_000),

    # OpenAI GPT Models
    LLMModel.GPT_4_TURBO: ModelPricing(10.0, 30.0, 128_000),
    LLMModel.GPT_4: ModelPricing(30.0, 60.0, 8_192),
    LLMModel.GPT_4O: ModelPricing(2.5, 10.0, 128_000),
    LLMModel.GPT_4O_MINI: ModelPricing(0.15, 0.6, 128_000),

    # X.AI Models
    LLMModel.GROK_2: ModelPricing(2.0, 10.0, 128_000),
    LLMModel.GROK_CODE_FAST: ModelPricing(0.5, 1.5, 128_000),

    # Google Models
    LLMModel.GEMINI_PRO_1_5: ModelPricing(1.25, 5.0, 1_000_000),
    LLMModel.GEMINI_FLASH_1_5: ModelPricing(0.075, 0.3, 1_000_000),

    # Meta Models
    LLMModel.LLAMA_3_1_70B: ModelPricing(0.9, 0.9, 128_000),
    LLMModel.LLAMA_3_1_8B: ModelPricing(0.2, 0.2, 128_000),
}


# Recommended models for different use cases
class RecommendedModels:
    """Recommended models for different Flowscribe operations"""

    # High-quality analysis (best accuracy, higher cost)
    ARCHITECTURE_REVIEW = LLMModel.CLAUDE_SONNET_4_5
    LEVEL_4_GENERATION = LLMModel.CLAUDE_SONNET_4

    # Balanced performance (good accuracy, moderate cost)
    LEVEL_1_GENERATION = LLMModel.GPT_4O
    LEVEL_2_GENERATION = LLMModel.GPT_4O
    LEVEL_3_GENERATION = LLMModel.GPT_4O

    # Fast and economical (acceptable accuracy, low cost)
    QUICK_ANALYSIS = LLMModel.GPT_4O_MINI
    BATCH_PROCESSING = LLMModel.GROK_CODE_FAST


def get_model_pricing(model: str) -> ModelPricing:
    """
    Get pricing information for a model

    Args:
        model: Model identifier string

    Returns:
        ModelPricing object with cost and context window info

    Raises:
        ValueError: If model is not found in pricing database
    """
    # Try to match as LLMModel enum
    try:
        model_enum = LLMModel(model)
        if model_enum in MODEL_PRICING:
            return MODEL_PRICING[model_enum]
    except ValueError:
        pass

    # Try string match against enum values
    for model_enum, pricing in MODEL_PRICING.items():
        if model_enum.value == model:
            return pricing

    raise ValueError(
        f"Model '{model}' not found in pricing database. "
        f"Available models: {', '.join(m.value for m in LLMModel)}"
    )


def is_supported_model(model: str) -> bool:
    """
    Check if a model is supported

    Args:
        model: Model identifier string

    Returns:
        True if model is supported, False otherwise
    """
    try:
        get_model_pricing(model)
        return True
    except ValueError:
        return False


def list_supported_models() -> list[str]:
    """
    Get list of all supported model identifiers

    Returns:
        List of model identifier strings
    """
    return [model.value for model in LLMModel]


def get_recommended_model(use_case: str) -> LLMModel:
    """
    Get recommended model for a specific use case

    Args:
        use_case: One of "architecture_review", "level1", "level2", "level3", "level4", "quick", "batch"

    Returns:
        Recommended LLMModel for the use case

    Raises:
        ValueError: If use_case is not recognized
    """
    use_case_map = {
        "architecture_review": RecommendedModels.ARCHITECTURE_REVIEW,
        "level1": RecommendedModels.LEVEL_1_GENERATION,
        "level2": RecommendedModels.LEVEL_2_GENERATION,
        "level3": RecommendedModels.LEVEL_3_GENERATION,
        "level4": RecommendedModels.LEVEL_4_GENERATION,
        "quick": RecommendedModels.QUICK_ANALYSIS,
        "batch": RecommendedModels.BATCH_PROCESSING,
    }

    if use_case not in use_case_map:
        raise ValueError(
            f"Unknown use case: {use_case}. "
            f"Valid use cases: {', '.join(use_case_map.keys())}"
        )

    return use_case_map[use_case]
