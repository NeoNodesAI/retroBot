"""LLM model factory for managing different providers."""
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings
from src.utils.logger import logger


def get_model(
    model_name: Optional[str] = None,
    provider: Optional[str] = None,
    fast_mode: bool = False
):
    """
    Get LLM model instance.
    
    Args:
        model_name: Model name (e.g., "claude-sonnet-4-20250514")
        provider: Provider name ("openai", "anthropic", "gemini")
        fast_mode: Use fast model for simple queries
    
    Returns:
        LLM model instance
    """
    # Determine model and provider
    if fast_mode and settings.enable_hybrid_models:
        model_name = model_name or settings.fast_model
    else:
        model_name = model_name or settings.default_model
    
    provider = provider or settings.llm_provider
    
    logger.info(f"Getting model: {model_name} (provider: {provider})")
    
    # Create model instance
    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        return ChatAnthropic(
            model=model_name,
            anthropic_api_key=settings.anthropic_api_key,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )
    
    elif provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        return ChatOpenAI(
            model=model_name,
            openai_api_key=settings.openai_api_key,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )
    
    elif provider == "gemini":
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY not set")
        
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.google_api_key,
            temperature=settings.temperature,
            max_output_tokens=settings.max_tokens,
        )
    
    else:
        raise ValueError(f"Unknown provider: {provider}")

