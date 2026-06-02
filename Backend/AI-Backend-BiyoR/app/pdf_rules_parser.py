"""
PDF Rules Parser Module
-----------------------
Extracts text from the Dandi Biyo rulebook PDF and generates structured rule cards
without requiring LLM calls. Used as a fallback when API rate limits are hit.
"""

import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class DandiBiyoPDFParser:
    """Parse Dandi Biyo rulebook PDF and generate structured rule cards."""
    
    # Rule card templates with detailed AR-optimized content
    # Designed for mobile AR card display - clear, concise, actionable
    RULE_TEMPLATES = {
        "objective": {
            "keywords": ["objective", "goal", "aim", "propel", "far"],
            "default_card": {
                "card_id": "rule_001",
                "category": "objective",
                "title": "Game Objective",
                "body": "Strike the Biyo (wooden peg) with your Dandi (stick) and launch it as FAR as possible! Distance = Points. Farthest thrower wins!",
                "priority": 1,
                "icon_hint": "target",
                "ar_highlight": "field_center"
            }
        },
        "equipment": {
            "keywords": ["dandi", "biyo", "stick", "peg", "cm", "length", "diameter"],
            "default_card": {
                "card_id": "rule_002",
                "category": "equipment",
                "title": "Equipment",
                "body": "DANDI: 45-60cm hardwood stick (your bat). BIYO: 10-15cm tapered wooden peg (the projectile). Both ends of Biyo are pointed for easy flipping.",
                "priority": 2,
                "icon_hint": "ruler",
                "ar_highlight": "equipment_area"
            }
        },
        "setup": {
            "keywords": ["field", "khop", "hole", "dimension", "oval", "rectangular"],
            "default_card": {
                "card_id": "rule_003",
                "category": "setup",
                "title": "Field Setup",
                "body": "Field: 40m × 50m open area. Dig a small hole called 'KHOP' (fits the Biyo) about 5m from one end. This is your striking zone!",
                "priority": 3,
                "icon_hint": "flag",
                "ar_highlight": "boundary_lines"
            }
        },
        "gameplay": {
            "keywords": ["hutne", "hit", "strike", "placed", "hole"],
            "default_card": {
                "card_id": "rule_004",
                "category": "gameplay",
                "title": "How to Hit (Hutne)",
                "body": "Step 1: Place Biyo in the Khop (hole). Step 2: Strike the Biyo's tip to FLIP it into the air. Step 3: SMASH it mid-air to send it flying!",
                "priority": 4,
                "icon_hint": "info",
                "ar_highlight": "field_center"
            }
        },
        "turns": {
            "keywords": ["turn", "inning", "rotation", "team", "player"],
            "default_card": {
                "card_id": "rule_005",
                "category": "turns",
                "title": "Turn Order",
                "body": "Players take turns batting. Each turn: attempt to hit the Biyo. If successful, you can continue with TYAK (bonus taps). Miss or get OUT = next player's turn.",
                "priority": 5,
                "icon_hint": "player",
                "ar_highlight": "player_position"
            }
        },
        "scoring": {
            "keywords": ["tyak", "score", "point", "distance", "measure"],
            "default_card": {
                "card_id": "rule_006",
                "category": "scoring",
                "title": "Scoring (Tyaks)",
                "body": "Measure distance from Khop to where Biyo lands. 1 Dandi length = 1 TYAK (point). BONUS: After landing, tap Biyo upward repeatedly for extra tyaks!",
                "priority": 6,
                "icon_hint": "score",
                "ar_highlight": "scoring_zones"
            }
        },
        "defending": {
            "keywords": ["catch", "defend", "fielder", "return", "throw"],
            "default_card": {
                "card_id": "rule_007",
                "category": "defending",
                "title": "Defending",
                "body": "Fielders stand 20-25m away. CATCH the Biyo mid-air = Batter OUT! Or pick up landed Biyo and THROW it to hit the Dandi on the Khop = Batter OUT!",
                "priority": 7,
                "icon_hint": "player",
                "ar_highlight": "field_center"
            }
        },
        "foul": {
            "keywords": ["out", "foul", "violation", "boundary", "zero"],
            "default_card": {
                "card_id": "rule_008",
                "category": "foul",
                "title": "Out Conditions",
                "body": "You're OUT if: (1) Biyo caught mid-air, (2) Thrown Biyo hits your Dandi, (3) Zero tyaks scored, (4) Biyo lands outside boundary, (5) Miss 3 times.",
                "priority": 8,
                "icon_hint": "warning",
                "ar_highlight": None
            }
        },
        "winning": {
            "keywords": ["win", "victory", "target", "end", "final"],
            "default_card": {
                "card_id": "rule_009",
                "category": "winning",
                "title": "Winning",
                "body": "Set a target score before starting (e.g., 100, 200, or 500 tyaks). First player/team to reach the target WINS! Alternatively, highest score after set innings.",
                "priority": 9,
                "icon_hint": "target",
                "ar_highlight": None
            }
        },
        "safety": {
            "keywords": ["safety", "helmet", "distance", "spectator", "mandatory"],
            "default_card": {
                "card_id": "rule_010",
                "category": "safety",
                "title": "Safety First",
                "body": "HELMETS are mandatory for batters. Fielders stay 4m+ from batter. Spectators behind boundary only. Shout 'BIYO!' before hitting to alert others!",
                "priority": 10,
                "icon_hint": "warning",
                "ar_highlight": "player_position"
            }
        }
    }
    
    def __init__(self, pdf_path: Optional[str] = None):
        """
        Initialize the parser.
        
        Args:
            pdf_path: Path to the Dandi Biyo rulebook PDF
        """
        self.pdf_path = pdf_path
        self.pdf_text: str = ""
        self.parsed_sections: Dict[str, str] = {}
    
    def load_pdf(self, pdf_path: Optional[str] = None) -> str:
        """
        Load and extract text from the PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        path = pdf_path or self.pdf_path
        if not path:
            logger.warning("No PDF path provided")
            return ""
        
        try:
            from langchain_community.document_loaders import PyPDFLoader
            
            pdf_file = Path(path)
            if not pdf_file.exists():
                logger.error(f"PDF file not found: {path}")
                return ""
            
            loader = PyPDFLoader(str(pdf_file))
            pages = loader.load()
            
            self.pdf_text = "\n\n".join([page.page_content for page in pages])
            logger.info(f"Loaded PDF: {len(pages)} pages, {len(self.pdf_text)} characters")
            
            return self.pdf_text
            
        except Exception as e:
            logger.error(f"Error loading PDF: {e}")
            return ""
    
    def extract_rules_by_keyword(self, text: str, keywords: List[str], max_length: int = 150) -> Optional[str]:
        """
        Extract rule text from PDF content based on keywords.
        
        Args:
            text: Full PDF text
            keywords: Keywords to search for
            max_length: Maximum length of extracted text
            
        Returns:
            Extracted and cleaned rule text, or None if not found
        """
        text_lower = text.lower()
        
        for keyword in keywords:
            # Find sentences containing the keyword
            pattern = rf'[^.!?]*{re.escape(keyword)}[^.!?]*[.!?]'
            matches = re.findall(pattern, text_lower)
            
            if matches:
                # Get the most relevant match (first one usually)
                match = matches[0].strip()
                # Clean and truncate
                if len(match) > max_length:
                    match = match[:max_length-3] + "..."
                return match.capitalize()
        
        return None
    
    def generate_rule_cards(
        self,
        game_config: Optional[Dict[str, Any]] = None,
        num_cards: int = 7
    ) -> Dict[str, Any]:
        """
        Generate structured rule cards from PDF content.
        
        This is the main fallback method used when LLM is rate-limited.
        
        Args:
            game_config: Optional game configuration (equipment, field, players)
            num_cards: Number of cards to generate (default 7)
            
        Returns:
            Dict containing rules_cards and game_summary
        """
        rules_cards: List[Dict[str, Any]] = []
        
        # Load PDF if text not already loaded
        if not self.pdf_text and self.pdf_path:
            self.load_pdf()
        
        # Generate cards from templates, potentially enriched with PDF content
        categories_to_use = ["objective", "equipment", "setup", "gameplay", "turns", "scoring", "defending", "foul", "winning", "safety"]
        categories_to_use = categories_to_use[:num_cards]
        
        for i, category in enumerate(categories_to_use):
            template_info = self.RULE_TEMPLATES.get(category)
            if not template_info:
                continue
            
            card = template_info["default_card"].copy()
            card["card_id"] = f"rule_{i+1:03d}"
            card["priority"] = i + 1
            
            # Keep the well-crafted default body - only override if PDF has BETTER content
            # (longer, more complete sentences that improve on the default)
            if self.pdf_text:
                extracted = self.extract_rules_by_keyword(
                    self.pdf_text,
                    template_info["keywords"]
                )
                # Only use extracted content if it's substantial and well-formed
                # Skip if: too short, starts with list markers, contains raw formatting
                if (extracted and 
                    len(extracted) > 80 and 
                    not extracted.startswith("-") and
                    not extracted.startswith("1") and
                    not extracted.startswith("2") and
                    not extracted.startswith("3") and
                    not extracted.startswith("4") and
                    not extracted.endswith("1.") and
                    not extracted.endswith("2.") and
                    "\n-" not in extracted and
                    "rulebook" not in extracted.lower() and
                    "rag-friendly" not in extracted.lower()):
                    card["body"] = extracted
            
            # Adapt equipment rules if config provided
            if game_config and category == "equipment":
                equip = game_config.get("equipment_dimensions", {})
                if equip:
                    dandi_len = equip.get("dandi_length_cm", 60)
                    biyo_len = equip.get("biyo_length_cm", 10)
                    card["body"] = f"Dandi ({dandi_len}cm stick) and Biyo ({biyo_len}cm peg). Place Biyo on raised surface to start."
            
            # Adapt field rules if config provided
            if game_config and category == "setup":
                field = game_config.get("ground_description", {})
                if field:
                    surface = field.get("surface_type", "grass")
                    if hasattr(surface, "value"):
                        surface = surface.value
                    length = field.get("field_length_m", "open")
                    card["body"] = f"Playing on {surface} surface. Mark striking circle (1m). Field extends {length}m for distance."
            
            rules_cards.append(card)
        
        # Generate game summary
        game_summary = self._generate_summary(game_config)
        
        return {
            "rules_cards": rules_cards,
            "game_summary": game_summary
        }
    
    def _generate_summary(self, game_config: Optional[Dict[str, Any]] = None) -> str:
        """Generate a brief game summary."""
        base_summary = "Dandi Biyo is a traditional Nepali stick-and-peg game. Hit the Biyo with your Dandi to launch it far and score points (tyaks). Defend by catching or returning the Biyo!"
        
        if game_config:
            players = game_config.get("num_players_available")
            if players:
                base_summary += f" Ready for {players} players."
        
        return base_summary


# Singleton instance for reuse
_parser_instance: Optional[DandiBiyoPDFParser] = None


def get_fallback_rules(
    pdf_path: str,
    game_config: Optional[Dict[str, Any]] = None,
    num_cards: int = 7
) -> Dict[str, Any]:
    """
    Get fallback rule cards without LLM.
    
    This function is called when the Gemini API is rate-limited.
    It parses the PDF and generates structured rules manually.
    
    Args:
        pdf_path: Path to the rulebook PDF
        game_config: Optional game configuration
        num_cards: Number of cards to generate
        
    Returns:
        Dict with rules_cards and game_summary
    """
    global _parser_instance
    
    if _parser_instance is None:
        _parser_instance = DandiBiyoPDFParser(pdf_path)
    elif _parser_instance.pdf_path != pdf_path:
        _parser_instance = DandiBiyoPDFParser(pdf_path)
    
    return _parser_instance.generate_rule_cards(
        game_config=game_config,
        num_cards=num_cards
    )
