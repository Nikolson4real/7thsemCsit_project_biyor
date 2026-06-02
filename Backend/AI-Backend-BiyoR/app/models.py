"""
Pydantic models for BiyoR AI Rules Engine API.
Simplified 2-phase game flow: initial_game and in_game.
Flexible validation for LLM responses.
"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class GamePhase(str, Enum):
    """Simplified phases of Dandi Biyo game."""
    INITIAL_GAME = "initial_game"  # Game setup, briefing, field layout
    IN_GAME = "in_game"            # Active gameplay: scoring, fouls, clarifications


class SurfaceType(str, Enum):
    """Types of playing surfaces for Dandi Biyo."""
    GRASS = "grass"
    DIRT = "dirt"
    CONCRETE = "concrete"
    SAND = "sand"
    OTHER = "other"


# ============================================================================
# Shared Models
# ============================================================================

class EquipmentDimensions(BaseModel):
    """Physical dimensions of Dandi Biyo equipment."""
    dandi_length_cm: Optional[float] = Field(
        None,
        gt=0,
        le=200,
        description="Length of the Dandi stick in centimeters"
    )
    biyo_length_cm: Optional[float] = Field(
        None,
        gt=0,
        le=50,
        description="Length of the Biyo piece in centimeters"
    )
    biyo_diameter_cm: Optional[float] = Field(
        None,
        gt=0,
        le=10,
        description="Diameter of the Biyo piece in centimeters"
    )
    
    class Config:
        extra = "allow"


class GroundDescription(BaseModel):
    """Description of the playing field/ground."""
    surface_type: Optional[SurfaceType] = Field(
        None,
        description="Type of playing surface"
    )
    field_length_m: Optional[float] = Field(
        None,
        gt=0,
        le=100,
        description="Length of the field in meters"
    )
    field_width_m: Optional[float] = Field(
        None,
        gt=0,
        le=100,
        description="Width of the field in meters"
    )
    anchor_position: Optional[str] = Field(
        None,
        description="AR reference or description of anchor/center position"
    )
    free_text_description: Optional[str] = Field(
        None,
        description="Additional free-form field description"
    )
    
    class Config:
        extra = "allow"


class GameConfiguration(BaseModel):
    """
    Game configuration settings. Used in both initial_game and in_game phases.
    """
    equipment_dimensions: Optional[EquipmentDimensions] = Field(
        None,
        description="Dimensions of Dandi and Biyo equipment"
    )
    
    ground_description: Optional[GroundDescription] = Field(
        None,
        description="Description of the playing field"
    )
    
    num_players_available: Optional[int] = Field(
        None,
        ge=1,
        le=50,
        description="Total number of players available"
    )
    
    team_a_players: Optional[int] = Field(
        None,
        ge=0,
        description="Number of players in team A"
    )
    
    team_b_players: Optional[int] = Field(
        None,
        ge=0,
        description="Number of players in team B"
    )
    
    language_preference: Optional[str] = Field(
        default="en",
        description="Language code (e.g., 'en', 'ne')"
    )
    
    class Config:
        extra = "allow"
        json_schema_extra = {
            "example": {
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
            }
        }


class InstructionCard(BaseModel):
    """A single instruction card with rule or guidance information."""
    
    id: Optional[str] = Field(None, description="Unique identifier for this card")
    title: Optional[str] = Field(None, description="Short title for the card")
    type: Optional[str] = Field(None, description="Type of card (rule, warning, tip, etc.)")
    priority: Optional[int] = Field(None, description="Display priority (1=highest)")
    body: Optional[str] = Field(None, description="Main content of the card")
    reasoning_summary: Optional[str] = Field(None, description="Explanation of why this applies")
    related_rule_refs: Optional[List[Any]] = Field(default_factory=list, description="Rule references")
    suggested_ar_visual: Optional[str] = Field(None, description="Hint for AR visualization")
    
    class Config:
        extra = "allow"


class ModelMetadata(BaseModel):
    """Metadata about the AI model used for generating the response."""
    model_name: Optional[str] = Field(None, description="Name of the model used")
    retrieved_chunk_count: Optional[int] = Field(None, description="Number of chunks retrieved")
    retrieval_scores: Optional[List[float]] = Field(None, description="Similarity scores")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in ms")
    
    class Config:
        extra = "allow"


class RuleReference(BaseModel):
    """Reference to a specific rule in a rulebook."""
    source: Optional[str] = Field(None, description="Source document name")
    section: Optional[str] = Field(None, description="Section name or number")
    page: Optional[int] = Field(None, description="Page number")
    
    class Config:
        extra = "allow"


class ARFieldLayout(BaseModel):
    """AR field layout information for dynamic rendering on the frontend."""
    anchor_position: Optional[str] = Field(
        None,
        description="Description of anchor/center point placement"
    )
    
    field_boundaries: Optional[str] = Field(
        None,
        description="Description of field boundaries for AR visualization"
    )
    
    safe_zone_radius_m: Optional[float] = Field(
        None,
        gt=0,
        description="Radius of safe zone around anchor in meters"
    )
    
    scoring_zones: Optional[List[Any]] = Field(
        None,
        description="List of scoring zones with distances and point values"
    )
    
    visual_hints: Optional[str] = Field(
        None,
        description="Additional hints for AR rendering"
    )
    
    class Config:
        extra = "allow"


# ============================================================================
# Phase 1: Initial Game Request/Response
# ============================================================================

class InitialGameRequest(BaseModel):
    """
    Request for initial game setup - returns rules briefing and field layout.
    Use this when starting a new game.
    """
    game_config: Optional[GameConfiguration] = Field(
        None,
        description="Game configuration settings"
    )
    
    session_id: Optional[str] = Field(
        None,
        description="Unique session identifier for logging"
    )
    
    client_version: Optional[str] = Field(
        None,
        description="Mobile app client version"
    )
    
    class Config:
        extra = "allow"
        json_schema_extra = {
            "example": {
                "game_config": {
                    "equipment_dimensions": {
                        "dandi_length_cm": 60,
                        "biyo_length_cm": 8
                    },
                    "ground_description": {
                        "surface_type": "grass",
                        "field_length_m": 30,
                        "field_width_m": 20
                    },
                    "num_players_available": 4,
                    "team_a_players": 2,
                    "team_b_players": 2
                },
                "session_id": "sess_abc123"
            }
        }


class InitialGameResponse(BaseModel):
    """
    Response for initial game setup - includes rules and field layout.
    """
    important_rules: Optional[List[InstructionCard]] = Field(
        default_factory=list,
        description="Most important rules to understand before starting"
    )
    
    field_layout: Optional[ARFieldLayout] = Field(
        None,
        description="AR field layout information"
    )
    
    game_overview: Optional[str] = Field(
        None,
        description="High-level overview of the game"
    )
    
    model_metadata: Optional[ModelMetadata] = Field(
        None,
        description="AI model metadata"
    )
    
    session_id: Optional[str] = Field(
        None,
        description="Session ID echo"
    )
    
    class Config:
        extra = "allow"


# ============================================================================
# Phase 2: In-Game Request/Response
# ============================================================================

class InGameRequest(BaseModel):
    """
    Request for in-game queries - scoring, fouls, rule clarifications.
    Use this during active gameplay.
    """
    game_config: Optional[GameConfiguration] = Field(
        None,
        description="Game configuration (should match initial game setup)"
    )
    
    query_type: Optional[str] = Field(
        None,
        description="Type of query: 'scoring', 'foul_check', 'clarification', or 'general'"
    )
    
    situation_summary: Optional[str] = Field(
        None,
        description="Description of the current game situation or question"
    )
    
    # Scoring specific fields
    estimated_distance_m: Optional[float] = Field(
        None,
        ge=0,
        description="Estimated distance of Biyo from anchor (for scoring queries)"
    )
    
    # Foul check specific fields
    action_description: Optional[str] = Field(
        None,
        description="Description of action to check for fouls"
    )
    
    player_team: Optional[str] = Field(
        None,
        description="Which team/player is involved"
    )
    
    session_id: Optional[str] = Field(
        None,
        description="Session identifier"
    )
    
    class Config:
        extra = "allow"
        json_schema_extra = {
            "example": {
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
                "situation_summary": "Player hit the Biyo and it landed 12 meters away",
                "estimated_distance_m": 12.0,
                "session_id": "sess_abc123"
            }
        }


class InGameResponse(BaseModel):
    """
    Response for in-game queries - flexible to handle scoring, fouls, and clarifications.
    """
    # Common fields
    cards: Optional[List[InstructionCard]] = Field(
        default_factory=list,
        description="Instruction cards with relevant information"
    )
    
    overall_summary: Optional[str] = Field(
        None,
        description="Summary of the ruling or answer"
    )
    
    # Scoring specific fields
    score: Optional[int] = Field(
        None,
        ge=0,
        description="Calculated score (for scoring queries)"
    )
    
    is_valid_attempt: Optional[bool] = Field(
        None,
        description="Whether this was a valid attempt"
    )
    
    # Foul check specific fields
    is_foul: Optional[bool] = Field(
        None,
        description="Whether the action is a foul"
    )
    
    penalty_description: Optional[str] = Field(
        None,
        description="Description of penalty if foul"
    )
    
    # Metadata
    model_metadata: Optional[ModelMetadata] = Field(
        None,
        description="AI model metadata"
    )
    
    session_id: Optional[str] = Field(
        None,
        description="Session ID echo"
    )
    
    game_state_update: Optional[Any] = Field(
        None,
        description="Optional game state update"
    )
    
    class Config:
        extra = "allow"


# ============================================================================
# Legacy/Backward Compatibility - RulesQuery (maps to InGame)
# ============================================================================

class RulesQueryRequest(BaseModel):
    """Legacy request model - use InGameRequest for new implementations."""
    
    situation_summary: Optional[str] = Field(
        None,
        description="Natural language description of the current game situation"
    )
    
    equipment_dimensions: Optional[EquipmentDimensions] = Field(
        None,
        description="Dimensions of Dandi and Biyo equipment"
    )
    
    ground_description: Optional[GroundDescription] = Field(
        None,
        description="Description of the playing field"
    )
    
    num_players_available: Optional[int] = Field(
        None,
        ge=1,
        le=50,
        description="Total number of players available"
    )
    
    team_a_players: Optional[int] = Field(None, ge=0, description="Players in team A")
    team_b_players: Optional[int] = Field(None, ge=0, description="Players in team B")
    game_phase: Optional[GamePhase] = Field(None, description="Current game phase")
    language_preference: Optional[str] = Field(default="en", description="Language code")
    client_version: Optional[str] = Field(None, description="Client version")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    class Config:
        extra = "allow"


class RulesQueryResponse(BaseModel):
    """Legacy response model - flexible to handle any LLM response."""
    
    cards: Optional[List[InstructionCard]] = Field(
        default_factory=list,
        description="List of instruction cards"
    )
    
    overall_summary: Optional[str] = Field(
        None,
        description="High-level summary"
    )
    
    model_metadata: Optional[ModelMetadata] = Field(
        None,
        description="AI model metadata"
    )
    
    session_id: Optional[str] = Field(None, description="Session ID echo")
    game_state_update: Optional[Any] = Field(None, description="Game state update")
    
    class Config:
        extra = "allow"


# ============================================================================
# Reindexing Models
# ============================================================================

class ReindexRequest(BaseModel):
    """Request to rebuild the FAISS index from rulebooks."""
    force_rebuild: bool = Field(default=False, description="Force rebuild even if index exists")


# ============================================================================
# Initial Rules Modified Models (for AR overlay cards)
# ============================================================================

class InitialRuleCard(BaseModel):
    """
    A single rule card optimized for AR overlay display.
    Contains one atomic rule that frontend can render as a card.
    """
    card_id: str = Field(..., description="Unique identifier for this card (e.g., 'rule_001')")
    category: str = Field(
        ..., 
        description="Rule category: 'objective', 'equipment', 'setup', 'scoring', 'gameplay', 'foul', 'safety', 'turn_order'"
    )
    title: str = Field(..., description="Short title for the card (max 50 chars)")
    body: str = Field(..., description="Rule explanation (max 200 chars for AR readability)")
    priority: int = Field(..., ge=1, le=10, description="Display priority (1=highest, show first)")
    icon_hint: Optional[str] = Field(None, description="Suggested icon: 'target', 'ruler', 'flag', 'warning', 'info', 'score', 'player'")
    ar_highlight: Optional[str] = Field(None, description="AR element to highlight when showing this card")
    
    class Config:
        extra = "allow"


class InitialRulesModifiedRequest(BaseModel):
    """
    Request for the modified initial rules endpoint.
    Includes game configuration for contextual rule generation.
    """
    game_config: GameConfiguration = Field(
        ...,
        description="Game configuration including equipment and field dimensions"
    )
    session_id: Optional[str] = Field(
        None,
        description="Unique session identifier for logging/tracking"
    )
    
    class Config:
        extra = "allow"
        json_schema_extra = {
            "example": {
                "game_config": {
                    "equipment_dimensions": {
                        "dandi_length_cm": 60,
                        "biyo_length_cm": 8
                    },
                    "ground_description": {
                        "surface_type": "grass",
                        "field_length_m": 30,
                        "field_width_m": 20
                    },
                    "num_players_available": 4
                },
                "session_id": "game_001"
            }
        }


class InitialRulesModifiedResponse(BaseModel):
    """
    Response containing all initial rules as separate cards for AR display.
    Rules are organized by category and priority for frontend rendering.
    """
    rules_cards: List[InitialRuleCard] = Field(
        ...,
        description="List of rule cards for AR overlay display"
    )
    total_cards: int = Field(..., description="Total number of rule cards")
    categories: List[str] = Field(..., description="List of unique categories in the response")
    game_summary: str = Field(..., description="Brief summary of Dandi Biyo game")
    equipment_adapted: bool = Field(
        ..., 
        description="Whether rules were adapted based on provided equipment dimensions"
    )
    field_adapted: bool = Field(
        ..., 
        description="Whether rules were adapted based on provided field dimensions"
    )
    model_metadata: Optional[ModelMetadata] = Field(None, description="AI model metadata")
    session_id: Optional[str] = Field(None, description="Session ID echo")
    
    class Config:
        extra = "allow"


class ReindexResponse(BaseModel):
    """Response from reindexing operation."""
    success: bool = Field(..., description="Whether reindexing was successful")
    message: str = Field(..., description="Status message")
    documents_processed: int = Field(..., ge=0, description="Documents processed")
    chunks_created: int = Field(..., ge=0, description="Chunks created and indexed")
    index_path: str = Field(..., description="Path where FAISS index was saved")


# ============================================================================
# Health Check Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    faiss_index_loaded: bool = Field(..., description="Whether FAISS index is loaded")
    gemini_api_accessible: bool = Field(..., description="Whether Gemini API is accessible")


# ============================================================================
# Error Models
# ============================================================================

class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Any] = Field(None, description="Additional error context")


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: ErrorDetail = Field(..., description="Error details")
    session_id: Optional[str] = Field(None, description="Session ID if available")
