#!/usr/bin/env python
"""
Continuous API Monitor
Tracks API status over time and generates usage history.
Run periodically (e.g., every hour) via cron or task scheduler.
"""

import os
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import httpx

# Load .env
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# ─── Configuration ────────────────────────────────────────────────────────

HISTORY_DIR = Path(__file__).resolve().parent / "api_monitoring_history"
HISTORY_DIR.mkdir(exist_ok=True)

HISTORY_FILE = HISTORY_DIR / "api_status_history.jsonl"  # Line-delimited JSON
SUMMARY_FILE = HISTORY_DIR / "api_status_summary.json"

# ─── Helper Functions ────────────────────────────────────────────────────

def check_groq_key(api_key: str, key_name: str) -> dict:
    """Check single Groq key status"""
    try:
        with httpx.Client(timeout=5) as client:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            response = client.get(
                "https://api.groq.com/openai/v1/models",
                headers=headers
            )
            
            if response.status_code == 200:
                return {
                    "key": key_name,
                    "status": "active",
                    "http_code": 200,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    "key": key_name,
                    "status": "error",
                    "http_code": response.status_code,
                    "error": error_data.get("error", {}).get("message", "Unknown error"),
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        return {
            "key": key_name,
            "status": "connection_error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def check_openai_key() -> dict:
    """Check OpenAI key status"""
    openai_key = os.getenv("OPENAI_API_KEY", "")
    
    if not openai_key:
        return {
            "provider": "openai",
            "status": "not_configured",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        with httpx.Client(timeout=5) as client:
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            response = client.get(
                "https://api.openai.com/v1/models",
                headers=headers
            )
            
            if response.status_code == 200:
                return {
                    "provider": "openai",
                    "status": "active",
                    "http_code": 200,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    "provider": "openai",
                    "status": "error",
                    "http_code": response.status_code,
                    "error": error_data.get("error", {}).get("message", "Unknown error"),
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        return {
            "provider": "openai",
            "status": "connection_error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def check_tavily_key() -> dict:
    """Check Tavily key status"""
    tavily_key = os.getenv("TAVILY_API_KEY", "")
    
    if not tavily_key:
        return {
            "provider": "tavily",
            "status": "not_configured",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        with httpx.Client(timeout=5) as client:
            payload = {
                "api_key": tavily_key,
                "query": "test",
                "max_results": 1,
            }
            response = client.post(
                "https://api.tavily.com/search",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                return {
                    "provider": "tavily",
                    "status": "active",
                    "http_code": 200,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    "provider": "tavily",
                    "status": "error",
                    "http_code": response.status_code,
                    "error": error_data.get("message", "Unknown error"),
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        return {
            "provider": "tavily",
            "status": "connection_error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def record_check() -> dict:
    """Perform API status check and record results"""
    
    # Check Groq keys
    groq_keys = []
    primary_key = os.getenv("GROQ_API_KEY", "")
    if primary_key:
        groq_keys.append(("GROQ_API_KEY (Primary)", primary_key))
    
    for i in range(1, 10):
        key = os.getenv(f"GROQ_API_KEY_{i}", "")
        if key:
            groq_keys.append((f"GROQ_API_KEY_{i}", key))
    
    groq_results = [check_groq_key(key, name) for name, key in groq_keys]
    
    # Check other providers
    openai_result = check_openai_key()
    tavily_result = check_tavily_key()
    
    # Compile results
    record = {
        "timestamp": datetime.now().isoformat(),
        "groq": {
            "keys_checked": len(groq_keys),
            "results": groq_results,
            "active": sum(1 for r in groq_results if r.get("status") == "active"),
            "errors": sum(1 for r in groq_results if r.get("status") in ["error", "connection_error"])
        },
        "openai": openai_result,
        "tavily": tavily_result,
    }
    
    # Determine overall health
    if record["groq"]["active"] > 0 or openai_result.get("status") == "active":
        record["overall_health"] = "operational"
    elif record["groq"]["active"] == 0 and openai_result.get("status") != "active":
        record["overall_health"] = "degraded"
    else:
        record["overall_health"] = "critical"
    
    return record

def append_to_history(record: dict):
    """Append record to history file (JSONL format)"""
    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")

def generate_summary() -> dict:
    """Generate summary statistics from history"""
    
    if not HISTORY_FILE.exists():
        return {"status": "no_history"}
    
    records = []
    with open(HISTORY_FILE, "r") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    
    if not records:
        return {"status": "no_records"}
    
    # Calculate statistics
    now = datetime.now()
    last_24h = [r for r in records if 
                datetime.fromisoformat(r["timestamp"]) > now - timedelta(hours=24)]
    last_7d = [r for r in records if 
               datetime.fromisoformat(r["timestamp"]) > now - timedelta(days=7)]
    
    # Groq health
    groq_active_24h = sum(1 for r in last_24h if r["groq"]["active"] > 0)
    groq_active_7d = sum(1 for r in last_7d if r["groq"]["active"] > 0)
    
    # OpenAI health
    openai_active_24h = sum(1 for r in last_24h if r["openai"].get("status") == "active")
    openai_active_7d = sum(1 for r in last_7d if r["openai"].get("status") == "active")
    
    # Tavily health
    tavily_active_24h = sum(1 for r in last_24h if r["tavily"].get("status") == "active")
    tavily_active_7d = sum(1 for r in last_7d if r["tavily"].get("status") == "active")
    
    # Overall health trend
    overall_health_24h = [r["overall_health"] for r in last_24h]
    operational_count = overall_health_24h.count("operational")
    degraded_count = overall_health_24h.count("degraded")
    critical_count = overall_health_24h.count("critical")
    
    summary = {
        "generated": datetime.now().isoformat(),
        "total_records": len(records),
        "records_24h": len(last_24h),
        "records_7d": len(last_7d),
        "groq": {
            "uptime_24h": f"{(groq_active_24h / len(last_24h) * 100):.1f}%" if last_24h else "N/A",
            "uptime_7d": f"{(groq_active_7d / len(last_7d) * 100):.1f}%" if last_7d else "N/A",
        },
        "openai": {
            "uptime_24h": f"{(openai_active_24h / len(last_24h) * 100):.1f}%" if last_24h else "N/A",
            "uptime_7d": f"{(openai_active_7d / len(last_7d) * 100):.1f}%" if last_7d else "N/A",
        },
        "tavily": {
            "uptime_24h": f"{(tavily_active_24h / len(last_24h) * 100):.1f}%" if last_24h else "N/A",
            "uptime_7d": f"{(tavily_active_7d / len(last_7d) * 100):.1f}%" if last_7d else "N/A",
        },
        "overall_health_trend_24h": {
            "operational": operational_count,
            "degraded": degraded_count,
            "critical": critical_count,
        },
        "latest_record": records[-1] if records else None,
    }
    
    return summary

def main():
    """Main execution"""
    print(f"API Continuous Monitor - {datetime.now().isoformat()}")
    print(f"Recording to: {HISTORY_FILE}")
    
    # Perform check
    record = record_check()
    
    # Append to history
    append_to_history(record)
    print(f"✓ Status recorded")
    
    # Generate summary
    summary = generate_summary()
    with open(SUMMARY_FILE, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Summary generated")
    
    # Print current status
    print(f"\nCurrent Status: {record['overall_health'].upper()}")
    print(f"Groq Keys Active: {record['groq']['active']}/{record['groq']['keys_checked']}")
    print(f"OpenAI: {record['openai'].get('status', 'unknown')}")
    print(f"Tavily: {record['tavily'].get('status', 'unknown')}")
    
    # Print 24h trend
    if summary.get("records_24h", 0) > 1:
        print(f"\n24-Hour Trend:")
        print(f"  Operational: {summary['overall_health_trend_24h']['operational']} checks")
        print(f"  Degraded: {summary['overall_health_trend_24h']['degraded']} checks")
        print(f"  Critical: {summary['overall_health_trend_24h']['critical']} checks")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
