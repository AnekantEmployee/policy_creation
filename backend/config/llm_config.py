"""
LLM Configuration with API Key + Model Rotation
Supports: Groq (key × model rotation)
"""

import os
import logging
import itertools
import time
from typing import Optional, List, Tuple
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

logger = logging.getLogger(__name__)

os.environ["LITELLM_LOG"] = "ERROR"
logging.getLogger("LiteLLM").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)

GROQ_MODELS = [
    "groq/llama-3.3-70b-versatile",
    "groq/llama-3.1-8b-instant",
    "groq/qwen/qwen3-32b",
]

GROQ_API_KEYS: List[str] = [
    v for k, v in sorted(os.environ.items())
    if k.startswith("GROQ_API_KEY") and v
]

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


class RotationState:
    def __init__(self):
        self._slots: List[Tuple[str, str]] = [
            (key, model)
            for key in GROQ_API_KEYS
            for model in GROQ_MODELS
        ]
        self._cycle = itertools.cycle(self._slots) if self._slots else iter([])
        logger.info(f"RotationState: {len(GROQ_API_KEYS)} Groq keys × {len(GROQ_MODELS)} models = {len(self._slots)} slots")

    def next_slot(self) -> Optional[Tuple[str, str]]:
        if not self._slots:
            return None
        return next(self._cycle)

    @property
    def total_slots(self) -> int:
        return len(self._slots)

    def info(self) -> dict:
        return {
            "groq_keys": len(GROQ_API_KEYS),
            "groq_models": GROQ_MODELS,
            "groq_total_slots": self.total_slots,
            "tavily_available": bool(TAVILY_API_KEY),
        }


_rotation = RotationState()


_RATE_LIMIT_SIGNALS = ["429", "rate_limit", "rate_limit_exceeded", "tokens", "503", "token"]


def get_llm(temperature: float = 0.3) -> LLM:
    slot = _rotation.next_slot()
    if not slot:
        raise RuntimeError("No Groq API keys configured")
    key, model = slot
    os.environ["GROQ_API_KEY"] = key
    logger.debug(f"Using Groq: {model}")
    return LLM(model=model, temperature=temperature, api_key=key)


def get_llm_with_fallback(temperature: float = 0.3, max_attempts: int = 10) -> LLM:
    """Rotate through all key×model slots on rate-limit/token errors."""
    errors = []
    attempts = min(max_attempts, max(_rotation.total_slots, 1))
    for _ in range(attempts):
        try:
            return get_llm(temperature=temperature)
        except Exception as e:
            err = str(e)
            if any(sig in err.lower() for sig in _RATE_LIMIT_SIGNALS):
                errors.append(err[:120])
                time.sleep(2)
                continue
            raise
    raise RuntimeError(f"All Groq slots exhausted. Last errors: {errors[-3:]}")


def get_fresh_llm(temperature: float = 0.3) -> LLM:
    """Always rotate to the next slot — use this on each retry."""
    return get_llm(temperature=temperature)


def get_rotation_info() -> dict:
    return _rotation.info()


def get_tavily_key() -> str:
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY not set in environment")
    return TAVILY_API_KEY
