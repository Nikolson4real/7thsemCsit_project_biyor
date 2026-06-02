# BiyoR AI Rules Engine - Game Flow Logic

## Overview

The BiyoR AI Rules Engine provides a **2-phase game flow** for the Dandi Biyo AR mobile app. This simplified architecture handles all game scenarios through two main phases: **Initial Game** and **In-Game**.

---

## Game Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BIYOAR GAME FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │  APP START   │
                              └──────┬───────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │     Configure Game Settings    │
                    │  - Equipment dimensions        │
                    │  - Field/ground description    │
                    │  - Number of players           │
                    │  - Team assignments            │
                    └────────────────┬───────────────┘
                                     │
                                     ▼
         ╔═══════════════════════════════════════════════════════╗
         ║              PHASE 1: INITIAL GAME                    ║
         ║                                                       ║
         ║  POST /api/v1/game/initial                            ║
         ║                                                       ║
         ║  Purpose:                                             ║
         ║  • Get rules briefing                                 ║
         ║  • Receive AR field layout                            ║
         ║  • Understand game basics                             ║
         ╚═══════════════════════════════════════════════════════╝
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │   Display Rules & Field Setup  │
                    │   - Show important rules       │
                    │   - Render AR field overlay    │
                    │   - Display scoring zones      │
                    └────────────────┬───────────────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │  GAME START  │
                              └──────┬───────┘
                                     │
         ╔═══════════════════════════════════════════════════════╗
         ║               PHASE 2: IN-GAME                        ║
         ║                                                       ║
         ║  POST /api/v1/game/query                              ║
         ║                                                       ║
         ║  Handles all gameplay queries:                        ║
         ║  ┌─────────────────────────────────────────────────┐  ║
         ║  │  query_type: "scoring"                          │  ║
         ║  │  - Calculate points for hits                    │  ║
         ║  │  - Validate scoring attempts                    │  ║
         ║  └─────────────────────────────────────────────────┘  ║
         ║  ┌─────────────────────────────────────────────────┐  ║
         ║  │  query_type: "foul_check"                       │  ║
         ║  │  - Determine if action is a foul                │  ║
         ║  │  - Get penalty information                      │  ║
         ║  └─────────────────────────────────────────────────┘  ║
         ║  ┌─────────────────────────────────────────────────┐  ║
         ║  │  query_type: "clarification"                    │  ║
         ║  │  - Answer rule questions                        │  ║
         ║  │  - Explain specific scenarios                   │  ║
         ║  └─────────────────────────────────────────────────┘  ║
         ║  ┌─────────────────────────────────────────────────┐  ║
         ║  │  query_type: "general"                          │  ║
         ║  │  - Any other game-related queries               │  ║
         ║  └─────────────────────────────────────────────────┘  ║
         ╚═══════════════════════════════════════════════════════╝
                                     │
                                     │ (Loop during gameplay)
                                     │
                              ┌──────┴───────┐
                              │   GAME END   │
                              └──────────────┘
```

---

## Phase Details

### Phase 1: Initial Game (`/api/v1/game/initial`)

**When to call:** At the start of a new game session, before gameplay begins.

**Purpose:**
- Retrieve essential rules briefing for players
- Get AR field layout configuration
- Understand game overview and setup requirements

**Request:**
```json
{
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
  "session_id": "unique_session_id"
}
```

**Response:**
```json
{
  "important_rules": [
    {
      "id": "rule_1",
      "title": "Basic Objective",
      "type": "RULE",
      "priority": 1,
      "body": "Hit the Biyo with the Dandi to score points...",
      "reasoning_summary": "Core game mechanic"
    }
  ],
  "field_layout": {
    "anchor_position": "Center of playing field",
    "field_boundaries": "Rectangular, 30m x 20m",
    "safe_zone_radius_m": 5,
    "scoring_zones": [...],
    "visual_hints": "Mark boundaries with AR lines"
  },
  "game_overview": "Dandi Biyo is a traditional stick-hitting game...",
  "model_metadata": {...},
  "session_id": "unique_session_id"
}
```

---

### Phase 2: In-Game (`/api/v1/game/query`)

**When to call:** During active gameplay for any game-related queries.

#### Query Type: `scoring`

**Purpose:** Calculate points when a player hits the Biyo.

**Request:**
```json
{
  "game_config": {...},
  "query_type": "scoring",
  "situation_summary": "Player hit the Biyo and it landed 12 meters away",
  "estimated_distance_m": 12.0,
  "session_id": "unique_session_id"
}
```

**Response:**
```json
{
  "cards": [...],
  "overall_summary": "Valid hit! Score: 12 points",
  "score": 12,
  "is_valid_attempt": true,
  "model_metadata": {...}
}
```

---

#### Query Type: `foul_check`

**Purpose:** Determine if an action constitutes a foul.

**Request:**
```json
{
  "game_config": {...},
  "query_type": "foul_check",
  "action_description": "Player stepped outside the striking zone while hitting",
  "player_team": "Team A",
  "session_id": "unique_session_id"
}
```

**Response:**
```json
{
  "cards": [...],
  "overall_summary": "This is a foul - stepping outside the zone",
  "is_foul": true,
  "penalty_description": "Turn passes to opposing team",
  "model_metadata": {...}
}
```

---

#### Query Type: `clarification`

**Purpose:** Answer rule-related questions during gameplay.

**Request:**
```json
{
  "game_config": {...},
  "query_type": "clarification",
  "situation_summary": "What happens if the Biyo goes out of bounds?",
  "session_id": "unique_session_id"
}
```

**Response:**
```json
{
  "cards": [
    {
      "id": "clarify_1",
      "title": "Out of Bounds Rule",
      "body": "If the Biyo lands outside the field...",
      "reasoning_summary": "Boundary rules"
    }
  ],
  "overall_summary": "When Biyo goes out of bounds...",
  "model_metadata": {...}
}
```

---

#### Query Type: `general`

**Purpose:** Handle any other game-related queries.

**Request:**
```json
{
  "game_config": {...},
  "query_type": "general",
  "situation_summary": "How do we decide who goes first?",
  "session_id": "unique_session_id"
}
```

---

## Sequence Diagram

```
┌──────────┐          ┌──────────────┐          ┌─────────────┐
│  Mobile  │          │   Backend    │          │   Gemini    │
│   App    │          │   (FastAPI)  │          │     LLM     │
└────┬─────┘          └──────┬───────┘          └──────┬──────┘
     │                       │                         │
     │  POST /game/initial   │                         │
     │──────────────────────>│                         │
     │                       │  Retrieve rules context │
     │                       │  from FAISS index       │
     │                       │─────────────────────────│
     │                       │                         │
     │                       │  Generate briefing      │
     │                       │────────────────────────>│
     │                       │                         │
     │                       │<────────────────────────│
     │                       │  JSON response          │
     │<──────────────────────│                         │
     │  Rules + Field Layout │                         │
     │                       │                         │
     │                       │                         │
     │  === GAMEPLAY LOOP ===│                         │
     │                       │                         │
     │  POST /game/query     │                         │
     │  (scoring)            │                         │
     │──────────────────────>│                         │
     │                       │  Retrieve scoring rules │
     │                       │────────────────────────>│
     │                       │<────────────────────────│
     │<──────────────────────│                         │
     │  Score + Validation   │                         │
     │                       │                         │
     │  POST /game/query     │                         │
     │  (foul_check)         │                         │
     │──────────────────────>│                         │
     │                       │  Check foul rules       │
     │                       │────────────────────────>│
     │                       │<────────────────────────│
     │<──────────────────────│                         │
     │  Foul + Penalty       │                         │
     │                       │                         │
     │  POST /game/query     │                         │
     │  (clarification)      │                         │
     │──────────────────────>│                         │
     │                       │  Find relevant rules    │
     │                       │────────────────────────>│
     │                       │<────────────────────────│
     │<──────────────────────│                         │
     │  Rule Explanation     │                         │
     │                       │                         │
```

---

## Data Models

### GameConfiguration
```
GameConfiguration
├── equipment_dimensions
│   ├── dandi_length_cm: float (optional)
│   ├── biyo_length_cm: float (optional)
│   └── biyo_diameter_cm: float (optional)
├── ground_description
│   ├── surface_type: enum (grass|dirt|concrete|sand|other)
│   ├── field_length_m: float (optional)
│   ├── field_width_m: float (optional)
│   └── anchor_position: string (optional)
├── num_players_available: int (optional)
├── team_a_players: int (optional)
├── team_b_players: int (optional)
└── language_preference: string (default: "en")
```

### Response Models

**InitialGameResponse:**
```
InitialGameResponse
├── important_rules: List[InstructionCard]
├── field_layout: ARFieldLayout
├── game_overview: string
├── model_metadata: ModelMetadata
└── session_id: string
```

**InGameResponse:**
```
InGameResponse
├── cards: List[InstructionCard]
├── overall_summary: string
├── score: int (for scoring queries)
├── is_valid_attempt: bool (for scoring queries)
├── is_foul: bool (for foul checks)
├── penalty_description: string (for foul checks)
├── model_metadata: ModelMetadata
└── session_id: string
```

---

## Error Handling

The API uses graceful degradation:

1. **Primary Model Failure:** Falls back to secondary Gemini model
2. **JSON Parse Failure:** Uses repair logic to fix malformed JSON
3. **All Models Fail:** Returns a fallback response with generic guidance
4. **Quota Exceeded:** Returns cached/fallback response

---

## Best Practices for Mobile App Integration

1. **Call `/game/initial` once** at the start of each game session
2. **Cache the initial response** for the duration of the game
3. **Use `/game/query` with appropriate `query_type`** for all in-game situations
4. **Include `session_id`** for logging and debugging
5. **Handle fallback responses gracefully** in the UI
6. **Implement retry logic** for transient failures

---

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/game/initial` | POST | Game setup and rules briefing |
| `/api/v1/game/query` | POST | All in-game queries |
| `/api/v1/rules/health` | GET | Health check |
| `/api/v1/rules/query` | POST | Legacy rules query |
| `/api/v1/rules/reindex` | POST | Rebuild FAISS index |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2025-12-16 | Simplified to 2-phase flow (initial_game, in_game) |
| 1.0 | 2025-12-15 | Initial 4-phase implementation |

---

# Frontend Integration Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MOBILE APP (Frontend)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  AR Camera  │  │  Game UI    │  │  Score      │  │  Rules      │        │
│  │  Module     │  │  Controls   │  │  Display    │  │  Cards      │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │               │
│         └────────────────┴────────────────┴────────────────┘               │
│                                   │                                         │
│                          HTTP/HTTPS Requests                                │
└───────────────────────────────────┼─────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND                                       │
│                                                                               │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐          │
│  │  /game/initial  │    │  /game/query    │    │  /rules/health  │          │
│  │  (Phase 1)      │    │  (Phase 2)      │    │  (Health Check) │          │
│  └────────┬────────┘    └────────┬────────┘    └─────────────────┘          │
│           │                      │                                           │
│           └──────────┬───────────┘                                           │
│                      │                                                       │
│                      ▼                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        RAG PIPELINE                                    │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐               │  │
│  │  │  Embedding  │───▶│   FAISS     │───▶│  Context    │               │  │
│  │  │  Generator  │    │   Search    │    │  Builder    │               │  │
│  │  └─────────────┘    └─────────────┘    └─────────────┘               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                      │                                                       │
│                      ▼                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        LLM CLIENT                                      │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐               │  │
│  │  │   Prompt    │───▶│   Gemini    │───▶│   JSON      │               │  │
│  │  │   Builder   │    │   2.5 Flash │    │   Parser    │               │  │
│  │  └─────────────┘    └─────────────┘    └─────────────┘               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SERVICES                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    Google AI Studio (Gemini API)                         │ │
│  │  • Gemini 2.5 Flash (Primary)                                           │ │
│  │  • Gemini 2.0 Flash (Fallback)                                          │ │
│  │  • Text Embedding 004 (Embeddings)                                      │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## RAG Pipeline Deep Dive

### What is RAG?

**RAG (Retrieval-Augmented Generation)** combines:
1. **Retrieval**: Finding relevant information from a knowledge base
2. **Generation**: Using an LLM to generate responses based on retrieved context

This ensures the AI's responses are grounded in the actual Dandi Biyo rulebook.

### RAG Pipeline Steps

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RAG PIPELINE FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

Step 1: INDEXING (Done once at startup or when rulebooks change)
═══════════════════════════════════════════════════════════════

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Rulebook    │────▶│   Chunking   │────▶│  Embedding   │────▶│    FAISS     │
│  PDF/MD      │     │  Split into  │     │  Convert to  │     │    Index     │
│  Files       │     │  600-char    │     │  768-dim     │     │  (Saved to   │
│              │     │  chunks      │     │  vectors     │     │   disk)      │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘

Example:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Original Text:                                                              │
│ "Dandi Biyo is a traditional Nepali game. The equipment consists of two    │
│ wooden sticks: the Dandi (longer stick, about 60cm) and the Biyo (shorter  │
│ piece, about 8cm). The game is played by hitting the Biyo with the Dandi   │
│ and measuring the distance..."                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Chunk 1: "Dandi Biyo is a traditional Nepali game. The equipment consists  │
│ of two wooden sticks: the Dandi (longer stick, about 60cm) and the Biyo    │
│ (shorter piece, about 8cm)."                                               │
│ → Embedding: [0.12, -0.34, 0.56, ..., 0.89] (768 dimensions)              │
└─────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────┐
│ Chunk 2: "The game is played by hitting the Biyo with the Dandi and        │
│ measuring the distance..."                                                  │
│ → Embedding: [0.23, -0.45, 0.67, ..., 0.78] (768 dimensions)              │
└─────────────────────────────────────────────────────────────────────────────┘


Step 2: RETRIEVAL (Done for each query)
═══════════════════════════════════════

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User Query  │────▶│   Embed      │────▶│    FAISS     │────▶│  Top-K       │
│  "How is     │     │   Query      │     │   Similarity │     │  Relevant    │
│  scoring     │     │              │     │   Search     │     │  Chunks      │
│  calculated?"│     │              │     │              │     │  (k=5)       │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘

Example:
Query: "How is scoring calculated in Dandi Biyo?"
Query Embedding: [0.15, -0.38, 0.62, ..., 0.85]

FAISS Search Results (by cosine similarity):
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Score: 0.92 - "Scoring in Dandi Biyo is based on the distance the Biyo  │
│    travels. Distances are measured from the anchor point..."               │
│                                                                             │
│ 2. Score: 0.87 - "Points are awarded as follows: 0-5m = 1 point,           │
│    5-10m = 2 points, 10-20m = 3 points, 20m+ = 4 points"                   │
│                                                                             │
│ 3. Score: 0.82 - "The distance measurement must be made from the center    │
│    of the anchor point to where the Biyo first lands..."                   │
│                                                                             │
│ 4. Score: 0.78 - "If the Biyo lands outside the boundary, the attempt      │
│    is still valid but the distance is measured to the boundary line..."    │
│                                                                             │
│ 5. Score: 0.74 - "Each player gets three attempts per round. The highest   │
│    scoring attempt counts..."                                               │
└─────────────────────────────────────────────────────────────────────────────┘


Step 3: GENERATION (LLM creates response using context)
═══════════════════════════════════════════════════════

┌──────────────────────────────────────────────────────────────────────────────┐
│ PROMPT SENT TO GEMINI:                                                       │
│                                                                              │
│ You are an expert Dandi Biyo scoring referee.                               │
│                                                                              │
│ RETRIEVED RULEBOOK CONTEXT:                                                  │
│ ---                                                                          │
│ Source: Dandi_Biyo_Rulebook.pdf                                             │
│ Scoring in Dandi Biyo is based on the distance the Biyo travels...          │
│ ---                                                                          │
│ Source: Dandi_Biyo_Rulebook.pdf                                             │
│ Points are awarded as follows: 0-5m = 1 point, 5-10m = 2 points...          │
│ ---                                                                          │
│ [... more context ...]                                                       │
│                                                                              │
│ SCORING QUERY:                                                               │
│ Situation: Player hit the Biyo cleanly                                       │
│ Estimated Distance: 12 meters                                                │
│                                                                              │
│ Calculate the score and provide your ruling...                               │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ GEMINI RESPONSE (JSON):                                                      │
│ {                                                                            │
│   "cards": [{                                                                │
│     "title": "Score Calculation",                                            │
│     "body": "12 meters falls in the 10-20m zone = 3 points",                │
│     "reasoning_summary": "Based on Section 3.2 of the rulebook"             │
│   }],                                                                        │
│   "score": 3,                                                                │
│   "is_valid_attempt": true                                                   │
│ }                                                                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Why RAG is Important

| Without RAG | With RAG |
|-------------|----------|
| LLM might hallucinate rules | Responses grounded in actual rulebook |
| Inconsistent answers | Consistent, accurate rulings |
| Generic game knowledge | Specific Dandi Biyo rules |
| No source references | Can cite specific rule sections |

---

## Frontend API Call Examples

### Phase 1: Initial Game Request Flow

```
┌──────────────┐                    ┌──────────────┐                    ┌──────────────┐
│  Mobile App  │                    │   Backend    │                    │  Gemini API  │
└──────┬───────┘                    └──────┬───────┘                    └──────┬───────┘
       │                                   │                                   │
       │  1. POST /api/v1/game/initial     │                                   │
       │  {game_config, session_id}        │                                   │
       │──────────────────────────────────▶│                                   │
       │                                   │                                   │
       │                                   │  2. Build context query           │
       │                                   │  "Explain basic rules..."         │
       │                                   │──────────┐                        │
       │                                   │          │                        │
       │                                   │◀─────────┘                        │
       │                                   │                                   │
       │                                   │  3. Embed query & search FAISS    │
       │                                   │──────────┐                        │
       │                                   │          │ (Local operation)      │
       │                                   │◀─────────┘                        │
       │                                   │                                   │
       │                                   │  4. Build prompt with context     │
       │                                   │──────────┐                        │
       │                                   │          │                        │
       │                                   │◀─────────┘                        │
       │                                   │                                   │
       │                                   │  5. Call Gemini API               │
       │                                   │──────────────────────────────────▶│
       │                                   │                                   │
       │                                   │  6. JSON response                 │
       │                                   │◀──────────────────────────────────│
       │                                   │                                   │
       │                                   │  7. Parse & validate response     │
       │                                   │──────────┐                        │
       │                                   │          │                        │
       │                                   │◀─────────┘                        │
       │                                   │                                   │
       │  8. InitialGameResponse           │                                   │
       │  {important_rules, field_layout,  │                                   │
       │   game_overview, model_metadata}  │                                   │
       │◀──────────────────────────────────│                                   │
       │                                   │                                   │
```

### Frontend Code Example (Dart/Flutter)

```dart
// lib/services/biyor_api_service.dart

class BiyorApiService {
  final String baseUrl = 'https://your-api-server.com/api/v1';
  final http.Client _client = http.Client();

  /// Phase 1: Initialize a new game
  Future<InitialGameResponse> startNewGame({
    required GameConfig config,
    String? sessionId,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/game/initial'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'game_config': {
          'equipment_dimensions': {
            'dandi_length_cm': config.dandiLength,
            'biyo_length_cm': config.biyoLength,
            'biyo_diameter_cm': config.biyoDiameter,
          },
          'ground_description': {
            'surface_type': config.surfaceType,
            'field_length_m': config.fieldLength,
            'field_width_m': config.fieldWidth,
          },
          'num_players_available': config.totalPlayers,
          'team_a_players': config.teamAPlayers,
          'team_b_players': config.teamBPlayers,
          'language_preference': config.language,
        },
        'session_id': sessionId ?? _generateSessionId(),
      }),
    );

    if (response.statusCode == 200) {
      return InitialGameResponse.fromJson(jsonDecode(response.body));
    } else {
      throw BiyorApiException(response.statusCode, response.body);
    }
  }

  /// Phase 2: Calculate score for a hit
  Future<InGameResponse> calculateScore({
    required double distanceMeters,
    required String situationDescription,
    required String sessionId,
    GameConfig? config,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/game/query'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'game_config': config?.toJson() ?? {},
        'query_type': 'scoring',
        'situation_summary': situationDescription,
        'estimated_distance_m': distanceMeters,
        'session_id': sessionId,
      }),
    );

    if (response.statusCode == 200) {
      return InGameResponse.fromJson(jsonDecode(response.body));
    } else {
      throw BiyorApiException(response.statusCode, response.body);
    }
  }

  /// Check if an action is a foul
  Future<InGameResponse> checkFoul({
    required String actionDescription,
    required String playerTeam,
    required String sessionId,
    GameConfig? config,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/game/query'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'game_config': config?.toJson() ?? {},
        'query_type': 'foul_check',
        'situation_summary': 'Checking if this action is a foul',
        'action_description': actionDescription,
        'player_team': playerTeam,
        'session_id': sessionId,
      }),
    );

    if (response.statusCode == 200) {
      return InGameResponse.fromJson(jsonDecode(response.body));
    } else {
      throw BiyorApiException(response.statusCode, response.body);
    }
  }

  /// Ask for rule clarification
  Future<InGameResponse> askClarification({
    required String question,
    required String sessionId,
    GameConfig? config,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/game/query'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'game_config': config?.toJson() ?? {},
        'query_type': 'clarification',
        'situation_summary': question,
        'session_id': sessionId,
      }),
    );

    if (response.statusCode == 200) {
      return InGameResponse.fromJson(jsonDecode(response.body));
    } else {
      throw BiyorApiException(response.statusCode, response.body);
    }
  }
}
```

---

## Error Handling

### Frontend Error Handling Strategy

```dart
class BiyorApiService {
  Future<InGameResponse> safeQuery({
    required String queryType,
    required String situation,
    required String sessionId,
  }) async {
    try {
      return await _makeQuery(queryType, situation, sessionId);
    } on SocketException {
      // Network error - show offline message
      return _createOfflineResponse();
    } on TimeoutException {
      // Request timeout - suggest retry
      return _createTimeoutResponse();
    } on BiyorApiException catch (e) {
      if (e.statusCode == 429) {
        // Rate limited - wait and retry
        await Future.delayed(Duration(seconds: 10));
        return await _makeQuery(queryType, situation, sessionId);
      } else if (e.statusCode == 503) {
        // Service unavailable
        return _createServiceUnavailableResponse();
      } else {
        // Other API error
        return _createErrorResponse(e.message);
      }
    }
  }
}
```

### Common Error Scenarios

| Error | HTTP Status | Frontend Action |
|-------|-------------|-----------------|
| Rate Limited | 429 | Wait 10s, retry automatically |
| Service Down | 503 | Show offline message, cache last response |
| Invalid Request | 400 | Show validation error to user |
| Server Error | 500 | Log error, show generic message |
| Timeout | - | Retry once, then show timeout message |

---

## Best Practices for Mobile App Integration

1. **Call `/game/initial` once** at the start of each game session
2. **Cache the initial response** for the duration of the game
3. **Use `/game/query` with appropriate `query_type`** for all in-game situations
4. **Include `session_id`** for logging and debugging
5. **Handle fallback responses gracefully** in the UI
6. **Implement retry logic** for transient failures
7. **Expect 1-3 second response times** for LLM queries
8. **Use `field_layout`** from initial response for AR overlay
9. **Use `suggested_ar_visual`** hints to guide AR rendering

---

## Experimental Endpoint: Initial Rules Modified

### `/api/v1/game/initial_rule_modified` (POST)

> **EXPERIMENTAL:** This endpoint bypasses RAG and injects the entire PDF rulebook directly into the LLM prompt for testing purposes.

**Purpose:**
- Load the COMPLETE Dandi Biyo rulebook PDF content
- Pass full rulebook to LLM without chunking/retrieval
- Generate 6-7 essential rule cards optimized for AR overlay
- Adapt rules based on provided game configuration

**When to use:**
- Testing full-context LLM responses vs RAG-based responses
- When you need all rulebook context without retrieval limitations
- Comparing response quality between RAG and full-document approaches

### Request Format

```json
{
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
```

### PowerShell Example

```powershell
$body = @{
  game_config = @{
    equipment_dimensions = @{
      dandi_length_cm = 60
      biyo_length_cm = 8
    }
    ground_description = @{
      surface_type = "grass"
      field_length_m = 30
      field_width_m = 20
    }
    num_players_available = 4
  }
  session_id = "game_001"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/game/initial_rule_modified" `
  -Method Post -Body $body -ContentType "application/json"
```

### Response Format

```json
{
  "rules_cards": [
    {
      "card_id": "rule_001",
      "category": "objective",
      "title": "Game Objective",
      "body": "Hit the Biyo as far as possible with the Dandi to score points.",
      "priority": 1,
      "icon_hint": "target",
      "ar_highlight": "field_center"
    },
    {
      "card_id": "rule_002",
      "category": "equipment",
      "title": "Equipment Setup",
      "body": "Use a 60cm Dandi stick and 8cm Biyo peg.",
      "priority": 2,
      "icon_hint": "ruler",
      "ar_highlight": "equipment_area"
    }
    // ... 4-5 more cards
  ],
  "total_cards": 6,
  "categories": ["objective", "equipment", "gameplay", "scoring", "foul", "safety"],
  "game_summary": "Dandi Biyo is a traditional Nepali stick-hitting game where players score by hitting the Biyo as far as possible.",
  "equipment_adapted": true,
  "field_adapted": true,
  "model_metadata": {
    "model_name": "models/gemini-2.5-flash",
    "retrieved_chunk_count": 3,
    "processing_time_ms": 2500
  },
  "session_id": "game_001"
}
```

### Rule Card Categories

| Category | Description | Icon Hint |
|----------|-------------|------------|
| `objective` | Game goal and winning conditions | `target` |
| `equipment` | Equipment rules and requirements | `ruler` |
| `setup` | Field setup and positioning | `flag` |
| `turn_order` | Turn sequence and player order | `player` |
| `gameplay` | Core gameplay mechanics | `info` |
| `scoring` | How points are calculated | `score` |
| `foul` | Common fouls and penalties | `warning` |
| `safety` | Safety rules and guidelines | `warning` |

### AR Highlight Options

| Value | Description |
|-------|-------------|
| `field_center` | Highlight center of playing field |
| `scoring_zones` | Show scoring zone distance rings |
| `boundary_lines` | Display field boundary lines |
| `equipment_area` | Highlight equipment placement area |
| `player_position` | Show where players should stand |
| `null` | No AR highlight needed |

### Dart/Flutter Integration

```dart
class InitialRuleCard {
  final String cardId;
  final String category;
  final String title;
  final String body;
  final int priority;
  final String? iconHint;
  final String? arHighlight;

  InitialRuleCard.fromJson(Map<String, dynamic> json)
      : cardId = json['card_id'],
        category = json['category'],
        title = json['title'],
        body = json['body'],
        priority = json['priority'],
        iconHint = json['icon_hint'],
        arHighlight = json['ar_highlight'];
}

class InitialRulesModifiedResponse {
  final List<InitialRuleCard> rulesCards;
  final int totalCards;
  final List<String> categories;
  final String gameSummary;
  final bool equipmentAdapted;
  final bool fieldAdapted;

  InitialRulesModifiedResponse.fromJson(Map<String, dynamic> json)
      : rulesCards = (json['rules_cards'] as List)
            .map((c) => InitialRuleCard.fromJson(c))
            .toList(),
        totalCards = json['total_cards'],
        categories = List<String>.from(json['categories']),
        gameSummary = json['game_summary'],
        equipmentAdapted = json['equipment_adapted'],
        fieldAdapted = json['field_adapted'];
}

// API call
Future<InitialRulesModifiedResponse> getInitialRulesModified({
  required Map<String, dynamic> gameConfig,
  required String sessionId,
}) async {
  final response = await http.post(
    Uri.parse('$baseUrl/api/v1/game/initial_rule_modified'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'game_config': gameConfig,
      'session_id': sessionId,
    }),
  );

  if (response.statusCode == 200) {
    return InitialRulesModifiedResponse.fromJson(jsonDecode(response.body));
  } else {
    throw Exception('Failed to get initial rules: ${response.statusCode}');
  }
}
```

### Comparison: RAG vs Full-Document Approach

| Aspect | `/game/initial` (RAG) | `/game/initial_rule_modified` (Full PDF) |
|--------|----------------------|------------------------------------------|
| Context | Retrieved chunks only | Entire PDF content |
| Token Usage | Lower (~2-5K tokens) | Higher (~10-20K tokens) |
| Response Time | Faster (< 2s) | Slower (2-5s) |
| Accuracy | Good for specific queries | Better for comprehensive rules |
| Cost | Lower API cost | Higher API cost |
| Use Case | Production | Testing/Comparison |
