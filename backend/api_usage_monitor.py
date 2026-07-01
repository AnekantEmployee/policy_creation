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
                # Attempt a simple models list call
                response = client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers=headers
                )
                
                print_info(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    print_success("✓ Authentication successful")
                    data = response.json()
                    print_info(f"Available models: {len(data.get('data', []))}")
                    
                    # Check rate limit headers
                    rate_limit_limit = response.headers.get("x-ratelimit-limit-requests")
                    rate_limit_remaining = response.headers.get("x-ratelimit-remaining-requests")
                    rate_limit_reset = response.headers.get("x-ratelimit-reset-requests")
                    
                    if rate_limit_limit:
                        print_info(f"Rate Limit (Requests): {rate_limit_remaining}/{rate_limit_limit}")
                    if rate_limit_reset:
                        print_info(f"Rate Limit Reset: {rate_limit_reset}")
                    
                    results.append({
                        "key": key_name,
                        "status": "active",
                        "rate_limit_requests": rate_limit_limit,
                        "rate_limit_remaining": rate_limit_remaining,
                        "rate_limit_reset": rate_limit_reset,
                        "models_available": len(data.get('data', []))
                    })
                
                elif response.status_code == 401:
                    print_error("Authentication failed (401)")
                    error_data = response.json()
                    print_error(f"Error: {error_data.get('error', {}).get('message', 'Unknown error')}")
                    results.append({
                        "key": key_name,
                        "status": "invalid_key",
                        "error": error_data.get('error', {}).get('message', 'Invalid API key')
                    })
                
                elif response.status_code == 429:
                    print_error("Rate limited (429)")
                    print_warning(f"Headers: {dict(response.headers)}")
                    results.append({
                        "key": key_name,
                        "status": "rate_limited",
                        "headers": dict(response.headers)
                    })
                
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
                
                else:
                    print_error(f"Unexpected status: {response.status_code}")
                    results.append({
                        "key": key_name,
                        "status": f"http_{response.status_code}",
                        "response": response.text[:200]
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
    
    print_info(f"Groq Keys: {active_groq} active, {forbidden_groq} forbidden, {invalid_groq} invalid")
    
    if forbidden_groq > 0:
        print_error("⚠ CRITICAL: Some Groq keys are forbidden (organization_restricted)")
        print_error("  Action: Contact Groq support at https://support.groq.com")
        print_error("  Likely causes:")
        print_error("    - Account suspension due to ToS violation")
        print_error("    - Billing issues or payment failure")
        print_error("    - Excessive abuse patterns detected")
    
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
