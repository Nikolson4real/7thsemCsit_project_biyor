"""
Chat Routes for Text-Based Dandi Biyo Referee
----------------------------------------------
API endpoints for conversational game refereeing.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status

from app.chat_models import (
    ChatRequest, ChatResponse, GameState, GameSummary
)
from app.chat_referee import get_chat_referee, ChatReferee

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat Referee"])


def get_referee() -> ChatReferee:
    """Dependency to get chat referee instance."""
    return get_chat_referee()


# =============================================================================
# CHAT ENDPOINTS
# =============================================================================

@router.post(
    "/",
    response_model=ChatResponse,
    summary="Send chat message to referee",
    description="""
    Send a natural language message to the Dandi Biyo referee.
    The referee will parse your input, calculate scores, and respond naturally.
    
    **Game Flow:**
    1. Start: Send "Team [name], START" to begin
    2. Turns: Provide player name when prompted
    3. Hutnu: Describe the hit (zone, safe zone, any OUT)
    4. Tyak: Describe tapping attempt if any
    5. End: Game ends after 30 min or manually
    
    **Example Messages:**
    - "Team Tigers, START"
    - "Player Ram"
    - "Hutnu zone 3, safe middle, not out"
    - "Tyak zone 4, 3 taps"
    - "Caught in air" (OUT)
    - "No tyak"
    - "score" / "rules" / "help"
    """
)
async def send_message(request: ChatRequest) -> ChatResponse:
    """
    Process a chat message and return referee response.
    
    The response includes:
    - chat_text: Natural language response
    - embedded_json: Structured score/game data for app parsing
    - state: Current game state
    - next_prompt: Suggested next action
    """
    referee = get_referee()
    
    try:
        logger.info(f"[{request.session_id}] Chat: {request.message[:50]}...")
        response = referee.process_message(request)
        logger.info(f"[{request.session_id}] Phase: {response.state.phase}, Score: {response.state.total_score}")
        return response
    
    except Exception as e:
        import traceback
        logger.error(f"[{request.session_id}] Chat error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get(
    "/state/{session_id}",
    response_model=GameState,
    summary="Get current game state",
    description="Retrieve the current state of a game session for polling/sync."
)
async def get_state(session_id: str) -> GameState:
    """Get current game state for a session."""
    referee = get_referee()
    
    if session_id not in referee.sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found"
        )
    
    return referee.sessions[session_id]


@router.post(
    "/reset/{session_id}",
    response_model=GameState,
    summary="Reset game session",
    description="Reset a game session to start a new game."
)
async def reset_session(session_id: str) -> GameState:
    """Reset a game session."""
    referee = get_referee()
    state = referee.reset_session(session_id)
    logger.info(f"[{session_id}] Session reset")
    return state


@router.delete(
    "/session/{session_id}",
    summary="Delete game session",
    description="Permanently delete a game session."
)
async def delete_session(session_id: str):
    """Delete a game session."""
    referee = get_referee()
    
    if referee.delete_session(session_id):
        logger.info(f"[{session_id}] Session deleted")
        return {"message": f"Session '{session_id}' deleted"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found"
        )


@router.get(
    "/sessions",
    summary="List all active sessions",
    description="Get a list of all active game sessions (admin endpoint)."
)
async def list_sessions():
    """List all active sessions."""
    referee = get_referee()
    
    sessions = []
    for session_id, state in referee.sessions.items():
        sessions.append({
            "session_id": session_id,
            "team": state.team,
            "turn": state.turn,
            "score": state.total_score,
            "time_left": state.time_left,
            "phase": state.phase,
            "created_at": state.created_at.isoformat(),
            "updated_at": state.updated_at.isoformat()
        })
    
    return {
        "total_sessions": len(sessions),
        "sessions": sessions
    }


@router.get(
    "/history/{session_id}",
    summary="Get chat history",
    description="Retrieve the full chat history for a session."
)
async def get_history(session_id: str, limit: int = 50):
    """Get chat history for a session."""
    referee = get_referee()
    
    if session_id not in referee.sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found"
        )
    
    state = referee.sessions[session_id]
    history = state.history[-limit:] if limit > 0 else state.history
    
    return {
        "session_id": session_id,
        "total_messages": len(state.history),
        "returned_messages": len(history),
        "history": history
    }


@router.get(
    "/health",
    summary="Chat service health check",
    description="Check if the chat referee service is healthy."
)
async def health_check():
    """Health check for chat service."""
    referee = get_referee()
    
    return {
        "status": "healthy",
        "service": "chat_referee",
        "model": referee.model,
        "active_sessions": len(referee.sessions),
        "chat_enabled": True
    }
