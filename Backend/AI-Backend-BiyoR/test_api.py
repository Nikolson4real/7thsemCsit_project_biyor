"""
Test script for BiyoR AI Rules Engine
Run this after starting the server to verify everything works.
"""

import requests
import json
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_health_check() -> bool:
    """Test the health check endpoint."""
    print_section("Test 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/rules/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print("[OK] Service is healthy!")
                return True
            else:
                print("[WARNING] Service is unhealthy. Will attempt to build FAISS index...")
                return False
        else:
            print(f"[ERROR] Health check failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to server. Is it running?")
        print("   Start with: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        return False


def test_reindex(force: bool = True) -> bool:
    """Test the reindex endpoint."""
    print_section("Test 2: Build FAISS Index")
    
    try:
        payload = {"force_rebuild": force}
        print(f"Requesting reindex (force_rebuild={force})...")
        print("⏳ This may take 10-30 seconds depending on rulebook size...")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/rules/reindex",
            json=payload,
            timeout=90  # Increased timeout for indexing
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
            print(f"\n[OK] Indexed {data.get('documents_processed', 0)} documents")
            print(f"   Created {data.get('chunks_created', 0)} chunks")
            print(f"   Index saved to: {data.get('index_path', 'unknown')}")
            return True
        else:
            print(f"[ERROR] Reindex failed")
            print(json.dumps(response.json(), indent=2))
            return False
            
    except requests.exceptions.Timeout:
        print("[ERROR] Reindex timed out. The index might still be building.")
        print("   Check server logs for progress.")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        return False


def test_rules_query() -> bool:
    """Test the rules query endpoint."""
    print_section("Test 3: Query Rules")
    
    # Sample query
    query_data = {
        "situation_summary": "Player A struck the Biyo and it landed 15 meters away. We need to verify if this is a valid hit and calculate the score.",
        "equipment_dimensions": {
            "dandi_length_cm": 60,
            "biyo_length_cm": 8,
            "biyo_diameter_cm": 2.5
        },
        "ground_description": {
            "surface_type": "grass",
            "field_length_m": 30,
            "field_width_m": 20
        },
        "num_players_available": 4,
        "team_a_players": 2,
        "team_b_players": 2,
        "game_phase": "scoring",
        "language_preference": "en",
        "session_id": "test_session_001"
    }
    
    print("Sending query...")
    print(f"Situation: {query_data['situation_summary'][:80]}...")
    print("⏳ This may take 30-60 seconds on first request (Gemini API warm-up)...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/rules/query",
            json=query_data,
            timeout=90  # Increased timeout to 90 seconds for first query
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n[OK] Received {len(data.get('cards', []))} instruction cards")
            print(f"   Model used: {data.get('model_metadata', {}).get('model_name', 'unknown')}") 
            print(f"   Retrieved chunks: {data.get('model_metadata', {}).get('retrieved_chunk_count', 0)}")
            
            # Print first card as sample
            if data.get('cards'):
                card = data['cards'][0]
                print(f"\nSample Card:")
                print(f"   Title: {card.get('title')}")
                print(f"   Type: {card.get('type')}")
                print(f"   Body: {card.get('body', '')[:150]}...")
            
            print(f"\nOverall Summary: {data.get('overall_summary', '')[:150]}...")
            return True
        else:
            print(f"[ERROR] Query failed")
            print(json.dumps(response.json(), indent=2))
            return False
            
    except requests.exceptions.Timeout:
        print("[ERROR] Query timed out after 90 seconds.")
        print("   This might indicate:")
        print("   1. Gemini API is slow (first request can be slower)")
        print("   2. Network connectivity issues")
        print("   3. Server processing bottleneck")
        print("\n   Tip: Check server logs for detailed error information")
        print("   Tip: Try running the query again (subsequent calls are faster)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection error: {str(e)}")
        print("   The server might have crashed. Check server logs.")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        return False
def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  BiyoR AI Rules Engine - Test Suite")
    print("=" * 60)
    print("\nMake sure the server is running before proceeding!")
    print("Start server with: uvicorn app.main:app --reload\n")
    
    input("Press Enter to continue...")
    
    # Run tests
    results = []
    
    # Test 1: Health check
    health_ok = test_health_check()
    results.append(("Health Check", health_ok))
    
    # Test 2: Reindex (if health check failed or FAISS not loaded)
    if not health_ok:
        print("\n[WARNING] FAISS index not loaded. Building index now...")
        reindex_ok = test_reindex(force=True)
        results.append(("Build FAISS Index", reindex_ok))
        
        if reindex_ok:
            # Re-check health after indexing
            print("\nVerifying health after indexing...")
            health_ok = test_health_check()
    else:
        print("\n[OK] FAISS index already loaded. Skipping reindex.")
        reindex_ok = True
        results.append(("Build FAISS Index", True))
    
    # Test 3: Rules query (only if health is OK)
    if health_ok:
        query_ok = test_rules_query()
        results.append(("Rules Query", query_ok))
    else:
        print("\n[WARNING] Skipping rules query test due to unhealthy service")
        results.append(("Rules Query", False))
    
    # Summary
    print_section("Test Summary")
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}  {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n" + "=" * 60)
        print("  All tests passed!")
        print("=" * 60)
        print("\nYour BiyoR backend is ready to use!")
        print(f"API Docs: {BASE_URL}/api/v1/docs")
    else:
        print("\n" + "=" * 60)
        print("  Some tests failed. Check the output above.")
        print("=" * 60)
        print("\nIf Rules Query timed out:")
        print("   - Check server terminal for error logs")
        print("   - Verify your GOOGLE_API_KEY is valid")
        print("   - Try running the test again (first call is slower)")


if __name__ == "__main__":
    main()
