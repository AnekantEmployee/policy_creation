"""
TEST 1 — API Key Validation
Check every Groq key with a minimal HTTP call (no CrewAI overhead).
Prints: PASS / FAIL / RATE_LIMITED per key.
"""

import os
import sys
import json
import requests
from pathlib import Path

# Load .env manually so this script works standalone
env_path = Path(__file__).resolve().parent.parent / ".env"
for line in env_path.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"'))

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
MODEL          = "llama-3.1-8b-instant"          # cheapest / fastest
PROMPT         = "Reply with exactly: OK"

# Collect keys
keys: dict[str, str] = {}
if os.getenv("GROQ_API_KEY"):
    keys["GROQ_API_KEY"] = os.environ["GROQ_API_KEY"]
for i in range(1, 10):
    k = f"GROQ_API_KEY_{i}"
    if os.getenv(k):
        keys[k] = os.environ[k]

if not keys:
    print("ERROR: No GROQ_API_KEY* variables found in .env")
    sys.exit(1)

print(f"\n{'='*60}")
print(f"  Groq API Key Validation  ({len(keys)} keys found)")
print(f"{'='*60}\n")

results = {}
for name, key in keys.items():
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 10,
        "temperature": 0,
    }
    try:
        resp = requests.post(
            GROQ_ENDPOINT,
            json=payload,
            headers={"Authorization": f"Bearer {key}"},
            timeout=15,
        )
        if resp.status_code == 200:
            reply = resp.json()["choices"][0]["message"]["content"].strip()
            print(f"  ✅  {name:<20}  PASS   reply='{reply}'")
            results[name] = "PASS"
        elif resp.status_code == 429:
            print(f"  ⚠️   {name:<20}  RATE_LIMITED (429)")
            results[name] = "RATE_LIMITED"
        elif resp.status_code == 401:
            print(f"  ❌  {name:<20}  INVALID KEY (401)")
            results[name] = "INVALID"
        else:
            detail = resp.text[:120]
            print(f"  ❌  {name:<20}  HTTP {resp.status_code}: {detail}")
            results[name] = f"HTTP_{resp.status_code}"
    except Exception as e:
        print(f"  ❌  {name:<20}  ERROR: {e}")
        results[name] = "ERROR"

print(f"\n{'='*60}")
passed        = sum(1 for v in results.values() if v == "PASS")
rate_limited  = sum(1 for v in results.values() if v == "RATE_LIMITED")
failed        = len(results) - passed - rate_limited
print(f"  Summary: {passed} PASS  |  {rate_limited} RATE_LIMITED  |  {failed} FAIL")
print(f"{'='*60}\n")
sys.exit(0 if passed > 0 else 1)
