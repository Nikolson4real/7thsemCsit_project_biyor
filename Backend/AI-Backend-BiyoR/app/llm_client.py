"""
Gemini LLM client wrapper for BiyoR AI Rules Engine.
Uses Google AI Studio APIs (NOT Vertex AI) for Gemini Flash models.
Includes robust JSON repair and fallback handling.
"""

import json
import re
import time
from typing import Optional, Dict, Any, Tuple, List
import google.generativeai as genai
from loguru import logger

from app.config import settings


class GeminiRulesLLM:
    """
    Wrapper for Google Gemini models via Google AI Studio.
    Handles prompt construction, retries, fallback, and JSON parsing with repair.
    """
    
    def __init__(self):
        """Initialize Gemini client with Google AI Studio API key."""
        # Configure Google AI Studio SDK
        genai.configure(api_key=settings.google_api_key)
        
        # Primary and fallback model names
        self.primary_model_name = settings.gemini_primary_model
        self.fallback_model_name = settings.gemini_fallback_model
        
        # Safety settings - Disable all safety filters for Dandi Biyo rules
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
        
        # Generation configuration
        self.generation_config = {
            "temperature": settings.llm_temperature,
            "max_output_tokens": settings.llm_max_output_tokens,
            "response_mime_type": "application/json",
        }
        
        logger.info(
            f"Initialized GeminiRulesLLM with primary model: {self.primary_model_name}, "
            f"fallback: {self.fallback_model_name}"
        )
    
    def _build_system_prompt(self) -> str:
        """Build the system-level instruction for Gemini."""
        return """You are an expert Dandi Biyo referee and instructor with deep knowledge of the traditional Nepali sport.

Your role:
- Provide accurate, authoritative rules and guidance based ONLY on the official Dandi Biyo rulebooks provided to you.
- NEVER invent or fabricate rules that are not in the retrieved documents.
- Break down complex rules into small, digestible, player-friendly instruction cards.
- Each card should be self-contained and focus on ONE specific rule, action, or decision.
- Use clear, simple language suitable for first-time players and experienced players alike.
- Reference specific rule sections in your responses.
- When rules are ambiguous or not covered in the retrieved documents, explicitly state this.

CRITICAL OUTPUT REQUIREMENTS:
- You MUST respond with valid, complete JSON only.
- No commentary, explanations, or text outside the JSON structure.
- Ensure all strings are properly closed with quotation marks.
- Ensure all arrays and objects are properly closed with ] and }.
- Keep card bodies short (max 2-3 sentences) for AR display readability.
"""
    
    def _build_user_prompt(
        self,
        situation: Dict[str, Any],
        retrieved_chunks: list,
        response_schema: Dict[str, Any]
    ) -> str:
        """Build the user prompt with situation, retrieved rules, and schema."""
        # Format retrieved chunks
        chunks_text = "\n\n".join([
            f"[Chunk {i+1}]\n"
            f"Source: {chunk.get('metadata', {}).get('source', 'Unknown')}\n"
            f"Section: {chunk.get('metadata', {}).get('section', 'N/A')}\n"
            f"Content: {chunk.get('content', '')}"
            for i, chunk in enumerate(retrieved_chunks)
        ])
        
        prompt = f"""# Current Game Situation

{json.dumps(situation, indent=2)}

# Retrieved Dandi Biyo Rule Chunks

{chunks_text if chunks_text else "No relevant rule chunks were retrieved. Respond based on general Dandi Biyo knowledge but note the lack of specific rule references."}

# Your Task

Analyze the game situation above using the retrieved Dandi Biyo rules.

Generate a response that:
1. Breaks the applicable rules and guidance into separate instruction cards
2. Each card should address ONE specific aspect: a rule, an action step, a scoring decision, or a warning
3. Prioritize cards by importance (1 = most critical, 10 = least critical)
4. Include references to the rule sections from the chunks above
5. Provide a brief overall summary of what the player/team should do next

# Required JSON Response Schema

You MUST respond with JSON matching this exact structure:

{json.dumps(response_schema, indent=2)}

# CRITICAL: Output Requirements

- Output ONLY valid, complete JSON - nothing else
- Ensure ALL strings are properly quoted and closed
- Ensure ALL arrays end with ]
- Ensure ALL objects end with }}
- Keep responses concise to avoid truncation
- Maximum 3 cards to ensure complete response

Generate the JSON response now:"""
        return prompt
    
    def _repair_json(self, text: str) -> str:
        """
        Attempt to repair malformed JSON from LLM response.
        
        Args:
            text: Raw text that should be JSON
            
        Returns:
            Repaired JSON string
        """
        if not text:
            return "{}"
        
        original_text = text
        
        # Step 1: Remove markdown code fences
        text = re.sub(r'^```(?:json)?\s*\n?', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n?```\s*$', '', text, flags=re.MULTILINE)
        text = text.strip()
        
        # Step 2: Find the outermost JSON object
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            text = text[first_brace:last_brace + 1]
        elif first_brace != -1:
            # Only opening brace found - try to close it
            text = text[first_brace:]
        
        # Step 3: Fix common JSON issues
        # Replace smart quotes with regular quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Step 4: Fix truncated strings - find unclosed quotes
        in_string = False
        escaped = False
        fixed_chars = []
        
        for i, char in enumerate(text):
            if escaped:
                fixed_chars.append(char)
                escaped = False
                continue
            
            if char == '\\':
                escaped = True
                fixed_chars.append(char)
                continue
            
            if char == '"':
                in_string = not in_string
            
            fixed_chars.append(char)
        
        # If we ended inside a string, close it
        if in_string:
            fixed_chars.append('"')
        
        text = ''.join(fixed_chars)
        
        # Step 5: Try to fix truncated arrays/objects
        # Count brackets and braces
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')
        
        # Close any unclosed structures
        if open_brackets > 0:
            text = text.rstrip(',\n\t ')
            text += ']' * open_brackets
        
        if open_braces > 0:
            text = text.rstrip(',\n\t ')
            text += '}' * open_braces
        
        # Step 6: Remove trailing commas before closing brackets/braces
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        
        # Step 7: Fix missing commas between elements (basic)
        text = re.sub(r'"\s*\n\s*"', '",\n"', text)
        text = re.sub(r'}\s*\n\s*{', '},\n{', text)
        text = re.sub(r']\s*\n\s*"', '],\n"', text)
        
        logger.debug(f"JSON repair: {len(original_text)} -> {len(text)} chars")
        
        return text
    
    def _create_fallback_response(self, raw_text: str) -> Dict[str, Any]:
        """
        Create a valid fallback response when JSON parsing completely fails.
        
        Args:
            raw_text: The raw text from the model
            
        Returns:
            A valid response dictionary
        """
        # Clean up the text for display
        clean_text = raw_text.strip() if raw_text else ""
        
        # Remove any partial JSON artifacts
        clean_text = re.sub(r'[{}\[\]":]', ' ', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # Ensure we have meaningful content
        if len(clean_text) < 50:
            clean_text = (
                "Unable to retrieve specific rules for this situation. "
                "Please consult the official Dandi Biyo rulebook or ask a more specific question. "
                "The game involves striking the Biyo (small wooden piece) with the Dandi (larger stick) "
                "and scoring is based on the distance the Biyo travels."
            )
        
        # Truncate if too long
        if len(clean_text) > 500:
            clean_text = clean_text[:497] + "..."
        
        return {
            "cards": [
                {
                    "id": "fallback_1",
                    "title": "Dandi Biyo Rules Information",
                    "type": "INSTRUCTION",
                    "priority": 1,
                    "body": clean_text,
                    "related_rule_refs": [],
                    "suggested_ar_visual": None
                }
            ],
            "overall_summary": "Here is the available information about Dandi Biyo rules for your situation.",
            "game_state_update": None
        }
    
    def _normalize_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize the response to match expected schema.
        Handles variations in field names from different model responses.
        
        Args:
            result: Parsed JSON dictionary
            
        Returns:
            Normalized dictionary with expected field names
        """
        normalized = {}
        
        # Handle cards array - check various possible field names
        cards = (
            result.get("cards") or 
            result.get("instruction_cards") or 
            result.get("rules_cards") or 
            result.get("response_cards") or
            []
        )
        
        # Normalize each card
        normalized_cards = []
        for card in cards:
            if isinstance(card, dict):
                normalized_card = {
                    "id": card.get("id", card.get("card_id", f"card_{len(normalized_cards)+1}")),
                    "type": card.get("type", card.get("card_type", "INSTRUCTION")),
                    "title": card.get("title", card.get("card_title", "Rule Information")),
                    "body": card.get("body", card.get("content", card.get("description", card.get("text", "")))),
                    "priority": card.get("priority", card.get("importance", 1)),
                    "related_rule_refs": card.get("related_rule_refs", card.get("source_references", card.get("sources", card.get("references", [])))),
                    "suggested_ar_visual": card.get("suggested_ar_visual", card.get("ar_visual", None))
                }
                # Ensure related_rule_refs is a list
                if not isinstance(normalized_card["related_rule_refs"], list):
                    normalized_card["related_rule_refs"] = [str(normalized_card["related_rule_refs"])] if normalized_card["related_rule_refs"] else []
                
                normalized_cards.append(normalized_card)
        
        normalized["cards"] = normalized_cards
        
        # Handle overall_summary - check various possible field names
        normalized["overall_summary"] = str(
            result.get("overall_summary") or
            result.get("reasoning_summary") or
            result.get("summary") or
            result.get("response_summary") or
            result.get("ruling_summary") or
            result.get("conclusion") or
            result.get("answer") or
            ""
        )
        
        # Handle game_state_update
        normalized["game_state_update"] = (
            result.get("game_state_update") or
            result.get("state_update") or
            result.get("game_update") or
            None
        )
        
        return normalized

    def _parse_json_response(self, raw_response: str, model_name: str) -> Dict[str, Any]:
        """
        Parse raw LLM text into JSON with multiple repair attempts.
        
        Args:
            raw_response: Raw text from the model
            model_name: Name of the model for logging
            
        Returns:
            Parsed JSON dictionary (normalized to expected schema)
        """
        if not raw_response:
            logger.warning(f"Empty response from {model_name}")
            return self._create_fallback_response("")
        
        # Attempt 1: Direct parse
        try:
            result = json.loads(raw_response)
            if self._is_valid_response(result):
                return self._normalize_response(result)
            logger.warning("Parsed JSON but missing required content, attempting repair...")
        except json.JSONDecodeError as e:
            logger.debug(f"Direct JSON parse failed: {e}")
        
        # Attempt 2: Parse after repair
        repaired = self._repair_json(raw_response)
        try:
            result = json.loads(repaired)
            if self._is_valid_response(result):
                logger.info(f"JSON repair successful for {model_name}")
                return self._normalize_response(result)
            logger.warning("Repaired JSON but missing required content")
        except json.JSONDecodeError as e:
            logger.warning(f"JSON repair failed: {e}")
        
        # Attempt 3: Extract any valid JSON object using regex
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, raw_response, re.DOTALL)
        
        for match in matches:
            try:
                result = json.loads(match)
                if isinstance(result, dict) and self._is_valid_response(result):
                    logger.info(f"Extracted valid JSON object from {model_name} response")
                    return self._normalize_response(result)
            except json.JSONDecodeError:
                continue
        
        # Attempt 4: Create fallback response
        logger.warning(f"All JSON parsing attempts failed for {model_name}, using fallback")
        return self._create_fallback_response(raw_response)
    
    def _is_valid_response(self, result: Dict[str, Any]) -> bool:
        """
        Check if parsed response has required fields with valid content.
        Uses normalization to handle different field name variations.
        
        Args:
            result: Parsed JSON dictionary
            
        Returns:
            True if response meets minimum requirements
        """
        if not isinstance(result, dict):
            return False
        
        # Normalize first to check with expected field names
        normalized = self._normalize_response(result)
        
        # Check cards array
        cards = normalized.get("cards", [])
        if not cards or not isinstance(cards, list) or len(cards) == 0:
            return False
        
        # Check at least one card has content
        has_valid_card = False
        for card in cards:
            if isinstance(card, dict):
                body = card.get("body", "")
                if body and len(str(body)) > 10:
                    has_valid_card = True
                    break
        
        if not has_valid_card:
            return False
        
        # Check overall_summary has minimum length (20 chars required by schema)
        summary = normalized.get("overall_summary", "")
        if not summary or len(str(summary)) < 20:
            return False
        
        return True
    
    def _call_gemini_once(
        self,
        model_name: str,
        system_prompt: str,
        user_prompt: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Make a single API call to Gemini.
        
        Args:
            model_name: Name of the Gemini model to use
            system_prompt: System-level instructions
            user_prompt: User prompt with situation and retrieved chunks
        
        Returns:
            Tuple of (response_text, error_message)
            If successful, error_message is None
            If failed, response_text is None
        """
        try:
            logger.info(f"Calling Gemini model: {model_name}")
            
            # Initialize the model with safety settings
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings,
                system_instruction=system_prompt
            )
            
            # Generate response
            response = model.generate_content(user_prompt)
            
            # Check if response was blocked
            if not response.candidates:
                return None, "Response was blocked - no candidates returned"
            
            # Extract text from response
            try:
                if hasattr(response, 'text'):
                    result = response.text
                elif hasattr(response, 'parts'):
                    result = "".join(part.text for part in response.parts)
                else:
                    return None, "Unexpected response structure from Gemini"
                
                logger.info(f"Successfully received response from {model_name}")
                return result, None
                
            except ValueError:
                # Response was blocked, check finish_reason
                finish_reason = response.candidates[0].finish_reason if response.candidates else None
                return None, f"Response blocked with finish_reason: {finish_reason}"
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error calling Gemini model {model_name}: {error_msg}")
            return None, error_msg
    
    def _call_gemini_with_retry(
        self,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 2
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Call Gemini with retry logic, but skip retries for quota/404 errors.
        
        Returns:
            Tuple of (response_text, error_message)
        """
        last_error = None
        
        for attempt in range(max_retries):
            response_text, error = self._call_gemini_once(model_name, system_prompt, user_prompt)
            
            if response_text is not None:
                return response_text, None
            
            last_error = error
            
            # Don't retry on quota errors or model not found
            if error and ("429" in error or "404" in error or "quota" in error.lower()):
                logger.warning(f"Quota/404 error for {model_name}, skipping retries")
                break
            
            # Don't retry on the last attempt
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retrying {model_name} in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
        
        return None, last_error
    
    def generate_rules_response(
        self,
        situation: Dict[str, Any],
        retrieved_chunks: list,
        response_schema: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], str]:
        """
        Generate a rules response using Gemini with retrieved context.
        
        Args:
            situation: The game situation from the API request
            retrieved_chunks: List of retrieved rule chunks from FAISS
            response_schema: JSON schema for the expected response
        
        Returns:
            Tuple of (parsed_response_dict, model_name_used)
        
        Raises:
            Exception: If all attempts fail
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(situation, retrieved_chunks, response_schema)
        
        errors: Dict[str, str] = {}
        models_to_try = [self.primary_model_name, self.fallback_model_name]
        
        for model_name in models_to_try:
            if not model_name:
                continue
            
            # Try to get response from model
            response_text, error = self._call_gemini_with_retry(
                model_name, system_prompt, user_prompt, max_retries=2
            )
            
            if error:
                errors[model_name] = error
                logger.warning(f"Model {model_name} failed: {error}")
                continue
            
            # Try to parse the response
            try:
                parsed_response = self._parse_json_response(response_text, model_name)
                logger.info(f"Successfully generated response using {model_name}")
                return parsed_response, model_name
            except Exception as parse_error:
                errors[model_name] = f"Parse error: {str(parse_error)}"
                logger.warning(f"Failed to parse response from {model_name}: {parse_error}")
                continue
        
        # All models failed
        error_summary = " | ".join([f"{k}: {v}" for k, v in errors.items()])
        raise Exception(f"All configured models failed. Details: {error_summary}")
    
    async def agenerate_rules_response(
        self,
        situation: Dict[str, Any],
        retrieved_chunks: list,
        response_schema: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], str]:
        """Async version of generate_rules_response."""
        # For now, run synchronous version
        # TODO: Replace with native async when Google SDK supports it
        return self.generate_rules_response(situation, retrieved_chunks, response_schema)
    
    def generate_structured_response(
        self,
        prompt: str,
        response_schema: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate a structured JSON response from a prompt.
        
        This is a simpler interface for generating responses without 
        needing to construct situation/chunks separately.
        
        Args:
            prompt: Full prompt including context and instructions
            response_schema: Optional JSON schema for the expected response
        
        Returns:
            Parsed JSON response dict
        
        Raises:
            Exception: If generation fails
        """
        system_prompt = """You are an expert Dandi Biyo rules referee. 
Your responses must be valid JSON only. Do not include any markdown formatting or code blocks.
Provide accurate, helpful information based on the rules context provided."""

        errors: Dict[str, str] = {}
        models_to_try = [self.primary_model_name, self.fallback_model_name]
        
        for model_name in models_to_try:
            if not model_name:
                continue
            
            # Try to get response from model
            response_text, error = self._call_gemini_with_retry(
                model_name, system_prompt, prompt, max_retries=2
            )
            
            if error:
                errors[model_name] = error
                logger.warning(f"Model {model_name} failed: {error}")
                continue
            
            # Try to parse the response
            try:
                parsed_response = self._parse_json_response(response_text, model_name)
                logger.info(f"Successfully generated structured response using {model_name}")
                return parsed_response
            except Exception as parse_error:
                errors[model_name] = f"Parse error: {str(parse_error)}"
                logger.warning(f"Failed to parse response from {model_name}: {parse_error}")
                continue
        
        # All models failed - create fallback response
        error_summary = "; ".join([f"{k}: {v}" for k, v in errors.items()])
        logger.error(f"All models failed for structured response: {error_summary}")
        return self._create_fallback_response(f"Error generating response: {error_summary}")
    
    def generate_raw_json_response(
        self,
        prompt: str,
        response_schema: Dict[str, Any] = None,
        pdf_path: Optional[str] = None,
        game_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a raw JSON response from a prompt WITHOUT normalization.
        
        Unlike generate_structured_response, this method returns the parsed JSON
        exactly as the LLM generated it, without normalizing field names.
        Use this when you need the exact JSON structure from the LLM.
        
        If all LLM models fail (e.g., rate limited), falls back to PDF-based
        rule generation without LLM.
        
        Args:
            prompt: Full prompt including context and instructions
            response_schema: Optional JSON schema for the expected response
            pdf_path: Path to rulebook PDF (for fallback generation)
            game_config: Game configuration dict (for fallback generation)
        
        Returns:
            Raw parsed JSON response dict (no normalization)
        
        Raises:
            Exception: If generation fails
        """
        system_prompt = """You are an expert Dandi Biyo rules referee. 
Your responses must be valid JSON only. Do not include any markdown formatting or code blocks.
Provide accurate, helpful information based on the rules context provided."""

        errors: Dict[str, str] = {}
        models_to_try = [self.primary_model_name, self.fallback_model_name]
        
        for model_name in models_to_try:
            if not model_name:
                continue
            
            # Try to get response from model
            response_text, error = self._call_gemini_with_retry(
                model_name, system_prompt, prompt, max_retries=2
            )
            
            if error:
                errors[model_name] = error
                logger.warning(f"Model {model_name} failed: {error}")
                continue
            
            # Try to parse the response (raw JSON, no normalization)
            try:
                # Basic JSON repair without normalization
                repaired = self._repair_json(response_text)
                parsed_response = json.loads(repaired)
                logger.info(f"Successfully generated raw JSON response using {model_name}")
                return parsed_response
            except json.JSONDecodeError as e:
                errors[model_name] = f"JSON parse error: {str(e)}"
                logger.warning(f"Failed to parse raw JSON from {model_name}: {e}")
                continue
        
        # All models failed - use PDF fallback for any error
        error_summary = "; ".join([f"{k}: {v}" for k, v in errors.items()])
        logger.error(f"All models failed for raw JSON response: {error_summary}")
        
        # Fallback to PDF-based rule generation (works for any LLM failure)
        if pdf_path:
            logger.warning(f"LLM failed - using PDF fallback to generate rules. Error: {error_summary[:100]}")
            try:
                from app.pdf_rules_parser import get_fallback_rules
                fallback_response = get_fallback_rules(
                    pdf_path=pdf_path,
                    game_config=game_config,
                    num_cards=10
                )
                logger.info(f"Fallback generated {len(fallback_response.get('rules_cards', []))} rule cards from PDF")
                return fallback_response
            except Exception as fallback_error:
                logger.error(f"PDF fallback also failed: {fallback_error}")
        
        return {
            "rules_cards": [],
            "game_summary": "Unable to generate rules. Please try again."
        }
    
    def test_connection(self) -> bool:
        """
        Test the connection to Google AI Studio API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            model = genai.GenerativeModel(
                model_name=self.primary_model_name,
                safety_settings=self.safety_settings
            )
            response = model.generate_content("Reply with exactly: OK")
            _ = response.text
            logger.info("Google AI Studio API connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Google AI Studio API connection test failed: {str(e)}")
            return False
