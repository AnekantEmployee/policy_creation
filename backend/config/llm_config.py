"""
LLM Configuration with API Key & Model Rotation
"""

import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
import random

# Load .env from backend folder
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

logger = logging.getLogger(__name__)

os.environ["LITELLM_LOG"] = "ERROR"
logging.getLogger("LiteLLM").setLevel(logging.ERROR)

# ─── LLM Configuration ────────────────────────────────────────────────────────

# Collect all available Groq API keys
_groq_keys = []
_primary_key = os.getenv("GROQ_API_KEY", "")
if _primary_key:
    _groq_keys.append(_primary_key)
for i in range(1, 10):  # Check for GROQ_API_KEY_1 through GROQ_API_KEY_9
    key = os.getenv(f"GROQ_API_KEY_{i}", "")
    if key and key not in _groq_keys:
        _groq_keys.append(key)

GROQ_API_KEYS = _groq_keys if _groq_keys else []
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

GROQ_MODELS = [
    "groq/llama-3.3-70b-versatile",    # primary — best quality for document generation
    "groq/llama-3.1-70b-versatile",    # fallback 70b variant
    "groq/llama-3.3-70b-versatile",    # repeat to weight 70b higher
    "groq/llama-3.1-8b-instant",       # last resort — fast but produces less content
]

# Track rotation state
_api_key_index = 0
_model_index = 0

def get_next_api_key() -> Optional[str]:
    """Get next API key in rotation"""
    global _api_key_index
    if not GROQ_API_KEYS:
        return OPENAI_API_KEY
    _api_key_index = (_api_key_index + 1) % len(GROQ_API_KEYS)
    return GROQ_API_KEYS[_api_key_index]

def get_current_api_key() -> Optional[str]:
    """Get current API key without rotating"""
    if not GROQ_API_KEYS:
        return OPENAI_API_KEY
    return GROQ_API_KEYS[_api_key_index]

def get_next_model() -> str:
    """Get next model in rotation"""
    global _model_index
    _model_index = (_model_index + 1) % len(GROQ_MODELS)
    return GROQ_MODELS[_model_index]

def get_current_model() -> str:
    """Get current model without rotating"""
    return GROQ_MODELS[_model_index]

def get_random_api_key() -> Optional[str]:
    """Get random API key"""
    if not GROQ_API_KEYS:
        return OPENAI_API_KEY
    return random.choice(GROQ_API_KEYS)

def get_random_model() -> str:
    """Get random model"""
    return random.choice(GROQ_MODELS)

def get_llm_config() -> Dict[str, Any]:
    """Get current LLM configuration"""
    return {
        "provider": "groq" if GROQ_API_KEYS else "openai",
        "api_keys_count": len(GROQ_API_KEYS),
        "models": GROQ_MODELS,
        "current_model": get_current_model(),
        "current_api_key_index": _api_key_index,
    }

def get_rotation_info() -> Dict[str, Any]:
    """Get LLM rotation info for status endpoint"""
    unique_models = list(dict.fromkeys(GROQ_MODELS))   # deduplicated
    return {
        "groq_keys_available": len(GROQ_API_KEYS),
        "groq_models": unique_models,
        "groq_total_slots": len(GROQ_API_KEYS) * len(unique_models),
        "current_model": get_current_model(),
        "current_api_key_index": _api_key_index,
        "tavily_available": bool(TAVILY_API_KEY),
    }

def get_llm_with_fallback(temperature: float = 0.7):
    """Get LLM instance with fallback - uses current (non-rotating) API key"""
    from crewai import LLM
    
    if not GROQ_API_KEYS and not OPENAI_API_KEY:
        logger.warning("No LLM API keys configured, using default LLM")
    
    api_key = get_current_api_key()
    model = get_current_model()
    
    if GROQ_API_KEYS:
        logger.debug(f"Initializing Groq LLM with model: {model} (key index: {_api_key_index})")
        return LLM(model=model, api_key=api_key, temperature=temperature,
                   max_tokens=8192)
    elif OPENAI_API_KEY:
        logger.debug("Initializing OpenAI LLM fallback")
        return LLM(model="gpt-4", api_key=api_key, temperature=temperature,
                   max_tokens=8192)
    else:
        logger.warning("No LLM API keys configured, using default LLM")
        return LLM(model=model, temperature=temperature, max_tokens=8192)

def get_fresh_llm(temperature: float = 0.7, rotate: bool = True):
    """Get fresh LLM instance with API key and model rotation
    
    Args:
        temperature: Temperature for LLM
        rotate: If True, rotates both API key and model. If False, uses random selection.
    """
    from crewai import LLM
    
    if not GROQ_API_KEYS and not OPENAI_API_KEY:
        logger.warning("No LLM API keys configured, using default LLM")
    
    if rotate:
        api_key = get_next_api_key()
        model = get_next_model()
        logger.info(f"Rotating to: API key index {_api_key_index}, Model: {model}")
    else:
        api_key = get_random_api_key()
        model = get_random_model()
        logger.info(f"Random selection: Model: {model}")
    
    if GROQ_API_KEYS:
        logger.debug(f"Initializing fresh Groq LLM with model: {model} (key index: {_api_key_index})")
        return LLM(model=model, api_key=api_key, temperature=temperature,
                   max_tokens=8192)
    elif OPENAI_API_KEY:
        logger.debug("Initializing fresh OpenAI LLM fallback")
        return LLM(model="gpt-4", api_key=api_key, temperature=temperature,
                   max_tokens=8192)
    else:
        logger.warning("No LLM API keys configured, using default LLM")
        return LLM(model=model, temperature=temperature, max_tokens=8192)

def get_tavily_key() -> Optional[str]:
    """Get Tavily API key"""
    return TAVILY_API_KEY if TAVILY_API_KEY else None
