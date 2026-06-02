"""
Simplified 2-phase game flow API routes for BiyoR AI Rules Engine.
Phase 1: initial_game - Game setup, rules briefing, field layout
Phase 2: in_game - Active gameplay queries (scoring, fouls, clarifications)
"""

import time
import json
import hashlib
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, status
from loguru import logger

# Simple in-memory cache for initial rules (avoids repeated LLM calls)
_initial_rules_cache: Dict[str, Dict[str, Any]] = {}

from app.models import (
    InitialGameRequest,
    InitialGameResponse,
    InGameRequest,
    InGameResponse,
    ARFieldLayout,
    InstructionCard,
    ModelMetadata,
    InitialRulesModifiedRequest,
    InitialRulesModifiedResponse,
    InitialRuleCard
)
from app.rag_pipeline import DandiBiyoRAGPipeline
from app.llm_client import GeminiRulesLLM
from app.config import settings


# Create router
router = APIRouter(prefix=f"/api/{settings.api_version}/game", tags=["game"])

# Global instances (will be injected via dependencies)
rag_pipeline: Optional[DandiBiyoRAGPipeline] = None
llm_client: Optional[GeminiRulesLLM] = None


def set_dependencies(pipeline: DandiBiyoRAGPipeline, llm: GeminiRulesLLM) -> None:
    """Set global dependencies for the game routes."""
    global rag_pipeline, llm_client
    rag_pipeline = pipeline
    llm_client = llm


def get_rag_pipeline() -> DandiBiyoRAGPipeline:
    """Dependency injection for RAG pipeline."""
    if rag_pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG pipeline not initialized"
        )
    return rag_pipeline


def get_llm_client() -> GeminiRulesLLM:
    """Dependency injection for LLM client."""
    if llm_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM client not initialized"
        )
    return llm_client


def _build_initial_game_schema() -> Dict[str, Any]:
    """Build JSON schema for initial game response."""
    return {
        "type": "object",
        "properties": {
            "important_rules": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "type": {"type": "string"},
                        "priority": {"type": "integer", "minimum": 1, "maximum": 10},
                        "body": {"type": "string"},
                        "reasoning_summary": {"type": "string"},
                        "related_rule_refs": {"type": "array", "items": {"type": "object"}},
                        "suggested_ar_visual": {"type": "string"}
                    }
                }
            },
            "field_layout": {
                "type": "object",
                "properties": {
                    "anchor_position": {"type": "string"},
                    "field_boundaries": {"type": "string"},
                    "safe_zone_radius_m": {"type": "number"},
                    "scoring_zones": {"type": "array", "items": {"type": "object"}},
                    "visual_hints": {"type": "string"}
                }
            },
            "game_overview": {"type": "string"}
        }
    }


def _build_in_game_schema() -> Dict[str, Any]:
    """Build JSON schema for in-game response."""
    return {
        "type": "object",
        "properties": {
            "cards": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "type": {"type": "string"},
                        "priority": {"type": "integer"},
                        "body": {"type": "string"},
                        "reasoning_summary": {"type": "string"}
                    }
                }
            },
            "overall_summary": {"type": "string"},
            "score": {"type": "integer"},
            "is_valid_attempt": {"type": "boolean"},
            "is_foul": {"type": "boolean"},
            "penalty_description": {"type": "string"}
        }
    }


@router.post("/initial", response_model=InitialGameResponse)
async def initial_game(
    request: InitialGameRequest,
    pipeline: DandiBiyoRAGPipeline = Depends(get_rag_pipeline),
    llm: GeminiRulesLLM = Depends(get_llm_client)
) -> InitialGameResponse:
    """
    Phase 1: Initial Game Setup
    
    Returns essential rules briefing and field layout for starting a new game.
    Call this endpoint when:
    - Starting a new game session
    - Players need to understand the rules
    - AR field overlay needs to be generated
    
    Returns:
    - important_rules: Key rules to understand before playing
    - field_layout: AR-friendly field configuration
    - game_overview: High-level game description
    """
    start_time = time.time()
    logger.info(f"Initial game request received. Session: {request.session_id}")
    
    try:
        # Build context query
        config = request.game_config or {}
        config_dict = config.model_dump() if hasattr(config, 'model_dump') else (config if isinstance(config, dict) else {})
        
        context_query = "Explain the basic rules and setup for Dandi Biyo game."
        
        if config_dict:
            num_players = config_dict.get('num_players_available', 0)
            if num_players:
                context_query += f" We have {num_players} players."
            
            ground = config_dict.get('ground_description', {})
            if ground:
                surface = ground.get('surface_type') if isinstance(ground, dict) else getattr(ground, 'surface_type', None)
                if surface:
                    surface_val = surface.value if hasattr(surface, 'value') else surface
                    context_query += f" Playing on {surface_val} surface."
        
        # Retrieve relevant context
        retrieved_chunks = pipeline.retrieve(context_query, top_k=5)
        context_text = "\n\n---\n\n".join([
            f"Source: {chunk.get('source', 'Unknown')}\n{chunk.get('text', '')}"
            for chunk in retrieved_chunks
        ])
        
        # Build prompt
        prompt = f"""You are an expert Dandi Biyo rules referee. Based on the retrieved rulebook context and game configuration, provide an initial game briefing.

RETRIEVED RULEBOOK CONTEXT:
{context_text}

GAME CONFIGURATION:
{json.dumps(config_dict, indent=2, default=str)}

Provide a JSON response with:
1. important_rules: Array of 3-5 most important rules as instruction cards
2. field_layout: AR field layout with anchor_position, field_boundaries, safe_zone_radius_m, scoring_zones, visual_hints
3. game_overview: Brief overview of the game (2-3 sentences)

Each rule card should have: id, title, type, priority (1-10), body, reasoning_summary

Focus on:
- Basic game objective
- Equipment setup
- Scoring fundamentals
- Safety guidelines
- Field dimensions and zones"""

        # Get LLM response
        response_dict = llm.generate_structured_response(
            prompt=prompt,
            response_schema=_build_initial_game_schema()
        )
        
        # Process response
        processing_time = (time.time() - start_time) * 1000
        
        # Build instruction cards
        important_rules = []
        for i, rule in enumerate(response_dict.get('important_rules', [])):
            card = InstructionCard(
                id=rule.get('id', f'rule_{i+1}'),
                title=rule.get('title', 'Rule'),
                type=rule.get('type', 'RULE'),
                priority=rule.get('priority', i+1),
                body=rule.get('body', ''),
                reasoning_summary=rule.get('reasoning_summary', ''),
                related_rule_refs=rule.get('related_rule_refs', []),
                suggested_ar_visual=rule.get('suggested_ar_visual')
            )
            important_rules.append(card)
        
        # Build field layout
        layout_data = response_dict.get('field_layout', {})
        field_layout = ARFieldLayout(
            anchor_position=layout_data.get('anchor_position'),
            field_boundaries=layout_data.get('field_boundaries'),
            safe_zone_radius_m=layout_data.get('safe_zone_radius_m'),
            scoring_zones=layout_data.get('scoring_zones', []),
            visual_hints=layout_data.get('visual_hints')
        )
        
        # Build metadata
        metadata = ModelMetadata(
            model_name=settings.gemini_primary_model,
            retrieved_chunk_count=len(retrieved_chunks),
            retrieval_scores=[c.get('score', 0.0) for c in retrieved_chunks],
            processing_time_ms=processing_time
        )
        
        logger.info(f"Initial game response generated in {processing_time:.0f}ms")
        
        return InitialGameResponse(
            important_rules=important_rules,
            field_layout=field_layout,
            game_overview=response_dict.get('game_overview', 'Dandi Biyo is a traditional stick-hitting game.'),
            model_metadata=metadata,
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"Error processing initial game request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate initial game response: {str(e)}"
        )


@router.post("/query", response_model=InGameResponse)
async def in_game_query(
    request: InGameRequest,
    pipeline: DandiBiyoRAGPipeline = Depends(get_rag_pipeline),
    llm: GeminiRulesLLM = Depends(get_llm_client)
) -> InGameResponse:
    """
    Phase 2: In-Game Query
    
    Handle all in-game queries including:
    - Scoring: Calculate points for hits
    - Foul checks: Determine if an action is a foul
    - Clarifications: Answer rule questions
    - General: Any other game-related queries
    
    Args:
        request: Contains query_type, situation_summary, and optional fields
    
    Returns:
        InGameResponse with cards, summary, and query-specific fields
    """
    start_time = time.time()
    query_type = request.query_type or "general"
    logger.info(f"In-game query received. Type: {query_type}, Session: {request.session_id}")
    
    try:
        # Build context query based on query type
        situation = request.situation_summary or ""
        
        if query_type == "scoring":
            distance = request.estimated_distance_m
            context_query = f"Scoring rules for Dandi Biyo. {situation}"
            if distance:
                context_query += f" Hit distance: {distance} meters."
        elif query_type == "foul_check":
            action = request.action_description or situation
            context_query = f"Foul rules and penalties in Dandi Biyo. Action: {action}"
        elif query_type == "clarification":
            context_query = f"Dandi Biyo rules clarification: {situation}"
        else:
            context_query = f"Dandi Biyo rules: {situation}"
        
        # Retrieve relevant context
        retrieved_chunks = pipeline.retrieve(context_query, top_k=5)
        context_text = "\n\n---\n\n".join([
            f"Source: {chunk.get('source', 'Unknown')}\n{chunk.get('text', '')}"
            for chunk in retrieved_chunks
        ])
        
        # Build config dict
        config = request.game_config or {}
        config_dict = config.model_dump() if hasattr(config, 'model_dump') else (config if isinstance(config, dict) else {})
        
        # Build prompt based on query type
        if query_type == "scoring":
            prompt = f"""You are an expert Dandi Biyo scoring referee.

RETRIEVED RULEBOOK CONTEXT:
{context_text}

GAME CONFIGURATION:
{json.dumps(config_dict, indent=2, default=str)}

SCORING QUERY:
Situation: {situation}
Estimated Distance: {request.estimated_distance_m} meters

Calculate the score and provide your ruling. Return JSON with:
- cards: Array of 1-3 instruction cards explaining the scoring
- overall_summary: Brief summary of the ruling
- score: The calculated score (integer)
- is_valid_attempt: Whether this was a valid scoring attempt (boolean)

Each card should have: id, title, type, priority, body, reasoning_summary"""

        elif query_type == "foul_check":
            prompt = f"""You are an expert Dandi Biyo foul referee.

RETRIEVED RULEBOOK CONTEXT:
{context_text}

GAME CONFIGURATION:
{json.dumps(config_dict, indent=2, default=str)}

FOUL CHECK QUERY:
Action: {request.action_description or situation}
Player/Team: {request.player_team or 'Unknown'}

Determine if this is a foul. Return JSON with:
- cards: Array of 1-3 instruction cards explaining the ruling
- overall_summary: Brief summary of the ruling
- is_foul: Whether this action is a foul (boolean)
- penalty_description: Description of penalty if foul (string or null)

Each card should have: id, title, type, priority, body, reasoning_summary"""

        else:
            prompt = f"""You are an expert Dandi Biyo rules referee.

RETRIEVED RULEBOOK CONTEXT:
{context_text}

GAME CONFIGURATION:
{json.dumps(config_dict, indent=2, default=str)}

QUERY:
{situation}

Provide a clear answer. Return JSON with:
- cards: Array of 1-3 instruction cards with relevant rules
- overall_summary: Brief summary of your answer

Each card should have: id, title, type, priority, body, reasoning_summary"""

        # Get LLM response
        response_dict = llm.generate_structured_response(
            prompt=prompt,
            response_schema=_build_in_game_schema()
        )
        
        # Process response
        processing_time = (time.time() - start_time) * 1000
        
        # Build instruction cards
        cards = []
        for i, card_data in enumerate(response_dict.get('cards', [])):
            card = InstructionCard(
                id=card_data.get('id', f'card_{i+1}'),
                title=card_data.get('title', 'Information'),
                type=card_data.get('type', 'RULE'),
                priority=card_data.get('priority', i+1),
                body=card_data.get('body', ''),
                reasoning_summary=card_data.get('reasoning_summary', '')
            )
            cards.append(card)
        
        # Build metadata
        metadata = ModelMetadata(
            model_name=settings.gemini_primary_model,
            retrieved_chunk_count=len(retrieved_chunks),
            retrieval_scores=[c.get('score', 0.0) for c in retrieved_chunks],
            processing_time_ms=processing_time
        )
        
        logger.info(f"In-game query response generated in {processing_time:.0f}ms")
        
        return InGameResponse(
            cards=cards,
            overall_summary=response_dict.get('overall_summary', ''),
            score=response_dict.get('score'),
            is_valid_attempt=response_dict.get('is_valid_attempt'),
            is_foul=response_dict.get('is_foul'),
            penalty_description=response_dict.get('penalty_description'),
            model_metadata=metadata,
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"Error processing in-game query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process in-game query: {str(e)}"
        )


def _build_initial_rules_modified_schema() -> Dict[str, Any]:
    """Build JSON schema for initial rules modified response."""
    return {
        "type": "object",
        "properties": {
            "rules_cards": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "card_id": {"type": "string"},
                        "category": {"type": "string"},
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                        "priority": {"type": "integer", "minimum": 1, "maximum": 10},
                        "icon_hint": {"type": "string"},
                        "ar_highlight": {"type": "string"}
                    },
                    "required": ["card_id", "category", "title", "body", "priority"]
                }
            },
            "game_summary": {"type": "string"}
        },
        "required": ["rules_cards", "game_summary"]
    }


@router.post("/initial_rule_modified", response_model=InitialRulesModifiedResponse)
async def initial_rules_modified(
    request: InitialRulesModifiedRequest,
    llm: GeminiRulesLLM = Depends(get_llm_client)
) -> InitialRulesModifiedResponse:
    """
    Modified Initial Rules Endpoint - Generates comprehensive rule cards for AR overlay.
    
    NOTE: This is a TEST endpoint that bypasses RAG and injects the ENTIRE PDF 
    content directly into the LLM prompt for experimentation purposes.
    
    This endpoint:
    1. Reads the ENTIRE Dandi Biyo rulebook PDF content
    2. Injects full content into LLM prompt (no chunking/retrieval)
    3. Uses LLM to reason and extract essential initial-stage rules
    4. Returns rules as individual cards optimized for AR frontend display
    
    The response adapts rules based on the provided game configuration:
    - Equipment dimensions (dandi/biyo sizes)
    - Ground/field specifications
    - Number of players
    
    Use this endpoint when starting a new game to display rules overlay in AR.
    
    Request Body:
    - game_config: Equipment dimensions, ground description, player count
    - session_id: Optional session identifier
    
    Returns:
    - rules_cards: List of rule cards (each with category, title, body, priority)
    - total_cards: Number of cards generated
    - categories: Unique categories covered
    - game_summary: Brief game overview
    """
    from pathlib import Path
    from langchain_community.document_loaders import PyPDFLoader
    
    start_time = time.time()
    logger.info(f"Initial rules modified request received (NO RAG - Full PDF). Session: {request.session_id}")
    
    try:
        # Extract game configuration
        config = request.game_config
        config_dict = config.model_dump() if hasattr(config, 'model_dump') else (config if isinstance(config, dict) else {})
        
        # ============================================================
        # CHECK CACHE FIRST (avoid repeated LLM calls)
        # ============================================================
        cache_key = hashlib.md5(json.dumps(config_dict, sort_keys=True, default=str).encode()).hexdigest()
        
        if cache_key in _initial_rules_cache:
            logger.info(f"[{request.session_id}] Returning CACHED response (key: {cache_key[:8]}...)")
            # Deep copy cached data to avoid mutation issues with Pydantic models
            import copy
            cached_response = copy.deepcopy(_initial_rules_cache[cache_key])
            cached_response['session_id'] = request.session_id
            # Safely update processing time in model_metadata dict
            if isinstance(cached_response.get('model_metadata'), dict):
                cached_response['model_metadata']['processing_time_ms'] = (time.time() - start_time) * 1000
                cached_response['model_metadata']['cache_hit'] = True
            return InitialRulesModifiedResponse(**cached_response)
        
        # Check what adaptations are available
        equipment_adapted = bool(config_dict.get('equipment_dimensions'))
        field_adapted = bool(config_dict.get('ground_description'))
        
        # ============================================================
        # LOAD ENTIRE PDF CONTENT (bypassing RAG)
        # ============================================================
        pdf_path = Path(settings.rulebooks_dir) / "Dandi_Biyo_Rulebook_RAG.pdf"
        
        if not pdf_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rulebook PDF not found at {pdf_path}"
            )
        
        logger.info(f"Loading entire PDF from: {pdf_path}")
        loader = PyPDFLoader(str(pdf_path))
        pdf_pages = loader.load()
        
        # Concatenate all pages into one large text block
        full_pdf_content = "\n\n--- PAGE BREAK ---\n\n".join([
            f"[Page {i+1}]\n{page.page_content}"
            for i, page in enumerate(pdf_pages)
        ])
        
        logger.info(f"Loaded {len(pdf_pages)} pages, {len(full_pdf_content)} characters total")
        
        # Format equipment info if provided
        equipment_info = ""
        if config_dict.get('equipment_dimensions'):
            equip = config_dict['equipment_dimensions']
            equipment_info = f"""
EQUIPMENT PROVIDED:
- Dandi (stick) length: {equip.get('dandi_length_cm', 'Not specified')} cm
- Biyo (peg) length: {equip.get('biyo_length_cm', 'Not specified')} cm
- Biyo diameter: {equip.get('biyo_diameter_cm', 'Not specified')} cm
"""
        
        # Format field info if provided
        field_info = ""
        if config_dict.get('ground_description'):
            ground = config_dict['ground_description']
            surface = ground.get('surface_type')
            if hasattr(surface, 'value'):
                surface = surface.value
            field_info = f"""
FIELD PROVIDED:
- Surface type: {surface or 'Not specified'}
- Field length: {ground.get('field_length_m', 'Not specified')} meters
- Field width: {ground.get('field_width_m', 'Not specified')} meters
"""
        
        # Format player info
        player_info = ""
        if config_dict.get('num_players_available'):
            player_info = f"\nPLAYERS AVAILABLE: {config_dict['num_players_available']}"
        
        # Build comprehensive prompt with FULL PDF content
        prompt = f"""You are an expert Dandi Biyo rules teacher creating rule cards for an AR (Augmented Reality) game overlay.

============================================================
COMPLETE DANDI BIYO RULEBOOK (FULL CONTENT)
============================================================
{full_pdf_content}
============================================================
END OF RULEBOOK
============================================================

GAME CONFIGURATION:
{equipment_info}
{field_info}
{player_info}

YOUR TASK:
Analyze the COMPLETE rulebook above and create a comprehensive set of RULE CARDS for new players starting a game.
Each card should contain ONE atomic rule - short, clear, and suitable for AR display.

REQUIREMENTS:
1. Generate EXACTLY 10 rule cards covering ALL essential rules
2. Each card body should be MAX 150 characters for AR readability
3. Organize cards by category and priority
4. Include all critical rules - be comprehensive

CATEGORIES TO COVER (use all 10):
- "objective": What is the goal of the game?
- "equipment": Equipment rules and requirements (Dandi and Biyo specs)
- "setup": Field setup, hole (khop) placement, and initial positioning
- "gameplay": Core gameplay mechanics - how to hit the Biyo
- "turns": Turn structure, player rotation, and attempts per turn
- "scoring": How points (tyaks) are calculated and measured
- "defending": Defender's role - catching and returning the Biyo
- "foul": Common fouls, out conditions, and what to avoid
- "winning": Win conditions and game end rules
- "safety": Safety rules and guidelines

PRIORITY GUIDE:
- 1-3: Critical rules (must know before playing)
- 4-6: Important rules (core gameplay)
- 7-10: Good to know (edge cases, advanced)

ICON HINTS (choose appropriate):
- "target": For objective/goal rules
- "ruler": For measurement/distance rules
- "flag": For field/boundary rules
- "warning": For foul/penalty rules
- "info": For general information
- "score": For scoring rules
- "player": For turn/player rules

AR HIGHLIGHT OPTIONS:
- "field_center": Highlight center of field
- "scoring_zones": Show scoring zone rings
- "boundary_lines": Show field boundaries
- "equipment_area": Highlight equipment position
- "player_position": Show where players stand
- null: No AR highlight needed

ADAPT THE RULES based on the provided equipment and field dimensions where applicable.

Return a JSON object with:
{{
  "rules_cards": [
    {{
      "card_id": "rule_001",
      "category": "objective",
      "title": "Game Objective",
      "body": "Hit the Biyo as far as possible with the Dandi to score points.",
      "priority": 1,
      "icon_hint": "target",
      "ar_highlight": "field_center"
    }},
    ... more cards
  ],
  "game_summary": "Brief 2-3 sentence summary of Dandi Biyo"
}}

Generate the complete JSON now:"""

        # Get LLM response (use raw JSON method to preserve rules_cards structure)
        # Pass PDF path and game config for fallback generation if rate limited
        response_dict = llm.generate_raw_json_response(
            prompt=prompt,
            response_schema=_build_initial_rules_modified_schema(),
            pdf_path=str(pdf_path),
            game_config=config_dict
        )
        
        # Process response
        processing_time = (time.time() - start_time) * 1000
        
        # Build rule cards from response
        rules_cards: List[InitialRuleCard] = []
        categories_set = set()
        
        for card_data in response_dict.get('rules_cards', []):
            card = InitialRuleCard(
                card_id=card_data.get('card_id', f'rule_{len(rules_cards)+1:03d}'),
                category=card_data.get('category', 'general'),
                title=card_data.get('title', 'Rule'),
                body=card_data.get('body', ''),
                priority=card_data.get('priority', 5),
                icon_hint=card_data.get('icon_hint'),
                ar_highlight=card_data.get('ar_highlight')
            )
            rules_cards.append(card)
            categories_set.add(card.category)
        
        # Sort cards by priority
        rules_cards.sort(key=lambda x: x.priority)
        
        # Build metadata (no retrieval scores since we're not using RAG)
        metadata = ModelMetadata(
            model_name=settings.gemini_primary_model,
            retrieved_chunk_count=len(pdf_pages),  # Number of PDF pages loaded
            retrieval_scores=[],  # No RAG retrieval
            processing_time_ms=processing_time
        )
        
        logger.info(
            f"Initial rules modified response generated (NO RAG): {len(rules_cards)} cards, "
            f"{len(categories_set)} categories, {processing_time:.0f}ms"
        )
        
        # Build response data with plain dicts for caching compatibility
        response_data = {
            'rules_cards': [
                card.model_dump() if hasattr(card, 'model_dump') else card 
                for card in rules_cards
            ],
            'total_cards': len(rules_cards),
            'categories': sorted(list(categories_set)),
            'game_summary': response_dict.get('game_summary', 'Dandi Biyo is a traditional Nepali stick-hitting game.'),
            'equipment_adapted': equipment_adapted,
            'field_adapted': field_adapted,
            'model_metadata': metadata.model_dump() if hasattr(metadata, 'model_dump') else metadata,
            'session_id': request.session_id
        }
        
        # ============================================================
        # CACHE THE RESPONSE (only if we got valid rules)
        # ============================================================
        if len(rules_cards) > 0:
            # Store as plain dicts (not Pydantic models) to avoid mutation issues
            import copy
            cache_data = copy.deepcopy(response_data)
            cache_data['session_id'] = None  # Will be set on retrieval
            _initial_rules_cache[cache_key] = cache_data
            logger.info(f"[{request.session_id}] Cached response (key: {cache_key[:8]}..., {len(rules_cards)} cards)")
        
        return InitialRulesModifiedResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing initial rules modified request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate initial rules: {str(e)}"
        )
