"""
Text-Based Conversational Dandi Biyo Referee
---------------------------------------------
LLM-powered chat referee with embedded scoring algorithm.
No RAG - rules are embedded directly in the prompt for speed.
Uses Groq Llama-3.1-8B-Instruct for fast, natural responses.
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from groq import Groq

from app.chat_models import (
    GameState, TurnEvent, HutneEvent, TyakEvent,
    SafeZone, ParsedInput, ScoreBreakdown, GameSummary,
    ChatRequest, ChatResponse
)
from app.config import settings

logger = logging.getLogger(__name__)

# =============================================================================
# EMBEDDED SCORING ALGORITHM PROMPT
# =============================================================================
SCORING_ALGORITHM_PROMPT = """
DANDI BIYO SCORING ALGORITHM v1.0
=================================

**EQUIPMENT & FIELD**:
- Dandi: 45cm stick. Biyo: 15cm pointed pin.
- Field: 10m length, square base with Khop hole (4in x 6in depth) at edge.
- Layout: Central square (hitting/Khop), 2 running paths, fan-shaped landing (7 zones 0-6).
- Zone Scoring: score = zone number where Biyo first lands; zone > 6 = boundary OUT, no score.
- Safe Zones: 2 paths × 3 zones (total 6). Furthest reached counts: Nearest=2, Middle=4, Furthest=6 (0 if none/failed).

**TEAMS & TIME**:
- 2 teams: Dandi (hitting, 5 active + 2 subs), Biyo (fielding).
- 30 minutes hitting time per team. No scoring after time = 0. Rotate on OUT; continue until time expires.

**SCORING FORMULAS**:
1. HUTNU SCORE:
   - If OUT or zone > 6: Hutnu = 0
   - Else: Hutnu = landing_zone + safe_points
   - safe_points: nearest=2, middle=4, furthest=6, none=0

2. TYAK SCORE (only if Hutnu NOT OUT):
   - If not attempted OR Hutnu OUT OR Tyak OUT OR taps <= 0 OR zone > 6: Tyak = 0
   - Else: Tyak = 2 × tyak_zone

3. TURN SCORE:
   - If Hutnu OUT: Turn = 0 (entire turn lost)
   - If Tyak OUT: Turn = Hutnu only (Tyak doesn't count, but Hutnu preserved)
   - Else: Turn = Hutnu + Tyak

**OUT CONDITIONS** (any triggers OUT):
- Biyo returned to Khop by fielder
- Thrown Biyo hits the Dandi
- Biyo caught in air by fielder
- Zero Tyak taps (if Tyak attempted)
- Boundary violation (zone > 6)

**EXAMPLES**:
- "Zone 3, safe middle" → Hutnu = 3 + 4 = 7
- "Zone 3, safe middle" + "Tyak zone 4, 3 taps" → Hutnu=7 + Tyak=8 = 15
- "Hutnu caught in air" → Turn = 0 (OUT during Hutnu)
- "Zone 5, no safe, Tyak out zone 2" → Turn = 5 (Tyak lost, Hutnu preserved)
"""

REFEREE_PERSONA = """
You are a warm, knowledgeable Dandi Biyo referee named "Dai" (meaning elder brother in Nepali).
- Chat casually and naturally, like a friendly village elder explaining the game.
- Confirm details before calculating ("So Ram hit to zone 3 and reached the middle safe zone, right?").
- Celebrate good plays ("Ramro! That's a solid hit!") and console misses ("Ke garne, next time!").
- Enforce rules fairly but kindly. Explain why if a play is invalid.
- Use occasional Nepali words for flavor: "Ramro" (good), "Bahini/Dai" (sister/brother), "Hajur" (yes/okay).
- Keep responses concise but warm - this is a mobile text chat.
- ALWAYS guide the user to the next step in the game flow.
"""

GAME_FLOW_PROMPT = """
**GAME FLOW** (follow this order):
1. START: Wait for team name + "START" → Initialize timer=30min, score=0, turn=1. Ask for first player.
2. TURN START: "Turn N: Player name?" → Record player, move to HUTNU phase.
3. HUTNU: Ask about Hutnu result:
   - "Was player OUT during Hutnu? (caught, returned to khop, hit dandi?)"
   - If OUT: Hutnu=0, turn ends, next player.
   - If NOT out: "Which zone (0-6) did Biyo land?" and "Safe zone reached (nearest/middle/furthest/none)?"
4. TYAK (only if Hutnu not OUT): 
   - "Tyak attempt? (Y/N)"
   - If Yes: "OUT during Tyak?" and "Tyak zone? How many taps?"
5. CALCULATE: Use algorithm, show breakdown, add to total.
6. TURN END: Show turn score, total score, time remaining. Ask "Ready for next turn?"
7. TIME CHECK: If time <= 0, end game automatically.
8. END: Show final summary with all stats.

**CURRENT PHASE**: {phase}
**CURRENT STATE**: Turn {turn}, Score {score}, Time {time}min
"""


class ChatReferee:
    """
    Text-based conversational Dandi Biyo referee.
    Manages game state and provides natural language interactions
    with embedded scoring calculations.
    """
    
    def __init__(self):
        """Initialize the chat referee with Groq client."""
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = getattr(settings, 'groq_chat_model', "llama-3.1-8b-instant")
        self.sessions: Dict[str, GameState] = {}  # In-memory session storage
        logger.info(f"ChatReferee initialized with model: {self.model}")
    
    def get_or_create_session(self, session_id: str) -> GameState:
        """Get existing session or create new one."""
        if session_id not in self.sessions:
            self.sessions[session_id] = GameState(session_id=session_id)
            logger.info(f"Created new session: {session_id}")
        return self.sessions[session_id]
    
    def reset_session(self, session_id: str) -> GameState:
        """Reset a session to initial state."""
        self.sessions[session_id] = GameState(session_id=session_id)
        logger.info(f"Reset session: {session_id}")
        return self.sessions[session_id]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False
    
    # =========================================================================
    # INPUT PARSING
    # =========================================================================
    
    def parse_user_input(self, message: str, state: GameState) -> ParsedInput:
        """
        Parse user's natural language input to extract game events.
        Uses rule-based parsing first, then LLM for ambiguous cases.
        IMPORTANT: Prioritize current game phase for context-aware parsing.
        """
        msg_lower = message.lower().strip()
        parsed = ParsedInput(raw_text=message, intent="unknown")
        
        # Detect START intent
        if "start" in msg_lower or state.phase == "start":
            parsed.intent = "start"
            # Extract team name (words before "start" or after "team")
            team_match = re.search(r'team\s+(\w+)', msg_lower) or re.search(r'(\w+)\s*,?\s*start', msg_lower)
            if team_match:
                parsed.team_name = team_match.group(1).capitalize()
            parsed.confidence = 0.9 if parsed.team_name else 0.6
            return parsed
        
        # Detect END/RESET intent
        if any(word in msg_lower for word in ["end", "stop", "finish", "quit", "restart", "reset"]):
            parsed.intent = "end" if "restart" not in msg_lower and "reset" not in msg_lower else "reset"
            parsed.confidence = 0.9
            return parsed
        
        # Detect player name for TURN phase
        if state.phase == "turn" or "player" in msg_lower:
            parsed.intent = "turn"
            # Extract player name
            name_match = re.search(r'player\s+(\w+)', msg_lower) or re.search(r'^(\w+)$', msg_lower.strip())
            if name_match:
                parsed.player_name = name_match.group(1).capitalize()
            parsed.confidence = 0.8 if parsed.player_name else 0.5
            return parsed
        
        # PHASE-AWARE: Prioritize current phase for parsing
        # If in tyak phase, interpret input as tyak first
        if state.phase == "tyak":
            parsed.intent = "tyak"
            parsed.tyak = self._parse_tyak(msg_lower)
            
            # If no tyak parsed but we have a standalone number, treat as zone
            if parsed.tyak.zone == 0 and not parsed.tyak.out:
                number_match = re.search(r'\b([1-6])\b', msg_lower)
                if number_match:
                    zone = int(number_match.group(1))
                    is_out = any(word in msg_lower for word in ["out", "caught", "returned", "missed"])
                    parsed.tyak = TyakEvent(attempted=True, zone=zone, taps=1, out=is_out)
            
            parsed.confidence = 0.85 if parsed.tyak.attempted else 0.6
            return parsed
        
        # If in hutnu phase, interpret input as hutnu first
        if state.phase == "hutnu":
            parsed.intent = "hutnu"
            parsed.hutnu = self._parse_hutnu(msg_lower)
            parsed.confidence = 0.85 if parsed.hutnu.zone > 0 or parsed.hutnu.out else 0.6
            return parsed
        
        # Detect HUTNU event by keywords (when not in a specific phase)
        if any(word in msg_lower for word in ["hutnu", "hit", "zone", "caught", "out", "safe"]):
            parsed.intent = "hutnu"
            parsed.hutnu = self._parse_hutnu(msg_lower)
            parsed.confidence = 0.85 if parsed.hutnu.zone > 0 or parsed.hutnu.out else 0.6
            return parsed
        
        # Detect TYAK event by keywords (when not in a specific phase)
        if any(word in msg_lower for word in ["tyak", "tap", "taps"]):
            parsed.intent = "tyak"
            parsed.tyak = self._parse_tyak(msg_lower)
            parsed.confidence = 0.85 if parsed.tyak.attempted else 0.6
            return parsed
        
        # Query intent (asking about rules, score, etc.)
        if any(word in msg_lower for word in ["what", "how", "score", "rule", "help", "?"]):
            parsed.intent = "query"
            parsed.confidence = 0.7
            return parsed
        
        return parsed
    
    def _parse_hutnu(self, text: str) -> HutneEvent:
        """Parse Hutnu event from text."""
        hutnu = HutneEvent()
        
        # Check for OUT conditions
        out_keywords = ["caught", "out", "returned", "hit dandi", "boundary"]
        if any(kw in text for kw in out_keywords):
            # Distinguish between "not out" and actual out
            if "not out" in text or "no out" in text or "safe" in text:
                hutnu.out = False
            else:
                hutnu.out = True
        
        # Extract zone number
        zone_match = re.search(r'zone\s*(\d)', text) or re.search(r'(\d)\s*zone', text)
        if zone_match:
            hutnu.zone = min(int(zone_match.group(1)), 7)
        else:
            # Descriptive zones
            if "far" in text or "long" in text:
                hutnu.zone = 5
            elif "medium" in text or "mid" in text:
                hutnu.zone = 3
            elif "short" in text or "near" in text:
                hutnu.zone = 1
        
        # Check for boundary (auto-OUT)
        if hutnu.zone > 6 or "boundary" in text:
            hutnu.zone = 7
            hutnu.out = True
        
        # Extract safe zone
        if "furthest" in text or "far safe" in text:
            hutnu.safe = SafeZone.FURTHEST
        elif "middle" in text or "mid safe" in text:
            hutnu.safe = SafeZone.MIDDLE
        elif "nearest" in text or "near safe" in text or "first safe" in text:
            hutnu.safe = SafeZone.NEAREST
        else:
            hutnu.safe = SafeZone.NONE
        
        return hutnu
    
    def _parse_tyak(self, text: str) -> TyakEvent:
        """Parse Tyak event from text."""
        tyak = TyakEvent()
        text_stripped = text.strip().lower()
        
        # Check if Tyak was explicitly declined
        decline_words = ["no", "n", "skip", "pass", "decline", "nope"]
        if "no tyak" in text or any(text_stripped == word for word in decline_words):
            tyak.attempted = False
            return tyak
        
        # Check for OUT conditions
        out_keywords = ["out", "caught", "returned", "missed", "hit dandi"]
        is_out = any(kw in text for kw in out_keywords) and "not out" not in text and "no out" not in text
        
        # Check if Tyak was attempted (explicit confirmation OR zone/tap info present)
        accept_words = ["yes", "y", "yeah", "yep", "sure", "ok", "okay"]
        has_explicit_yes = any(text_stripped == word or text_stripped.startswith(word + " ") or text_stripped.startswith(word + ",") for word in accept_words)
        has_tyak_keyword = "tyak" in text or "tap" in text
        
        # Extract zone
        zone = 0
        zone_match = re.search(r'zone\s*(\d)', text) or re.search(r'(\d)\s*zone', text)
        if zone_match:
            zone = min(int(zone_match.group(1)), 7)
        else:
            # Try to find standalone number (1-6) that could be zone
            number_match = re.search(r'\b([1-6])\b', text)
            if number_match and (has_explicit_yes or has_tyak_keyword):
                zone = int(number_match.group(1))
        
        # Extract taps
        taps = 0
        taps_match = re.search(r'(\d+)\s*tap', text)
        if taps_match:
            taps = int(taps_match.group(1))
        elif zone > 0 and not is_out:
            taps = 1  # Assume at least 1 tap if Tyak successful
        
        # Determine if Tyak was attempted
        # Case 1: User said "yes" without zone -> needs to ask for zone
        if has_explicit_yes and zone == 0 and not is_out:
            tyak.attempted = True
            tyak.zone = 0  # Signal that we need to ask for zone
            tyak.taps = 0
            tyak.out = False
            return tyak
        
        # Case 2: User provided zone info
        if zone > 0 or has_tyak_keyword or taps_match:
            tyak.attempted = True
            tyak.zone = zone
            tyak.taps = taps
            tyak.out = is_out
            return tyak
        
        # Case 3: User provided OUT info during tyak
        if is_out and (has_explicit_yes or has_tyak_keyword):
            tyak.attempted = True
            tyak.zone = zone
            tyak.taps = 0
            tyak.out = True
            return tyak
        
        return tyak
    
    # =========================================================================
    # SCORING CALCULATION
    # =========================================================================
    
    def calculate_score(self, turn: TurnEvent, time_left: float) -> ScoreBreakdown:
        """
        Calculate score using the embedded algorithm.
        Returns detailed breakdown with reasoning.
        """
        breakdown = ScoreBreakdown()
        reasoning_parts = []
        
        # Time check
        if time_left <= 0:
            breakdown.reasoning = "Game over - time expired. No score added."
            return breakdown
        
        # HUTNU calculation
        breakdown.hutnu_zone = turn.hutnu.zone
        breakdown.hutnu_safe = turn.hutnu.safe.value
        breakdown.hutnu_safe_points = turn.hutnu.safe_points
        
        if turn.hutnu.out:
            breakdown.hutnu_score = 0
            breakdown.is_out = True
            breakdown.out_reason = "OUT during Hutnu"
            reasoning_parts.append(f"Hutnu: OUT → 0 points (turn lost)")
        elif turn.hutnu.zone > 6:
            breakdown.hutnu_score = 0
            breakdown.is_out = True
            breakdown.out_reason = "Boundary violation (zone > 6)"
            reasoning_parts.append(f"Hutnu: Boundary OUT (zone {turn.hutnu.zone}) → 0 points")
        else:
            breakdown.hutnu_score = turn.hutnu.score
            reasoning_parts.append(
                f"Hutnu: zone {turn.hutnu.zone} + safe '{turn.hutnu.safe.value}' ({breakdown.hutnu_safe_points}) = {breakdown.hutnu_score}"
            )
        
        # TYAK calculation (only if Hutnu not OUT)
        breakdown.tyak_attempted = turn.tyak.attempted
        
        if turn.hutnu.out:
            breakdown.tyak_score = 0
            reasoning_parts.append("Tyak: N/A (Hutnu was OUT)")
        elif not turn.tyak.attempted:
            breakdown.tyak_score = 0
            reasoning_parts.append("Tyak: Not attempted → 0")
        elif turn.tyak.out:
            breakdown.tyak_score = 0
            breakdown.is_out = True
            breakdown.out_reason = "OUT during Tyak (Hutnu score preserved)"
            reasoning_parts.append(f"Tyak: OUT → 0 (but Hutnu {breakdown.hutnu_score} preserved)")
        elif turn.tyak.taps <= 0:
            breakdown.tyak_score = 0
            reasoning_parts.append("Tyak: Zero taps → 0")
        elif turn.tyak.zone > 6:
            breakdown.tyak_score = 0
            breakdown.is_out = True
            breakdown.out_reason = "Tyak boundary violation"
            reasoning_parts.append(f"Tyak: Boundary (zone {turn.tyak.zone}) → 0")
        else:
            breakdown.tyak_zone = turn.tyak.zone
            breakdown.tyak_taps = turn.tyak.taps
            breakdown.tyak_score = turn.tyak.score
            reasoning_parts.append(
                f"Tyak: 2 × zone {turn.tyak.zone} = {breakdown.tyak_score} ({turn.tyak.taps} taps)"
            )
        
        # Total
        breakdown.turn_score = breakdown.hutnu_score + breakdown.tyak_score
        reasoning_parts.append(f"TOTAL: {breakdown.hutnu_score} + {breakdown.tyak_score} = {breakdown.turn_score}")
        
        breakdown.reasoning = " | ".join(reasoning_parts)
        return breakdown
    
    # =========================================================================
    # RESPONSE GENERATION
    # =========================================================================
    
    def generate_response(
        self, 
        user_message: str, 
        state: GameState,
        parsed: ParsedInput,
        score_breakdown: Optional[ScoreBreakdown] = None
    ) -> Tuple[str, Optional[Dict[str, Any]], str]:
        """
        Generate natural language response using LLM.
        Returns: (chat_text, embedded_json, next_prompt)
        """
        # Build context for LLM
        system_prompt = f"""
{REFEREE_PERSONA}

{SCORING_ALGORITHM_PROMPT}

{GAME_FLOW_PROMPT.format(
    phase=state.phase,
    turn=state.turn,
    score=state.total_score,
    time=state.time_left
)}

CURRENT GAME STATE:
- Team: {state.team or 'Not set'}
- Turn: {state.turn}
- Total Score: {state.total_score}
- Time Remaining: {state.time_left:.1f} minutes
- Current Player: {state.current_player or 'None'}
- Phase: {state.phase}

PARSED USER INPUT:
- Intent: {parsed.intent}
- Player: {parsed.player_name or 'N/A'}
- Hutnu: {parsed.hutnu.model_dump() if parsed.hutnu else 'N/A'}
- Tyak: {parsed.tyak.model_dump() if parsed.tyak else 'N/A'}

{f'SCORE CALCULATION: {score_breakdown.model_dump()}' if score_breakdown else ''}

Respond naturally as Dai the referee. Keep it concise (2-4 sentences). 
End with a clear question or prompt for the next step.
Do NOT include JSON in your response - that's handled separately.
"""
        
        # Recent chat history (last 6 messages for context)
        history_context = ""
        if state.history:
            recent = state.history[-6:]
            history_context = "\n".join([
                f"{'User' if h['role']=='user' else 'Referee'}: {h['content']}"
                for h in recent if isinstance(h, dict)
            ])
        
        user_prompt = f"""
Recent conversation:
{history_context}

User's latest message: "{user_message}"

Generate a friendly, natural response as Dai the referee. Guide to the next step.
"""
        
        logger.info("[GEN] Calling LLM...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            chat_text = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            chat_text = self._get_fallback_response(state, parsed, score_breakdown)
        
        # Determine embedded JSON and next prompt
        embedded_json = None
        next_prompt = ""
        
        if score_breakdown and score_breakdown.turn_score >= 0:
            embedded_json = {
                "type": "score_breakdown",
                "data": score_breakdown.model_dump()
            }
        
        if state.is_game_over():
            summary = GameSummary(
                team=state.team,
                total_turns=state.turn - 1,
                final_score=state.total_score,
                players=state.players,
                game_duration=30.0 - state.time_left,
                average_score_per_turn=state.total_score / max(1, state.turn - 1)
            )
            embedded_json = {
                "type": "game_summary",
                "data": summary.model_dump()
            }
            next_prompt = "Game over! Type 'restart' for a new game."
        elif state.phase == "start":
            next_prompt = "Enter your team name and type START to begin!"
        elif state.phase == "turn":
            next_prompt = f"Turn {state.turn}: Who's playing?"
        elif state.phase == "hutnu":
            next_prompt = "Describe the Hutnu: Zone (0-6)? Safe zone? Any OUT?"
        elif state.phase == "tyak":
            next_prompt = "Tyak attempt? (Y/N) If yes: Zone? Taps? OUT?"
        
        return chat_text, embedded_json, next_prompt
    
    def _get_fallback_response(
        self, 
        state: GameState, 
        parsed: ParsedInput,
        score_breakdown: Optional[ScoreBreakdown]
    ) -> str:
        """Generate fallback response if LLM fails."""
        if state.phase == "start":
            return f"Welcome! Let's play Dandi Biyo! Enter your team name and say START."
        elif state.phase == "turn":
            return f"Turn {state.turn} - Who's batting? Tell me the player's name."
        elif state.phase == "hutnu":
            if score_breakdown:
                return f"Hutnu score: {score_breakdown.hutnu_score}. Tyak attempt? (Y/N)"
            return "Tell me about the Hutnu - which zone (0-6) and safe zone reached?"
        elif state.phase == "tyak":
            if score_breakdown:
                return f"Turn complete! Score: {score_breakdown.turn_score}. Total: {state.total_score}. Next turn?"
            return "Tyak result? Zone and number of taps, or 'no tyak' to skip."
        elif state.phase == "end":
            return f"Game over! {state.team} scored {state.total_score} in {state.turn-1} turns. Ramro khel!"
        return "Hajur? I didn't catch that. Could you rephrase?"
    
    # =========================================================================
    # MAIN CHAT PROCESSING
    # =========================================================================
    
    def process_message(self, request: ChatRequest) -> ChatResponse:
        """
        Main entry point for processing chat messages.
        Handles the complete flow: parse → calculate → respond → update state.
        """
        state = self.get_or_create_session(request.session_id)
        state.add_message("user", request.message)
        
        # Parse user input
        parsed = self.parse_user_input(request.message, state)
        logger.info(f"[{request.session_id}] Parsed: {parsed.intent} (confidence: {parsed.confidence})")
        
        score_breakdown = None
        
        # Handle different intents
        if parsed.intent == "start":
            return self._handle_start(state, parsed, request.message)
        
        elif parsed.intent == "reset":
            state = self.reset_session(request.session_id)
            chat_text = "Huncha! Game reset. Enter team name and START when ready!"
            state.add_message("assistant", chat_text)
            return ChatResponse(
                chat_text=chat_text,
                state=state,
                next_prompt="Enter team name and START",
                valid=True
            )
        
        elif parsed.intent == "end":
            return self._handle_end(state)
        
        elif parsed.intent == "turn":
            return self._handle_turn(state, parsed, request.message)
        
        elif parsed.intent == "hutnu":
            return self._handle_hutnu(state, parsed, request.message)
        
        elif parsed.intent == "tyak":
            return self._handle_tyak(state, parsed, request.message)
        
        elif parsed.intent == "query":
            return self._handle_query(state, request.message)
        
        else:
            # Unknown intent - ask LLM for clarification
            chat_text, embedded_json, next_prompt = self.generate_response(
                request.message, state, parsed
            )
            state.add_message("assistant", chat_text)
            return ChatResponse(
                chat_text=chat_text,
                embedded_json=embedded_json,
                state=state,
                next_prompt=next_prompt or "Could you clarify what happened?",
                valid=True
            )
    
    def _handle_start(self, state: GameState, parsed: ParsedInput, message: str) -> ChatResponse:
        """Handle game start."""
        if parsed.team_name:
            state.team = parsed.team_name
            state.phase = "turn"
            state.time_left = 30.0
            state.total_score = 0
            state.turn = 1
            chat_text = f"Ramro! Team {state.team} is ready! 30 minutes on the clock. Turn 1 - who's batting first?"
        else:
            chat_text = "Let's go! What's your team name? (e.g., 'Team Tigers, START')"
        
        state.add_message("assistant", chat_text)
        return ChatResponse(
            chat_text=chat_text,
            state=state,
            next_prompt=f"Turn {state.turn}: Player name?" if state.phase == "turn" else "Enter team name and START",
            valid=True
        )
    
    def _handle_turn(self, state: GameState, parsed: ParsedInput, message: str) -> ChatResponse:
        """Handle turn start with player name."""
        if parsed.player_name:
            state.current_player = parsed.player_name
            if parsed.player_name not in state.players:
                state.players.append(parsed.player_name)
            state.start_new_turn()
            state.phase = "hutnu"
            chat_text = f"Alright {state.current_player}, show us what you've got! Was there an OUT during Hutnu, or did it land safely?"
        else:
            chat_text = "Who's batting this turn? Just tell me the player's name."
        
        state.add_message("assistant", chat_text)
        return ChatResponse(
            chat_text=chat_text,
            state=state,
            next_prompt="Describe the Hutnu result: Zone? Safe? OUT?",
            valid=True
        )
    
    def _handle_hutnu(self, state: GameState, parsed: ParsedInput, message: str) -> ChatResponse:
        """
        Handle Hutnu phase with proper flow:
        1. Check if OUT
        2. If not OUT, ask for landing zone (if not provided)
        3. Then ask for safe zone reached (if not provided)
        4. Calculate Hutnu score and move to Tyak phase
        """
        if not state.turn_data:
            state.turn_data = TurnEvent(player=state.current_player or "")
        
        player_name = state.current_player or "Player"
        msg_lower = message.lower().strip()
        
        # Get existing hutnu data (from previous message in same phase)
        existing_hutnu = state.turn_data.hutnu
        
        # CASE 1: Check for OUT first
        out_keywords = ["out", "caught", "returned", "missed", "hit dandi", "boundary"]
        is_out = any(kw in msg_lower for kw in out_keywords) and "not out" not in msg_lower and "no out" not in msg_lower and "not" not in msg_lower
        
        if is_out:
            state.turn_data.hutnu = HutneEvent(zone=0, safe=SafeZone.NONE, out=True)
            state.complete_turn()
            
            summary = f"❌ {player_name} is OUT!\n"
            summary += f"Turn Score: 0 points\n"
            summary += f"Total Score: {state.total_score} points | Time: {state.time_left:.0f} min"
            
            if state.is_game_over():
                summary += "\n\n⏱️ Time's up! Game Over!"
                state.add_message("assistant", summary)
                return self._handle_end(state)
            
            summary += f"\n\nTurn {state.turn}: Who's batting next?"
            state.add_message("assistant", summary)
            
            return ChatResponse(
                chat_text=summary,
                embedded_json={"type": "turn_summary", "data": {"hutnu_score": 0, "tyak_score": 0, "turn_score": 0, "is_out": True}},
                state=state,
                next_prompt=f"Turn {state.turn}: Who's batting?",
                valid=True
            )
        
        # CASE 2: Not OUT - extract zone and safe zone info
        current_zone = existing_hutnu.zone if existing_hutnu.zone > 0 else 0
        current_safe = existing_hutnu.safe if existing_hutnu.safe != SafeZone.NONE else SafeZone.NONE
        
        # Try to extract zone from current message
        zone_match = re.search(r'zone\s*(\d+)', msg_lower) or re.search(r'(\d)\s*zone', msg_lower)
        if zone_match:
            current_zone = min(int(zone_match.group(1)), 6)
        elif current_zone == 0:
            # Try standalone number (1-6)
            number_match = re.search(r'\b([1-6])\b', msg_lower)
            if number_match:
                current_zone = int(number_match.group(1))
        
        # Try to extract safe zone from current message
        if current_safe == SafeZone.NONE:
            if any(word in msg_lower for word in ["furthest", "far", "third", "safe 3", "3rd", "farthest"]):
                current_safe = SafeZone.FURTHEST
            elif any(word in msg_lower for word in ["middle", "second", "safe 2", "2nd", "mid"]):
                current_safe = SafeZone.MIDDLE
            elif any(word in msg_lower for word in ["nearest", "near", "first", "safe 1", "1st"]):
                current_safe = SafeZone.NEAREST
        
        # CASE 2a: No zone yet - ask for landing zone
        if current_zone == 0:
            chat_text = f"Ramro! {player_name} hit the Biyo! Which zone did it land in? (1-6)"
            state.add_message("assistant", chat_text)
            return ChatResponse(
                chat_text=chat_text,
                embedded_json=None,
                state=state,
                next_prompt="Landing zone? (1-6)",
                valid=True
            )
        
        # CASE 2b: Have zone but no safe zone - store zone and ask for safe zone
        if current_zone > 0 and current_safe == SafeZone.NONE:
            # Store the zone
            state.turn_data.hutnu = HutneEvent(zone=current_zone, safe=SafeZone.NONE, out=False)
            
            chat_text = (
                f"Zone {current_zone}! Now, which safe zone did {player_name} reach?\n\n"
                f"• Nearest (Safe Zone 1) → 2 points\n"
                f"• Middle (Safe Zone 2) → 4 points\n"
                f"• Furthest (Safe Zone 3) → 6 points\n"
                f"• None → 0 points"
            )
            state.add_message("assistant", chat_text)
            return ChatResponse(
                chat_text=chat_text,
                embedded_json=None,
                state=state,
                next_prompt="Safe zone reached? (nearest/middle/furthest/none)",
                valid=True
            )
        
        # CASE 2c: Have both zone and safe - calculate score and move to Tyak
        if current_zone > 0:
            # Store complete hutnu data
            state.turn_data.hutnu = HutneEvent(zone=current_zone, safe=current_safe, out=False)
            
            # Calculate safe zone points
            safe_points = {"nearest": 2, "middle": 4, "furthest": 6, "none": 0}.get(current_safe.value, 0)
            hutnu_score = current_zone + safe_points
            
            # Move to Tyak phase
            state.phase = "tyak"
            
            chat_text = (
                f"🎯 Hutnu Score for {player_name}:\n"
                f"• Landing Zone: {current_zone} points\n"
                f"• Safe Zone ({current_safe.value.capitalize()}): {safe_points} points\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"• Hutnu Total: {current_zone} + {safe_points} = {hutnu_score} points\n\n"
                f"Would you like to attempt Tyak? (Yes/No)"
            )
            state.add_message("assistant", chat_text)
            
            return ChatResponse(
                chat_text=chat_text,
                embedded_json={"type": "hutnu_score", "data": {"zone": current_zone, "safe": current_safe.value, "safe_points": safe_points, "hutnu_score": hutnu_score}},
                state=state,
                next_prompt="Tyak attempt? (Yes/No)",
                valid=True
            )
        
        # Fallback - ask for zone
        chat_text = f"Was {player_name} OUT? If not, which zone (1-6) did the Biyo land in?"
        state.add_message("assistant", chat_text)
        return ChatResponse(
            chat_text=chat_text,
            embedded_json=None,
            state=state,
            next_prompt="OUT or Zone (1-6)?",
            valid=True
        )
    
    def _handle_tyak(self, state: GameState, parsed: ParsedInput, message: str) -> ChatResponse:
        """
        Handle Tyak phase with proper flow:
        1. Ask Y/N for Tyak attempt
        2. If Yes without zone, ask for zone
        3. Calculate score and show turn summary
        4. Then rotate to next player
        """
        if not state.turn_data:
            state.turn_data = TurnEvent()
        
        # CASE 1: User declined Tyak
        if parsed.tyak and not parsed.tyak.attempted:
            state.turn_data.tyak = TyakEvent(attempted=False, zone=0, taps=0, out=False)
            
            # Calculate final score (Hutnu only)
            breakdown = self.calculate_score(state.turn_data, state.time_left)
            turn_score = state.complete_turn()
            
            player_name = state.current_player or "Player"
            
            # Generate turn summary
            summary = f"━━━ TURN SUMMARY ({player_name}) ━━━\n"
            summary += f"• Hutnu: {breakdown.hutnu_score} points\n"
            summary += f"• Tyak: Not attempted (0 points)\n"
            summary += f"• Turn Total: {breakdown.turn_score} points\n"
            summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            summary += f"Team Total: {state.total_score} points | Time: {state.time_left:.0f} min"
            
            if state.is_game_over():
                chat_text = f"Tyak skipped. {summary}\n\n⏱️ Time's up! Game Over!"
                state.add_message("assistant", chat_text)
                return self._handle_end(state)
            
            chat_text = f"Huncha, no Tyak.\n\n{summary}\n\nTurn {state.turn}: Who's batting next?"
            state.add_message("assistant", chat_text)
            state.phase = "turn"
            
            return ChatResponse(
                chat_text=chat_text,
                embedded_json={"type": "turn_summary", "data": breakdown.model_dump()},
                state=state,
                next_prompt=f"Turn {state.turn}: Who's batting?",
                valid=True
            )
        
        # CASE 2: User said "Yes" but didn't provide zone
        if parsed.tyak and parsed.tyak.attempted and parsed.tyak.zone == 0 and not parsed.tyak.out:
            chat_text = "Tyak attempt confirmed! Which zone (1-6) did the Biyo land in?"
            state.add_message("assistant", chat_text)
            # Stay in tyak phase, wait for zone
            return ChatResponse(
                chat_text=chat_text,
                embedded_json=None,
                state=state,
                next_prompt="Tyak zone? (1-6)",
                valid=True
            )
        
        # CASE 3: User provided zone - check for OUT
        if parsed.tyak and parsed.tyak.attempted:
            state.turn_data.tyak = parsed.tyak
            
            if parsed.tyak.out:
                # Tyak OUT - Hutnu preserved, Tyak = 0
                breakdown = self.calculate_score(state.turn_data, state.time_left)
                turn_score = state.complete_turn()
                
                player_name = state.current_player or "Player"
                
                summary = f"━━━ TURN SUMMARY ({player_name}) ━━━\n"
                summary += f"• Hutnu: {breakdown.hutnu_score} points\n"
                summary += f"• Tyak: OUT! (0 points)\n"
                summary += f"• Turn Total: {breakdown.turn_score} points\n"
                summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                summary += f"Team Total: {state.total_score} points | Time: {state.time_left:.0f} min"
                
                if state.is_game_over():
                    chat_text = f"Oho! Tyak OUT!\n\n{summary}\n\n⏱️ Time's up! Game Over!"
                    state.add_message("assistant", chat_text)
                    return self._handle_end(state)
                
                chat_text = f"Oho! Tyak OUT! But Hutnu score is preserved.\n\n{summary}\n\nTurn {state.turn}: Who's batting next?"
                state.add_message("assistant", chat_text)
                state.phase = "turn"
                
                return ChatResponse(
                    chat_text=chat_text,
                    embedded_json={"type": "turn_summary", "data": breakdown.model_dump()},
                    state=state,
                    next_prompt=f"Turn {state.turn}: Who's batting?",
                    valid=True
                )
            
            # CASE 4: Successful Tyak - calculate and show summary
            breakdown = self.calculate_score(state.turn_data, state.time_left)
            turn_score = state.complete_turn()
            logger.info(f"[{state.session_id}] Turn completed: score={turn_score}, total={state.total_score}")
            
            player_name = state.current_player or "Player"
            
            # Detailed turn summary
            summary = f"━━━ TURN SUMMARY ({player_name}) ━━━\n"
            summary += f"• Hutnu: Zone {breakdown.hutnu_zone}"
            if breakdown.hutnu_safe != "none":
                summary += f" + {breakdown.hutnu_safe} ({breakdown.hutnu_safe_points})"
            summary += f" = {breakdown.hutnu_score} points\n"
            summary += f"• Tyak: Zone {breakdown.tyak_zone} × 2 = {breakdown.tyak_score} points\n"
            summary += f"• Turn Total: {breakdown.hutnu_score} + {breakdown.tyak_score} = {breakdown.turn_score} points\n"
            summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            summary += f"Team Total: {state.total_score} points | Time: {state.time_left:.0f} min"
            
            if state.is_game_over():
                chat_text = f"Ramro Tyak!\n\n{summary}\n\n⏱️ Time's up! Game Over!"
                state.add_message("assistant", chat_text)
                return self._handle_end(state)
            
            chat_text = f"Ramro Tyak! Zone {breakdown.tyak_zone} = {breakdown.tyak_score} points!\n\n{summary}\n\nTurn {state.turn}: Who's batting next?"
            state.add_message("assistant", chat_text)
            state.phase = "turn"
            
            return ChatResponse(
                chat_text=chat_text,
                embedded_json={"type": "turn_summary", "data": breakdown.model_dump()},
                state=state,
                next_prompt=f"Turn {state.turn}: Who's batting?",
                valid=True
            )
        
        # Default: Ask about Tyak attempt
        chat_text = "Would you like to attempt Tyak? (Yes/No)"
        state.add_message("assistant", chat_text)
        return ChatResponse(
            chat_text=chat_text,
            embedded_json=None,
            state=state,
            next_prompt="Tyak attempt? (Y/N)",
            valid=True
        )
    
    def _handle_end(self, state: GameState) -> ChatResponse:
        """Handle game end."""
        state.phase = "end"
        summary = GameSummary(
            team=state.team,
            total_turns=state.turn - 1,
            final_score=state.total_score,
            players=state.players,
            game_duration=30.0 - state.time_left,
            average_score_per_turn=state.total_score / max(1, state.turn - 1)
        )
        
        chat_text = f"""
🏏 GAME OVER! 🏏

Team: {state.team}
Final Score: {state.total_score} tyaks
Turns Played: {state.turn - 1}
Average per Turn: {summary.average_score_per_turn:.1f}

Ramro khel, {state.team}! Type 'restart' to play again!
"""
        state.add_message("assistant", chat_text)
        
        return ChatResponse(
            chat_text=chat_text,
            embedded_json={"type": "game_summary", "data": summary.model_dump()},
            state=state,
            next_prompt="Type 'restart' for a new game!",
            valid=True
        )
    
    def _handle_query(self, state: GameState, message: str) -> ChatResponse:
        """Handle queries about rules, score, etc."""
        msg_lower = message.lower()
        
        if "score" in msg_lower:
            chat_text = f"Current score: {state.total_score} tyaks. Turn {state.turn}, {state.time_left:.0f} min left."
        elif "rule" in msg_lower or "how" in msg_lower:
            chat_text = """Quick rules:
• Hutnu: Hit Biyo to zones 0-6 (zone = points). Reach safe zones for bonus (nearest=2, middle=4, furthest=6).
• Tyak: If not OUT, tap Biyo for bonus = 2 × landing zone.
• OUT: Caught, boundary (>6), returned to Khop, or hit Dandi.
• 30 min per team. Highest score wins!"""
        elif "help" in msg_lower:
            chat_text = f"""I'm Dai, your referee! Current phase: {state.phase}.
Commands: 'Team [name], START' | 'restart' | 'score' | 'rules'
Just describe plays naturally and I'll calculate!"""
        else:
            chat_text = f"Hajur? Current: Turn {state.turn}, Score {state.total_score}, {state.time_left:.0f} min. What would you like to know?"
        
        state.add_message("assistant", chat_text)
        return ChatResponse(
            chat_text=chat_text,
            state=state,
            next_prompt="Continue with the game or ask another question!",
            valid=True
        )


# Global instance (initialized in main.py)
chat_referee: Optional[ChatReferee] = None


def get_chat_referee() -> ChatReferee:
    """Get or create the global chat referee instance."""
    global chat_referee
    if chat_referee is None:
        chat_referee = ChatReferee()
    return chat_referee
