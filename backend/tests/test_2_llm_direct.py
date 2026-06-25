"""
TEST 2 — Direct LiteLLM / CrewAI LLM object
Tests get_fresh_llm() and get_llm_with_fallback() from llm_config.py.
Sends a short prompt through each model and measures latency.
"""

import sys
import time
import logging
from pathlib import Path

# Silence noisy loggers
logging.basicConfig(level=logging.WARNING, format="%(levelname)s | %(message)s")
logging.getLogger("LiteLLM").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.llm_config import (
    GROQ_API_KEYS, GROQ_MODELS,
    get_fresh_llm, get_llm_with_fallback,
)

PROMPT = "In one sentence, what is SOC 2 Type II compliance?"

print(f"\n{'='*60}")
print(f"  LLM Direct Test  ({len(GROQ_API_KEYS)} keys, {len(set(GROQ_MODELS))} unique models)")
print(f"  Total rotation slots: {len(GROQ_API_KEYS) * len(set(GROQ_MODELS))}")
print(f"{'='*60}\n")

if not GROQ_API_KEYS:
    print("ERROR: No Groq API keys loaded. Check your .env file.")
    sys.exit(1)

# ── Test A: rotate through all 6 keys once ───────────────────────────────────
print("── Test A: get_fresh_llm(rotate=True) — 6 calls, one per key ──")
passed = 0
for i in range(len(GROQ_API_KEYS)):
    try:
        llm   = get_fresh_llm(temperature=0, rotate=True)
        start = time.time()
        resp  = llm.call([{"role": "user", "content": PROMPT}])
        elapsed = time.time() - start
        text = str(resp).strip()[:100]
        print(f"  ✅  call #{i+1}  {elapsed:.2f}s  '{text}'")
        passed += 1
    except Exception as e:
        err = str(e)
        if "rate_limit" in err.lower() or "429" in err:
            print(f"  ⚠️   call #{i+1}  RATE_LIMITED: {err[:80]}")
        else:
            print(f"  ❌  call #{i+1}  ERROR: {err[:120]}")

print()

# ── Test 2: get_llm_with_fallback ─────────────────────────────────────────────
print("── Test B: get_llm_with_fallback() ──")
try:
    llm   = get_llm_with_fallback(temperature=0)
    start = time.time()
    resp  = llm.call([{"role": "user", "content": PROMPT}])
    elapsed = time.time() - start
    text = str(resp).strip()[:120]
    print(f"  ✅  {elapsed:.2f}s  '{text}'")
    passed += 1
except Exception as e:
    err = str(e)
    if "rate_limit" in err.lower() or "429" in err:
        print(f"  ⚠️   RATE_LIMITED: {err[:80]}")
    else:
        print(f"  ❌  ERROR: {err[:120]}")

print(f"\n{'='*60}")
print(f"  Passed: {passed} / {len(GROQ_API_KEYS) + 1} calls")
print(f"{'='*60}\n")
sys.exit(0 if passed > 0 else 1)
