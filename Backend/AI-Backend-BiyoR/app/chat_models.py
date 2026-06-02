"""
Chat Models for Text-Based Dandi Biyo Referee
----------------------------------------------
Pydantic models for conversational referee chat system.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class SafeZone(str, Enum):
    """Safe zone positions."""
    NEAREST = "nearest"
    MIDDLE = "middle"
    FURTHEST = "furthest"
    NONE = "none"


class HutneEvent(BaseModel):
    """Hutne (hitting) event data extracted from chat."""
    zone: int = Field(default=0, ge=0, le=7, description="Landing zone (0-6, 7=boundary OUT)")
    safe: SafeZone = Field(default=SafeZone.NONE, description="Safe zone reached")
    out: bool = Field(default=False, description="Whether player is OUT during Hutnu")
    
    @property
    def safe_points(self) -> int:
        """Calculate safe zone points."""
        return {"nearest": 2, "middle": 4, "furthest": 6, "none": 0}.get(self.safe.value, 0)
    
    @property
    def score(self) -> int:
        """Calculate Hutnu score."""
        if self.out or self.zone > 6:
            return 0
        return self.zone + self.safe_points


class TyakEvent(BaseModel):
    """Tyak (tapping) event data extracted from chat."""
    attempted: bool = Field(default=False, description="Whether Tyak was attempted")
    zone: int = Field(default=0, ge=0, le=7, description="Tyak landing zone")
    taps: int = Field(default=0, ge=0, description="Number of taps before landing")
    out: bool = Field(default=False, description="Whether player is OUT during Tyak")
    
    @property
    def score(self) -> int:
        """Calculate Tyak score (2 × zone if valid)."""
        if not self.attempted or self.out or self.taps <= 0 or self.zone > 6:
            return 0
        return 2 * self.zone


class TurnEvent(BaseModel):
    """Complete turn event combining Hutnu and Tyak."""
    player: str = Field(default="", description="Player name")
    hutnu: HutneEvent = Field(default_factory=HutneEvent)
    tyak: TyakEvent = Field(default_factory=TyakEvent)
    
    @property
    def turn_score(self) -> int:
        """Calculate total turn score."""
        # If Hutnu OUT, turn score is 0
        if self.hutnu.out:
            return 0
        # If Tyak OUT, only Hutnu counts
        if self.tyak.out:
            return self.hutnu.score
        return self.hutnu.score + self.tyak.score
    
    @property
    def is_out(self) -> bool:
        """Check if player is OUT this turn."""
        return self.hutnu.out or self.tyak.out


class PlayerState(BaseModel):
    """Individual player state."""
    name: str
    turns_played: int = 0
    total_score: int = 0
    outs: int = 0


class GameState(BaseModel):
    """Complete game state for a session."""
    session_id: str
    team: str = ""
    turn: int = 1
    total_score: int = 0
    time_left: float = Field(default=30.0, description="Time remaining in minutes")
    players: List[str] = Field(default_factory=list)
    current_player: Optional[str] = None
    history: List[Dict[str, Any]] = Field(default_factory=list, description="Chat history")
    phase: str = Field(default="start", description="Current game phase: start|turn|hutnu|tyak|end")
    turn_data: Optional[TurnEvent] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str):
        """Add message to history."""
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
    
    def start_new_turn(self):
        """Initialize a new turn."""
        self.turn_data = TurnEvent()
        self.phase = "hutnu"
    
    def complete_turn(self) -> int:
        """Complete current turn, add score, return turn score."""
        if self.turn_data:
            turn_score = self.turn_data.turn_score
            self.total_score += turn_score
            self.turn += 1
            # Decrement time (~1 min per turn)
            self.time_left = max(0, self.time_left - 1.0)
            self.phase = "turn" if self.time_left > 0 else "end"
            return turn_score
        return 0
    
    def is_game_over(self) -> bool:
        """Check if game is over."""
        return self.time_left <= 0 or self.phase == "end"


class GameSummary(BaseModel):
    """End-of-game summary."""
    team: str
    total_turns: int
    final_score: int
    players: List[str] = Field(default_factory=list)
    game_duration: float = Field(description="Game duration in minutes")
    average_score_per_turn: float = 0.0


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown for a turn."""
    hutnu_zone: int = 0
    hutnu_safe: str = "none"
    hutnu_safe_points: int = 0
    hutnu_score: int = 0
    tyak_attempted: bool = False
    tyak_zone: int = 0
    tyak_taps: int = 0
    tyak_score: int = 0
    turn_score: int = 0
    is_out: bool = False
    out_reason: Optional[str] = None
    reasoning: str = ""


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., min_length=1, description="User's chat message")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    chat_text: str = Field(..., description="Natural language response from referee")
    embedded_json: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Structured data (ScoreBreakdown, GameSummary, or None)"
    )
    state: GameState = Field(..., description="Current game state")
    next_prompt: str = Field(default="", description="Suggested next action/question")
    valid: bool = Field(default=True, description="Whether the request was valid")
    error: Optional[str] = None


class ParsedInput(BaseModel):
    """Parsed user input from natural language."""
    intent: str = Field(description="Detected intent: start|turn|hutnu|tyak|end|query|unknown")
    team_name: Optional[str] = None
    player_name: Optional[str] = None
    hutnu: Optional[HutneEvent] = None
    tyak: Optional[TyakEvent] = None
    raw_text: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
