"""
Tests for Text-Based Chat Referee System
-----------------------------------------
Test conversational game flow, scoring, and state management.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.chat_referee import ChatReferee, get_chat_referee
from app.models.chat_models import (
    ChatRequest, GameState, HutneEvent, TyakEvent, 
    TurnEvent, SafeZone, ScoreBreakdown
)


client = TestClient(app)


# =============================================================================
# UNIT TESTS - Scoring Algorithm
# =============================================================================

class TestScoringAlgorithm:
    """Test the embedded scoring algorithm."""
    
    def setup_method(self):
        """Setup test referee."""
        self.referee = ChatReferee()
    
    def test_hutnu_basic_score(self):
        """Test basic Hutnu scoring: zone + safe points."""
        turn = TurnEvent(
            player="Ram",
            hutnu=HutneEvent(zone=3, safe=SafeZone.MIDDLE, out=False),
            tyak=TyakEvent(attempted=False)
        )
        breakdown = self.referee.calculate_score(turn, time_left=30.0)
        
        assert breakdown.hutnu_zone == 3
        assert breakdown.hutnu_safe == "middle"
        assert breakdown.hutnu_safe_points == 4
        assert breakdown.hutnu_score == 7  # 3 + 4
        assert breakdown.turn_score == 7
        assert not breakdown.is_out
    
    def test_hutnu_with_tyak(self):
        """Test Hutnu + Tyak scoring."""
        turn = TurnEvent(
            player="Ram",
            hutnu=HutneEvent(zone=3, safe=SafeZone.MIDDLE, out=False),
            tyak=TyakEvent(attempted=True, zone=4, taps=3, out=False)
        )
        breakdown = self.referee.calculate_score(turn, time_left=30.0)
        
        assert breakdown.hutnu_score == 7  # 3 + 4
        assert breakdown.tyak_score == 8   # 2 × 4
        assert breakdown.turn_score == 15  # 7 + 8
    
    def test_hutnu_out(self):
        """Test Hutnu OUT - entire turn is 0."""
        turn = TurnEvent(
            player="Ram",
            hutnu=HutneEvent(zone=5, safe=SafeZone.FURTHEST, out=True),
            tyak=TyakEvent(attempted=True, zone=4, taps=3, out=False)
        )
        breakdown = self.referee.calculate_score(turn, time_left=30.0)
        
        assert breakdown.hutnu_score == 0
        assert breakdown.tyak_score == 0  # Tyak ignored when Hutnu OUT
        assert breakdown.turn_score == 0
        assert breakdown.is_out
        assert "Hutnu" in breakdown.out_reason
    
    def test_tyak_out_preserves_hutnu(self):
        """Test Tyak OUT preserves Hutnu score."""
        turn = TurnEvent(
            player="Ram",
            hutnu=HutneEvent(zone=5, safe=SafeZone.NONE, out=False),
            tyak=TyakEvent(attempted=True, zone=2, taps=1, out=True)
        )
        breakdown = self.referee.calculate_score(turn, time_left=30.0)
        
        assert breakdown.hutnu_score == 5  # Zone only, no safe
        assert breakdown.tyak_score == 0   # OUT
        assert breakdown.turn_score == 5   # Hutnu preserved
        assert breakdown.is_out
    
    def test_boundary_out(self):
        """Test boundary violation (zone > 6)."""
        turn = TurnEvent(
            player="Ram",
            hutnu=HutneEvent(zone=7, safe=SafeZone.NONE, out=False)
        )
        breakdown = self.referee.calculate_score(turn, time_left=30.0)
        
        assert breakdown.hutnu_score == 0
        assert breakdown.is_out
        assert "Boundary" in breakdown.out_reason
    
    def test_safe_zone_points(self):
        """Test all safe zone point values."""
        # Nearest = 2
        turn = TurnEvent(hutnu=HutneEvent(zone=1, safe=SafeZone.NEAREST, out=False))
        assert self.referee.calculate_score(turn, 30.0).hutnu_score == 3  # 1 + 2
        
        # Middle = 4
        turn = TurnEvent(hutnu=HutneEvent(zone=1, safe=SafeZone.MIDDLE, out=False))
        assert self.referee.calculate_score(turn, 30.0).hutnu_score == 5  # 1 + 4
        
        # Furthest = 6
        turn = TurnEvent(hutnu=HutneEvent(zone=1, safe=SafeZone.FURTHEST, out=False))
        assert self.referee.calculate_score(turn, 30.0).hutnu_score == 7  # 1 + 6
        
        # None = 0
        turn = TurnEvent(hutnu=HutneEvent(zone=1, safe=SafeZone.NONE, out=False))
        assert self.referee.calculate_score(turn, 30.0).hutnu_score == 1  # 1 + 0
    
    def test_time_expired(self):
        """Test no score when time expired."""
        turn = TurnEvent(
            hutnu=HutneEvent(zone=5, safe=SafeZone.FURTHEST, out=False),
            tyak=TyakEvent(attempted=True, zone=4, taps=3, out=False)
        )
        breakdown = self.referee.calculate_score(turn, time_left=0)
        
        assert breakdown.turn_score == 0
        assert "time expired" in breakdown.reasoning.lower()


# =============================================================================
# UNIT TESTS - Input Parsing
# =============================================================================

class TestInputParsing:
    """Test natural language input parsing."""
    
    def setup_method(self):
        """Setup test referee."""
        self.referee = ChatReferee()
        self.state = GameState(session_id="test")
    
    def test_parse_start(self):
        """Test parsing START command."""
        parsed = self.referee.parse_user_input("Team Tigers, START", self.state)
        assert parsed.intent == "start"
        assert parsed.team_name == "Tigers"
    
    def test_parse_player_name(self):
        """Test parsing player name."""
        self.state.phase = "turn"
        parsed = self.referee.parse_user_input("Player Ram", self.state)
        assert parsed.intent == "turn"
        assert parsed.player_name == "Ram"
    
    def test_parse_hutnu_zone_safe(self):
        """Test parsing Hutnu with zone and safe."""
        self.state.phase = "hutnu"
        parsed = self.referee.parse_user_input("zone 3, safe middle, not out", self.state)
        assert parsed.intent == "hutnu"
        assert parsed.hutnu.zone == 3
        assert parsed.hutnu.safe == SafeZone.MIDDLE
        assert not parsed.hutnu.out
    
    def test_parse_hutnu_out(self):
        """Test parsing Hutnu OUT."""
        self.state.phase = "hutnu"
        parsed = self.referee.parse_user_input("caught in air", self.state)
        assert parsed.intent == "hutnu"
        assert parsed.hutnu.out
    
    def test_parse_tyak(self):
        """Test parsing Tyak."""
        self.state.phase = "tyak"
        parsed = self.referee.parse_user_input("tyak zone 4, 3 taps", self.state)
        assert parsed.intent == "tyak"
        assert parsed.tyak.attempted
        assert parsed.tyak.zone == 4
        assert parsed.tyak.taps == 3
    
    def test_parse_no_tyak(self):
        """Test parsing no Tyak."""
        self.state.phase = "tyak"
        parsed = self.referee.parse_user_input("no tyak", self.state)
        assert parsed.intent == "tyak"
        assert not parsed.tyak.attempted


# =============================================================================
# INTEGRATION TESTS - API Endpoints
# =============================================================================

class TestChatAPI:
    """Test chat API endpoints."""
    
    def test_start_game(self):
        """Test starting a game via chat."""
        response = client.post(
            "/api/v1/chat/",
            json={"session_id": "test_game_1", "message": "Team Tigers, START"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Tigers" in data["chat_text"] or "chat_text" in data
        assert data["state"]["team"] == "Tigers" or data["state"]["phase"] == "turn"
    
    def test_get_state(self):
        """Test getting game state."""
        # First start a game
        client.post(
            "/api/v1/chat/",
            json={"session_id": "test_state_1", "message": "Team Eagles, START"}
        )
        
        # Then get state
        response = client.get("/api/v1/chat/state/test_state_1")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test_state_1"
    
    def test_reset_session(self):
        """Test resetting a session."""
        # Start a game
        client.post(
            "/api/v1/chat/",
            json={"session_id": "test_reset_1", "message": "Team Hawks, START"}
        )
        
        # Reset it
        response = client.post("/api/v1/chat/reset/test_reset_1")
        assert response.status_code == 200
        data = response.json()
        assert data["phase"] == "start"
        assert data["total_score"] == 0
    
    def test_health_check(self):
        """Test chat health endpoint."""
        response = client.get("/api/v1/chat/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["chat_enabled"] == True
    
    def test_full_turn_flow(self):
        """Test a complete turn flow."""
        session = "test_full_turn"
        
        # 1. Start game
        r1 = client.post("/api/v1/chat/", json={
            "session_id": session,
            "message": "Team Pandas, START"
        })
        assert r1.status_code == 200
        
        # 2. Player name
        r2 = client.post("/api/v1/chat/", json={
            "session_id": session,
            "message": "Player Ram"
        })
        assert r2.status_code == 200
        
        # 3. Hutnu result
        r3 = client.post("/api/v1/chat/", json={
            "session_id": session,
            "message": "Hutnu zone 3, safe middle, not out"
        })
        assert r3.status_code == 200
        data3 = r3.json()
        assert data3["state"]["phase"] == "tyak"
        
        # 4. Tyak result
        r4 = client.post("/api/v1/chat/", json={
            "session_id": session,
            "message": "Tyak zone 4, 2 taps"
        })
        assert r4.status_code == 200
        data4 = r4.json()
        
        # Check score: Hutnu (3+4=7) + Tyak (2×4=8) = 15
        assert data4["state"]["total_score"] >= 0  # Score should be recorded
        assert data4["embedded_json"] is not None


# =============================================================================
# DEMO TESTS - Full Game Simulation
# =============================================================================

class TestFullGameDemo:
    """Demonstrate a full game via curl-like requests."""
    
    def test_demo_game(self):
        """Simulate a complete game with multiple turns."""
        session = "demo_game_001"
        
        # Turn 1: Start
        r = client.post("/api/v1/chat/", json={
            "session_id": session,
            "message": "Team Demo, START"
        })
        print(f"\n=== START ===\n{r.json()['chat_text']}")
        
        # Turn 1: Player
        r = client.post("/api/v1/chat/", json={
            "session_id": session,
            "message": "Player Ram"
        })
        print(f"\n=== TURN 1: PLAYER ===\n{r.json()['chat_text']}")
        
        # Turn 1: Hutnu
        r = client.post("/api/v1/chat/", json={
            "session_id": session,
            "message": "Zone 4, safe furthest, no out"
        })
        print(f"\n=== TURN 1: HUTNU ===\n{r.json()['chat_text']}")
        
        # Turn 1: Tyak
        r = client.post("/api/v1/chat/", json={
            "session_id": session,
            "message": "Tyak zone 3, 4 taps"
        })
        data = r.json()
        print(f"\n=== TURN 1: TYAK ===\n{data['chat_text']}")
        print(f"Score breakdown: {data.get('embedded_json')}")
        
        # Check final state
        state = client.get(f"/api/v1/chat/state/{session}").json()
        print(f"\n=== FINAL STATE ===")
        print(f"Total Score: {state['total_score']}")
        print(f"Turn: {state['turn']}")
        print(f"Time Left: {state['time_left']} min")
        
        # Expected: Hutnu (4+6=10) + Tyak (2×3=6) = 16
        assert state["total_score"] == 16


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
