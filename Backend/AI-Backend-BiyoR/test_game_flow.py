"""
Test script for the simplified 2-phase game flow API.
Phase 1: initial_game - Game setup and rules briefing
Phase 2: in_game - Active gameplay queries
"""

import requests
import json
import time
import sys
import subprocess

BASE_URL = "http://localhost:8000/api/v1"

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_response(response: dict, indent: int = 2):
    """Pretty print a JSON response."""
    print(json.dumps(response, indent=indent, default=str))

def check_server_health() -> bool:
    """Check if the server is running and healthy."""
    try:
        response = requests.get(f"{BASE_URL}/rules/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"Server Status: {data.get('status', 'unknown')}")
            print(f"FAISS Index Loaded: {data.get('faiss_index_loaded', False)}")
            print(f"Gemini API Accessible: {data.get('gemini_api_accessible', False)}")
            return data.get('status') == 'healthy'
        return False
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"ERROR checking health: {e}")
        return False

def build_faiss_index() -> bool:
    """Build the FAISS index if not loaded."""
    print("\nBuilding FAISS index...")
    try:
        response = requests.post(
            f"{BASE_URL}/rules/reindex",
            json={"force_rebuild": True},
            timeout=120
        )
        if response.status_code == 200:
            data = response.json()
            print(f"Index built successfully!")
            print(f"Documents processed: {data.get('documents_processed', 0)}")
            print(f"Chunks created: {data.get('chunks_created', 0)}")
            return True
        else:
            print(f"Failed to build index: {response.text}")
            return False
    except Exception as e:
        print(f"Error building index: {e}")
        return False

def test_initial_game():
    """Test Phase 1: Initial Game Setup."""
    print_header("PHASE 1: INITIAL GAME SETUP")
    
    request_data = {
        "game_config": {
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
            "language_preference": "en"
        },
        "session_id": "test_session_001"
    }
    
    print("\nRequest:")
    print_response(request_data)
    
    try:
        print("\nSending request to /game/initial...")
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/game/initial",
            json=request_data,
            timeout=90
        )
        elapsed = time.time() - start_time
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print("\n--- Response Summary ---")
            print(f"Game Overview: {data.get('game_overview', 'N/A')[:100]}...")
            print(f"Number of Rules: {len(data.get('important_rules', []))}")
            
            if data.get('important_rules'):
                print("\n--- Important Rules ---")
                for i, rule in enumerate(data['important_rules'][:3], 1):
                    print(f"\n  Rule {i}: {rule.get('title', 'N/A')}")
                    body = rule.get('body', 'N/A')
                    print(f"  Body: {body[:150]}..." if len(body) > 150 else f"  Body: {body}")
            
            if data.get('field_layout'):
                print("\n--- Field Layout ---")
                layout = data['field_layout']
                print(f"  Anchor: {layout.get('anchor_position', 'N/A')}")
                print(f"  Safe Zone: {layout.get('safe_zone_radius_m', 'N/A')} m")
            
            if data.get('model_metadata'):
                meta = data['model_metadata']
                print(f"\n--- Metadata ---")
                print(f"  Model: {meta.get('model_name', 'N/A')}")
                print(f"  Chunks Retrieved: {meta.get('retrieved_chunk_count', 'N/A')}")
                print(f"  Processing Time: {meta.get('processing_time_ms', 0):.0f} ms")
            
            return True
        else:
            print(f"\nError Response:")
            print_response(response.json() if response.text else {"error": "No response body"})
            return False
            
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out (90s)")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_in_game_scoring():
    """Test Phase 2: In-Game Scoring Query."""
    print_header("PHASE 2: IN-GAME SCORING QUERY")
    
    request_data = {
        "game_config": {
            "equipment_dimensions": {
                "dandi_length_cm": 60,
                "biyo_length_cm": 8
            },
            "ground_description": {
                "surface_type": "grass"
            },
            "num_players_available": 4
        },
        "query_type": "scoring",
        "situation_summary": "Player from Team A hit the Biyo with the Dandi. The Biyo flew and landed approximately 12 meters from the anchor point.",
        "estimated_distance_m": 12.0,
        "session_id": "test_session_001"
    }
    
    print("\nRequest:")
    print_response(request_data)
    
    try:
        print("\nSending request to /game/query...")
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/game/query",
            json=request_data,
            timeout=90
        )
        elapsed = time.time() - start_time
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print("\n--- Response Summary ---")
            print(f"Overall Summary: {data.get('overall_summary', 'N/A')}")
            print(f"Score: {data.get('score', 'N/A')}")
            print(f"Valid Attempt: {data.get('is_valid_attempt', 'N/A')}")
            
            if data.get('cards'):
                print(f"\n--- Cards ({len(data['cards'])}) ---")
                for card in data['cards'][:2]:
                    print(f"\n  {card.get('title', 'N/A')}")
                    body = card.get('body', 'N/A')
                    print(f"  {body[:100]}..." if len(body) > 100 else f"  {body}")
            
            return True
        else:
            print(f"\nError Response:")
            print_response(response.json() if response.text else {"error": "No response body"})
            return False
            
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out (90s)")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_in_game_foul_check():
    """Test Phase 2: In-Game Foul Check Query."""
    print_header("PHASE 2: IN-GAME FOUL CHECK QUERY")
    
    request_data = {
        "game_config": {
            "num_players_available": 4
        },
        "query_type": "foul_check",
        "action_description": "A player from the fielding team caught the Biyo after it bounced once on the ground",
        "player_team": "Team B (fielding)",
        "session_id": "test_session_001"
    }
    
    print("\nRequest:")
    print_response(request_data)
    
    try:
        print("\nSending request to /game/query...")
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/game/query",
            json=request_data,
            timeout=90
        )
        elapsed = time.time() - start_time
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print("\n--- Response Summary ---")
            print(f"Overall Summary: {data.get('overall_summary', 'N/A')}")
            print(f"Is Foul: {data.get('is_foul', 'N/A')}")
            print(f"Penalty: {data.get('penalty_description', 'N/A')}")
            
            return True
        else:
            print(f"\nError Response:")
            print_response(response.json() if response.text else {"error": "No response body"})
            return False
            
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out (90s)")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_in_game_clarification():
    """Test Phase 2: In-Game Rule Clarification Query."""
    print_header("PHASE 2: IN-GAME CLARIFICATION QUERY")
    
    request_data = {
        "game_config": {
            "num_players_available": 4
        },
        "query_type": "clarification",
        "situation_summary": "What happens if the Biyo goes out of bounds during play?",
        "session_id": "test_session_001"
    }
    
    print("\nRequest:")
    print_response(request_data)
    
    try:
        print("\nSending request to /game/query...")
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/game/query",
            json=request_data,
            timeout=90
        )
        elapsed = time.time() - start_time
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print("\n--- Response Summary ---")
            print(f"Overall Summary: {data.get('overall_summary', 'N/A')}")
            
            if data.get('cards'):
                print(f"\n--- Cards ({len(data['cards'])}) ---")
                for card in data['cards'][:2]:
                    print(f"\n  {card.get('title', 'N/A')}")
                    body = card.get('body', 'N/A')
                    print(f"  {body[:100]}..." if len(body) > 100 else f"  {body}")
            
            return True
        else:
            print(f"\nError Response:")
            print_response(response.json() if response.text else {"error": "No response body"})
            return False
            
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out (90s)")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Run all tests."""
    print_header("BiyoR 2-PHASE GAME FLOW TEST")
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check server health
    print_header("HEALTH CHECK")
    if not check_server_health():
        print("\nServer is not healthy. Please start the server first:")
        print("  cd AI-Backend-BiyoR")
        print("  .\\env_biyor\\Scripts\\activate")
        print("  python -m uvicorn app.main:app --reload")
        sys.exit(1)
    
    # Check if FAISS index needs to be built
    try:
        health_response = requests.get(f"{BASE_URL}/rules/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            if not health_data.get('faiss_index_loaded', False):
                print("\nFAISS index not loaded. Building...")
                if not build_faiss_index():
                    print("Failed to build FAISS index. Some tests may fail.")
    except Exception as e:
        print(f"Warning: Could not check/build FAISS index: {e}")
    
    # Run tests
    results = {}
    
    # Phase 1: Initial Game
    results['initial_game'] = test_initial_game()
    
    # Phase 2: In-Game Queries
    results['scoring'] = test_in_game_scoring()
    results['foul_check'] = test_in_game_foul_check()
    results['clarification'] = test_in_game_clarification()
    
    # Summary
    print_header("TEST SUMMARY")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll tests passed!")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
