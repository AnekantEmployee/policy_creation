#!/usr/bin/env python
"""
API Usage Monitor
Retrieves usage information, rate limits, and token statistics for all configured APIs.
Helps diagnose API restriction issues.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import httpx

# Load .env
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# ─── Color output for terminal ────────────────────────────────────────────────
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_section(title: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")

def print_success(msg: str):
    print(f"{Colors.GREEN}✓{Colors.RESET} {msg}")

def print_error(msg: str):
    print(f"{Colors.RED}✗{Colors.RESET} {msg}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {msg}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {msg}")

# ─── GROQ API Usage ───────────────────────────────────────────────────────────

def check_groq_usage() -> Dict[str, Any]:
    """Check Groq API usage and rate limits"""
    print_section("GROQ API USAGE")
    
    groq_keys = []
    primary_key = os.getenv("GROQ_API_KEY", "")
    if primary_key:
        groq_keys.append(("GROQ_API_KEY (Primary)", primary_key))
    
    for i in range(1, 10):
        key = os.getenv(f"GROQ_API_KEY_{i}", "")
        if key:
            groq_keys.append((f"GROQ_API_KEY_{i}", key))
    
    if not groq_keys:
        print_error("No Groq API keys found in .env")
        return {"status": "error", "message": "No API keys configured"}
    
    print_info(f"Found {len(groq_keys)} Groq API key(s)")
    
    results = []
    
    for key_name, api_key in groq_keys:
        print(f"\n{Colors.BOLD}Testing {key_name}...{Colors.RESET}")
        
        try:
            # Test basic connectivity
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Try to get API status
            with httpx.Client(timeout=10) as client:
                # 1. Test: Simple models list call
                print("  [1/3] Testing basic authentication...")
                response = client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers=headers,
                    timeout=10
                )
                
                print_info(f"Status Code: {response.status_code}")
                
                basic_auth_ok = False
                rate_limit_limit = None
                rate_limit_remaining = None
                rate_limit_reset = None
                models_available = 0
                
                if response.status_code == 200:
                    print_success("✓ Authentication successful")
                    basic_auth_ok = True
                    data = response.json()
                    models_available = len(data.get('data', []))
                    print_info(f"Available models: {models_available}")
                    
                    # Check rate limit headers
                    rate_limit_limit = response.headers.get("x-ratelimit-limit-requests")
                    rate_limit_remaining = response.headers.get("x-ratelimit-remaining-requests")
                    rate_limit_reset = response.headers.get("x-ratelimit-reset-requests")
                    
                    if rate_limit_limit:
                        print_info(f"Rate Limit (Requests): {rate_limit_remaining}/{rate_limit_limit}")
                    if rate_limit_reset:
                        print_info(f"Rate Limit Reset: {rate_limit_reset}")
                
                elif response.status_code == 401:
                    print_error("Authentication failed (401)")
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    print_error(f"Error: {error_msg}")
                    results.append({
                        "key": key_name,
                        "status": "invalid_key",
                        "error": error_msg
                    })
                    continue
                
                elif response.status_code == 429:
                    print_error("Rate limited on basic test (429)")
                    results.append({
                        "key": key_name,
                        "status": "rate_limited",
                        "error": "Rate limited on models endpoint"
                    })
                    continue
                
                elif response.status_code == 403:
                    print_error("Access forbidden (403)")
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Forbidden')
                    print_error(f"Error: {error_msg}")
                    results.append({
                        "key": key_name,
                        "status": "forbidden",
                        "error": error_msg
                    })
                    continue
                
                else:
                    print_error(f"Unexpected status: {response.status_code}")
                    results.append({
                        "key": key_name,
                        "status": f"http_{response.status_code}",
                        "error": response.text[:200]
                    })
                    continue
                
                # 2. Test: Heavy request with dummy data (simulate real workload)
                if basic_auth_ok:
                    print("  [2/3] Testing heavy request (document generation simulation)...")
                    heavy_prompt = """Write a comprehensive information security policy for a financial services organization. 
                    Include: 1) Policy purpose and scope, 2) Roles and responsibilities, 3) Key controls and procedures, 
                    4) Asset classification scheme, 5) Access control requirements, 6) Incident response workflow, 
                    7) Compliance monitoring approach, 8) Annual review schedule. Make it detailed (800+ words)."""
                    
                    heavy_payload = {
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": "You are a compliance expert. Provide detailed, actionable content."},
                            {"role": "user", "content": heavy_prompt}
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.3
                    }
                    
                    try:
                        heavy_response = client.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers=headers,
                            json=heavy_payload,
                            timeout=30
                        )
                        
                        if heavy_response.status_code == 200:
                            print_success("✓ Heavy request successful")
                            heavy_data = heavy_response.json()
                            response_length = len(heavy_data.get('choices', [{}])[0].get('message', {}).get('content', ''))
                            print_info(f"Response length: {response_length} chars")
                            
                            # Update rate limit info from heavy request
                            rate_limit_remaining = heavy_response.headers.get("x-ratelimit-remaining-requests")
                            rate_limit_reset = heavy_response.headers.get("x-ratelimit-reset-requests")
                            
                            heavy_request_ok = True
                        elif heavy_response.status_code == 429:
                            print_error("✗ Rate limited on heavy request (429)")
                            heavy_request_ok = False
                        elif heavy_response.status_code == 401:
                            print_error("✗ Auth failed on heavy request (401)")
                            heavy_request_ok = False
                        else:
                            print_error(f"✗ Heavy request failed with status {heavy_response.status_code}")
                            error_detail = heavy_response.json().get('error', {}).get('message', 'Unknown')
                            print_error(f"  Error: {error_detail}")
                            heavy_request_ok = False
                    except Exception as e:
                        print_error(f"✗ Heavy request error: {str(e)}")
                        heavy_request_ok = False
                    
                    # 3. Test: Concurrent-like behavior (multiple requests in sequence)
                    print("  [3/3] Testing multiple sequential requests...")
                    multi_ok = True
                    for attempt in range(2):
                        quick_payload = {
                            "model": "llama-3.1-8b-instant",
                            "messages": [
                                {"role": "user", "content": "Generate a 2-step security procedure in JSON format with steps array."}
                            ],
                            "max_tokens": 500,
                            "temperature": 0.2
                        }
                        
                        try:
                            multi_response = client.post(
                                "https://api.groq.com/openai/v1/chat/completions",
                                headers=headers,
                                json=quick_payload,
                                timeout=15
                            )
                            
                            if multi_response.status_code == 200:
                                print_success(f"  ✓ Sequential request {attempt + 1} successful")
                            elif multi_response.status_code == 429:
                                print_warning(f"  ⚠ Rate limited on sequential request {attempt + 1}")
                                multi_ok = False
                                break
                            else:
                                print_warning(f"  ⚠ Sequential request {attempt + 1} returned {multi_response.status_code}")
                                multi_ok = False
                                break
                        except Exception as e:
                            print_warning(f"  ⚠ Sequential request {attempt + 1} error: {str(e)[:50]}")
                            multi_ok = False
                            break
                    
                    results.append({
                        "key": key_name,
                        "status": "active",
                        "basic_auth": "ok",
                        "heavy_request": "ok" if heavy_request_ok else "failed",
                        "sequential_requests": "ok" if multi_ok else "failed",
                        "rate_limit_limit": rate_limit_limit,
                        "rate_limit_remaining": rate_limit_remaining,
                        "rate_limit_reset": rate_limit_reset,
                        "models_available": models_available
                    })
        
        except Exception as e:
            print_error(f"Connection error: {str(e)}")
            results.append({
                "key": key_name,
                "status": "connection_error",
                "error": str(e)
            })
    
    return {"keys_checked": len(groq_keys), "results": results}

# ─── OpenAI API Usage ─────────────────────────────────────────────────────────

def check_openai_usage() -> Dict[str, Any]:
    """Check OpenAI API usage and rate limits"""
    print_section("OPENAI API USAGE")
    
    openai_key = os.getenv("OPENAI_API_KEY", "")
    
    if not openai_key:
        print_warning("No OpenAI API key found in .env")
        return {"status": "not_configured"}
    
    print_info(f"Found OpenAI API key: {openai_key[:10]}...")
    
    try:
        with httpx.Client(timeout=10) as client:
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            
            # Check models endpoint
            response = client.get(
                "https://api.openai.com/v1/models",
                headers=headers
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print_success("✓ Authentication successful")
                data = response.json()
                print_info(f"Available models: {len(data.get('data', []))}")
                
                # Check rate limit headers
                rate_limit_requests_limit = response.headers.get("x-ratelimit-limit-requests")
                rate_limit_requests_remaining = response.headers.get("x-ratelimit-remaining-requests")
                rate_limit_tokens_limit = response.headers.get("x-ratelimit-limit-tokens")
                rate_limit_tokens_remaining = response.headers.get("x-ratelimit-remaining-tokens")
                
                if rate_limit_requests_limit:
                    print_info(f"Request Rate Limit: {rate_limit_requests_remaining}/{rate_limit_requests_limit}")
                if rate_limit_tokens_limit:
                    print_info(f"Token Rate Limit: {rate_limit_tokens_remaining}/{rate_limit_tokens_limit}")
                
                # Try to get usage from billing endpoint (requires specific permissions)
                try:
                    usage_response = client.get(
                        "https://api.openai.com/v1/usage/subscription",
                        headers=headers
                    )
                    if usage_response.status_code == 200:
                        usage_data = usage_response.json()
                        print_info(f"Billing: {json.dumps(usage_data, indent=2)}")
                except Exception as e:
                    print_warning(f"Could not fetch billing info: {str(e)}")
                
                return {
                    "status": "active",
                    "rate_limit_requests": rate_limit_requests_limit,
                    "rate_limit_requests_remaining": rate_limit_requests_remaining,
                    "rate_limit_tokens": rate_limit_tokens_limit,
                    "rate_limit_tokens_remaining": rate_limit_tokens_remaining,
                    "models_available": len(data.get('data', []))
                }
            
            elif response.status_code == 401:
                print_error("Authentication failed (401)")
                error_data = response.json()
                print_error(f"Error: {error_data.get('error', {}).get('message', 'Unknown error')}")
                return {"status": "invalid_key", "error": error_data}
            
            else:
                print_error(f"Unexpected status: {response.status_code}")
                return {"status": f"http_{response.status_code}", "response": response.text[:200]}
    
    except Exception as e:
        print_error(f"Connection error: {str(e)}")
        return {"status": "connection_error", "error": str(e)}

# ─── Tavily API Usage ─────────────────────────────────────────────────────────

def check_tavily_usage() -> Dict[str, Any]:
    """Check Tavily API usage and rate limits"""
    print_section("TAVILY API USAGE")
    
    tavily_key = os.getenv("TAVILY_API_KEY", "")
    
    if not tavily_key:
        print_warning("No Tavily API key found in .env")
        return {"status": "not_configured"}
    
    print_info(f"Found Tavily API key: {tavily_key[:10]}...")
    
    try:
        with httpx.Client(timeout=10) as client:
            # Tavily doesn't have a dedicated status endpoint, but we can test the search API
            payload = {
                "api_key": tavily_key,
                "query": "test",
                "max_results": 1,
            }
            
            response = client.post(
                "https://api.tavily.com/search",
                json=payload,
                timeout=10
            )
            
            print_info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print_success("✓ Authentication successful")
                data = response.json()
                
                # Check response structure
                if "results" in data:
                    print_info(f"Search API working: {len(data.get('results', []))} results returned")
                
                # Check headers for rate limit info
                rate_limit_limit = response.headers.get("x-ratelimit-limit-requests")
                rate_limit_remaining = response.headers.get("x-ratelimit-remaining-requests")
                
                if rate_limit_limit:
                    print_info(f"Rate Limit: {rate_limit_remaining}/{rate_limit_limit}")
                
                return {
                    "status": "active",
                    "rate_limit_requests": rate_limit_limit,
                    "rate_limit_remaining": rate_limit_remaining,
                    "search_api": "working"
                }
            
            elif response.status_code == 401:
                print_error("Authentication failed (401)")
                error_data = response.json()
                print_error(f"Error: {error_data.get('message', 'Invalid API key')}")
                return {"status": "invalid_key", "error": error_data}
            
            elif response.status_code == 429:
                print_error("Rate limited (429)")
                return {"status": "rate_limited", "headers": dict(response.headers)}
            
            else:
                print_error(f"Unexpected status: {response.status_code}")
                return {"status": f"http_{response.status_code}", "response": response.text[:200]}
    
    except Exception as e:
        print_error(f"Connection error: {str(e)}")
        return {"status": "connection_error", "error": str(e)}

# ─── LiteLLM Metadata ─────────────────────────────────────────────────────────

def check_litellm_config() -> Dict[str, Any]:
    """Check LiteLLM configuration"""
    print_section("LITELLM CONFIGURATION")
    
    try:
        from config.llm_config import (
            GROQ_API_KEYS,
            OPENAI_API_KEY,
            TAVILY_API_KEY,
            GROQ_MODELS,
            get_llm_config,
            get_rotation_info
        )
        
        print_info(f"Groq API Keys: {len(GROQ_API_KEYS)} configured")
        print_info(f"OpenAI API Key: {'✓ Configured' if OPENAI_API_KEY else '✗ Not configured'}")
        print_info(f"Tavily API Key: {'✓ Configured' if TAVILY_API_KEY else '✗ Not configured'}")
        
        print_info(f"\nGroq Models Available:")
        unique_models = list(dict.fromkeys(GROQ_MODELS))
        for model in unique_models:
            count = GROQ_MODELS.count(model)
            print_info(f"  - {model} (weight: {count})")
        
        config = get_llm_config()
        print_info(f"\nCurrent LLM Config: {json.dumps(config, indent=2)}")
        
        rotation_info = get_rotation_info()
        print_info(f"\nRotation Info: {json.dumps(rotation_info, indent=2)}")
        
        return {
            "groq_keys": len(GROQ_API_KEYS),
            "openai_key": bool(OPENAI_API_KEY),
            "tavily_key": bool(TAVILY_API_KEY),
            "groq_models": unique_models,
            "config": config,
            "rotation_info": rotation_info
        }
    
    except Exception as e:
        print_error(f"Failed to load LiteLLM config: {str(e)}")
        return {"status": "error", "error": str(e)}

# ─── Database Connection Check ───────────────────────────────────────────────

def check_database() -> Dict[str, Any]:
    """Check database connection and status"""
    print_section("DATABASE STATUS")
    
    try:
        from db.database import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        
        # Test connection
        result = db.execute(text("SELECT 1"))
        print_success("✓ Database connection successful")
        
        # Check tables
        from db.models import Base
        print_info(f"ORM Models: {len(Base.registry.mappers)} mapped")
        
        # Count records
        from db.models import User, Organization, Session as DBSession
        user_count = db.query(User).count()
        org_count = db.query(Organization).count()
        session_count = db.query(DBSession).count()
        
        print_info(f"Users: {user_count}")
        print_info(f"Organizations: {org_count}")
        print_info(f"Sessions: {session_count}")
        
        db.close()
        
        return {
            "status": "connected",
            "users": user_count,
            "organizations": org_count,
            "sessions": session_count
        }
    
    except Exception as e:
        print_error(f"Database error: {str(e)}")
        return {"status": "error", "error": str(e)}

# ─── Main Execution ──────────────────────────────────────────────────────────

def main():
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔" + "═"*68 + "╗")
    print("║" + "API USAGE & DIAGNOSTICS MONITOR".center(68) + "║")
    print("║" + f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(68) + "║")
    print("╚" + "═"*68 + "╝")
    print(f"{Colors.RESET}\n")
    
    # Collect all results
    all_results = {}
    
    # Check all APIs
    all_results["groq"] = check_groq_usage()
    all_results["openai"] = check_openai_usage()
    all_results["tavily"] = check_tavily_usage()
    all_results["litellm_config"] = check_litellm_config()
    all_results["database"] = check_database()
    
    # Summary
    print_section("SUMMARY & RECOMMENDATIONS")
    
    groq_status = all_results["groq"].get("results", [])
    active_groq = sum(1 for r in groq_status if r.get("status") == "active")
    forbidden_groq = sum(1 for r in groq_status if r.get("status") == "forbidden")
    invalid_groq = sum(1 for r in groq_status if r.get("status") == "invalid_key")
    rate_limited_groq = sum(1 for r in groq_status if r.get("status") == "rate_limited")
    
    print_info(f"Groq Keys Summary:")
    print_info(f"  • Active: {active_groq}")
    print_info(f"  • Forbidden: {forbidden_groq}")
    print_info(f"  • Invalid: {invalid_groq}")
    print_info(f"  • Rate Limited: {rate_limited_groq}")
    
    # Detailed analysis of active keys
    for result in groq_status:
        if result.get("status") == "active":
            key_name = result.get("key", "Unknown")
            heavy_status = result.get("heavy_request", "unknown")
            sequential_status = result.get("sequential_requests", "unknown")
            
            print(f"\n  {Colors.BOLD}{key_name}{Colors.RESET}:")
            print_info(f"    • Heavy request: {heavy_status}")
            print_info(f"    • Sequential requests: {sequential_status}")
            
            if heavy_status == "failed":
                print_warning(f"    ⚠ This key may have issues with document generation workloads")
            if sequential_status == "failed":
                print_warning(f"    ⚠ This key may be hitting rate limits quickly")
    
    if forbidden_groq > 0:
        print_error("\n⚠ CRITICAL: Some Groq keys are forbidden (organization_restricted)")
        print_error("  Action: Contact Groq support at https://support.groq.com")
        print_error("  Likely causes:")
        print_error("    - Account suspension due to ToS violation")
        print_error("    - Billing issues or payment failure")
        print_error("    - Excessive abuse patterns detected")
    
    if rate_limited_groq > 0:
        print_warning(f"\n⚠ {rate_limited_groq} key(s) are currently rate-limited")
        print_warning("  Recommendation: Wait a few minutes before retrying, or rotate to another key")
    
    # Check if any keys support heavy workloads
    heavy_capable_keys = sum(1 for r in groq_status if r.get("status") == "active" and r.get("heavy_request") == "ok")
    if heavy_capable_keys == 0 and active_groq > 0:
        print_warning("\n⚠ WARNING: No keys passed heavy request test")
        print_warning("  This suggests all active keys may struggle with document generation")
        print_warning("  → Check CrewAI logs for specific error messages")
        print_warning("  → Consider using fewer concurrent generation requests")
    elif heavy_capable_keys > 0:
        print_success(f"\n✓ {heavy_capable_keys}/{active_groq} active key(s) support heavy workloads")
    
    openai_status = all_results["openai"]
    if openai_status.get("status") == "active":
        print_success("✓ OpenAI API is active as fallback")
    elif openai_status.get("status") == "not_configured":
        print_warning("⚠ OpenAI not configured (no fallback available)")
    
    tavily_status = all_results["tavily"]
    if tavily_status.get("status") == "active":
        print_success("✓ Tavily API is active")
    
    db_status = all_results["database"]
    if db_status.get("status") == "connected":
        print_success("✓ Database is connected")
    
    # Export results to JSON
    output_file = Path(__file__).resolve().parent / "api_usage_report.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": all_results
        }, f, indent=2)
    
    print_info(f"\nDetailed report saved to: {output_file}")
    
    return all_results

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}Fatal error: {str(e)}{Colors.RESET}")
        sys.exit(1)
