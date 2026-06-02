# BiyoR AI Rules Engine - Architecture Documentation

## System Overview

The BiyoR AI Rules Engine is a Retrieval-Augmented Generation (RAG) backend that provides real-time, context-aware rules and guidance for the traditional Nepali sport Dandi Biyo. It bridges traditional sports knowledge with modern AR technology.

## Architecture Principles

1. **Dandi Biyo-Specific**: All logic, prompts, and processing are tailored exclusively for Dandi Biyo rules
2. **Google AI Studio Only**: Uses Google AI Studio APIs for both embeddings and LLM calls (NO Vertex AI)
3. **Card-Based Output**: Responses are structured as small, AR-friendly instruction cards
4. **Deterministic & Debuggable**: Extensive logging, configurable parameters, and transparent retrieval

## RAG Pipeline Architecture

### Phase 1: Document Ingestion & Indexing

```
Rulebook Files (PDF/TXT/MD/DOCX)
    │
    ▼
┌─────────────────────────────────┐
│   Document Loaders              │
│   - PyPDFLoader for PDFs        │
│   - TextLoader for TXT          │
│   - UnstructuredMarkdown for MD │
│   - Docx2txtLoader for DOCX     │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│   Text Splitter                 │
│   - RecursiveCharacterTextSplit │
│   - Chunk size: 600 tokens      │
│   - Overlap: 100 tokens         │
│   - Preserves metadata          │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│   Google AI Studio Embeddings   │
│   Model: text-embedding-004     │
│   - Batch embedding generation  │
│   - Task type: retrieval_doc    │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│   FAISS Index (IndexFlatL2)     │
│   - Stores embeddings           │
│   - Metadata stored separately  │
│   - Saved to disk (pickled)     │
└─────────────────────────────────┘
```

**Key Design Decisions:**

- **Chunk Size (600)**: Balances context richness with retrieval precision. Large enough for complete rule sections, small enough for focused retrieval.
- **Overlap (100)**: Ensures rule sections that span chunk boundaries are captured.
- **FAISS IndexFlatL2**: Simple L2 distance search. Exact search (no approximation) ensures we don't miss critical rules.
- **Metadata Preservation**: Each chunk retains source, section, page info for citations.

### Phase 2: Query Processing & Retrieval

```
API Request (RulesQueryRequest)
    │
    ▼
┌─────────────────────────────────┐
│   Query Construction            │
│   - Situation summary           │
│   - Equipment dimensions        │
│   - Ground description          │
│   - Game phase                  │
│   - Player count                │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│   Google AI Studio Embeddings   │
│   Model: text-embedding-004     │
│   - Task type: retrieval_query  │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│   FAISS Similarity Search       │
│   - Top-K retrieval (default: 5)│
│   - L2 distance scoring         │
│   - Returns chunks + scores     │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│   Retrieved Context             │
│   - Rule chunks with metadata   │
│   - Similarity scores           │
│   - Source references           │
└─────────────────────────────────┘
```

**Key Design Decisions:**

- **Structured Query Building**: Combines situation narrative with structured data (equipment, field) for richer semantic matching.
- **Top-K = 5**: Provides enough context without overwhelming the LLM. Tunable via config.
- **Task Type Differentiation**: Uses `retrieval_query` for queries vs `retrieval_document` for indexing (optimizes embedding generation).

### Phase 3: LLM Generation with Gemini

```
Retrieved Chunks + Situation
    │
    ▼
┌─────────────────────────────────┐
│   Prompt Engineering            │
│   ┌───────────────────────────┐ │
│   │ System Prompt             │ │
│   │ - Role: Dandi Biyo expert │ │
│   │ - Rules: Stay faithful   │ │
│   │ - Output: JSON only       │ │
│   └───────────────────────────┘ │
│   ┌───────────────────────────┐ │
│   │ User Prompt               │ │
│   │ - Situation JSON          │ │
│   │ - Retrieved chunks        │ │
│   │ - Response schema         │ │
│   │ - Task instructions       │ │
│   └───────────────────────────┘ │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│   Gemini API Call               │
│   Primary: gemini-2.5-flash     │
│   Fallback: gemini-2.0          │
│   Config:                       │
│   - Temperature: 0.1            │
│   - response_mime_type: JSON    │
│   - Max tokens: 2048            │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│   JSON Response Parsing         │
│   - Validate against schema     │
│   - Extract cards array         │
│   - Parse rule references       │
└─────────────┬───────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│   Pydantic Model Validation     │
│   - RulesQueryResponse          │
│   - InstructionCard[]           │
│   - ModelMetadata               │
└─────────────────────────────────┘
```

**Key Design Decisions:**

- **System Prompt**: Establishes Gemini as a strict Dandi Biyo referee who only uses retrieved rules.
- **JSON Mode**: Forces structured output via `response_mime_type: application/json`.
- **Low Temperature (0.1)**: Ensures consistent, deterministic responses focused on factual rules.
- **Retry + Fallback**: 3 retries with exponential backoff, then fallback to secondary model.
- **Schema Enforcement**: Both in prompt (examples) and in Pydantic validation.

## Prompt Engineering Strategy

### System Prompt Design

```
You are an expert Dandi Biyo referee and instructor.

Your role:
- Provide accurate rules based ONLY on retrieved documents
- NEVER invent rules
- Break down complex rules into small instruction cards
- Each card focuses on ONE rule/action/decision
- Use clear, player-friendly language
- Reference specific rule sections

Output format:
- MUST respond with valid JSON only
- Match the provided schema exactly
- Keep card bodies short (max 2-3 sentences)
```

**Why This Works:**
- Clear role definition prevents hallucination
- Explicit constraints ("ONLY retrieved documents", "NEVER invent")
- Output format specification ensures parseable responses
- Brevity requirement keeps cards AR-friendly

### User Prompt Structure

1. **Situation Summary**: Natural language + structured data
2. **Retrieved Chunks**: Formatted with metadata (source, section, page)
3. **Task Description**: Specific analysis instructions
   - Equipment validation
   - Field validation
   - Scoring computation
   - Foul detection
4. **Response Schema**: Exact JSON structure expected
5. **Critical Instructions**: Reinforcement of constraints

**Example Prompt Template:**

```
# Current Game Situation
{situation_json}

# Retrieved Dandi Biyo Rule Chunks
[Chunk 1]
Source: Official Dandi Biyo Rulebook 2024
Section: 4.2.1
Content: {chunk_content}

# Your Task
Analyze using retrieved rules.
Generate cards that:
1. Address one aspect per card
2. Prioritize by importance
3. Include rule references
4. Validate equipment/field
5. Compute scores
6. Identify fouls

# Required JSON Response Schema
{response_schema}

# Critical Instructions
- Output ONLY valid JSON
- Keep bodies concise
- Reference rule sections
- State when rules are unclear
- Suggest AR visualizations
```

## Card-Based Response Design

### Why Cards?

AR applications need bite-sized, focused information that can be:
- Displayed as overlay cards in AR view
- Shown one at a time without overwhelming players
- Easily prioritized (high priority cards shown first)
- Augmented with visual hints for AR rendering

### Card Structure

```typescript
{
  id: string              // Unique identifier
  title: string           // 3-7 word headline
  type: CardType          // RULE | EXPLANATION | ACTION_STEP | WARNING | TIP | SCORING
  priority: 1-10          // Display order (1 = highest)
  body: string            // 50-150 words of explanation
  reasoning_summary: string // Why this card applies
  related_rule_refs: [    // Source citations
    { source, section, page }
  ]
  suggested_ar_visual: string // AR rendering hint
}
```

### Card Types

- **RULE**: Fundamental game rule application
- **EXPLANATION**: Clarification of complex rules
- **ACTION_STEP**: What the player should do next
- **WARNING**: Foul alert or caution
- **TIP**: Helpful advice or best practice
- **SCORING**: Score calculation and explanation

### Example Card Generation Logic

For a situation: "Player struck Biyo, landed 15m away"

```
Card 1 (Priority 1, Type: RULE)
- Title: "Valid Strike Confirmed"
- Body: "Strike is valid. Biyo was airborne and landed in bounds."
- Rule Refs: Section 4.2.2
- AR Visual: "Highlight landing point, show boundary"

Card 2 (Priority 2, Type: SCORING)
- Title: "Score Calculation"
- Body: "Distance: 15m ÷ 0.6m Dandi = 25 points"
- Rule Refs: Section 5.1
- AR Visual: "Draw measurement line from anchor to landing"

Card 3 (Priority 3, Type: ACTION_STEP)
- Title: "Next Step"
- Body: "Record 25 points for Team A. Team B's turn."
- AR Visual: "Update scoreboard"
```

## Data Flow

### Complete Request-Response Flow

```
1. Flutter App → POST /api/v1/rules/query
   {
     situation_summary: "...",
     equipment_dimensions: {...},
     ground_description: {...},
     ...
   }

2. FastAPI → RulesQueryRequest validation (Pydantic)

3. RAG Pipeline → build_retrieval_query()
   Combines situation + equipment + ground → optimized query string

4. RAG Pipeline → retrieve()
   Query → Google embeddings → FAISS search → top-5 chunks

5. LLM Client → generate_rules_response()
   Chunks + situation + schema → Gemini prompt

6. Gemini API → generate_content()
   Temperature: 0.1, JSON mode → structured response

7. LLM Client → JSON parsing + validation

8. Routes → RulesQueryResponse construction
   Cards + metadata + session_id

9. FastAPI → RulesQueryResponse validation (Pydantic)

10. Flutter App ← JSON response
    {
      cards: [...],
      overall_summary: "...",
      model_metadata: {...}
    }
```

## Configuration & Tunables

### Environment Variables

| Variable | Purpose | Tuning Guidance |
|----------|---------|-----------------|
| `RETRIEVAL_TOP_K` | Chunks to retrieve | 3-5: focused, 6-10: comprehensive |
| `CHUNK_SIZE` | Document chunk tokens | 400-600: rules, 800-1200: narrative |
| `CHUNK_OVERLAP` | Chunk overlap tokens | 50-100: minimal, 150-200: maximum coherence |
| `LLM_TEMPERATURE` | Response randomness | 0.0-0.2: factual, 0.3-0.5: creative |
| `LLM_MAX_OUTPUT_TOKENS` | Response length | 1024: brief, 2048: detailed, 4096: comprehensive |

### Tuning for Different Use Cases

**Tutorial Mode:**
- Higher CHUNK_SIZE (800+)
- More TOP_K (8-10)
- Higher MAX_OUTPUT_TOKENS (3000+)
- More EXPLANATION and TIP cards

**Fast Referee Mode:**
- Lower CHUNK_SIZE (400-500)
- Fewer TOP_K (3-4)
- Lower MAX_OUTPUT_TOKENS (1024)
- More RULE and ACTION_STEP cards

**Scoring Validation:**
- Focus retrieval on scoring sections (filter by metadata)
- Prioritize SCORING card type
- Include detailed calculation in reasoning_summary

## Error Handling & Resilience

### Retry Strategy

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
```

- 3 attempts total
- Exponential backoff: 2s, 4s, 8s
- Applies to Gemini API calls

### Fallback Strategy

```
Primary Model (gemini-2.0-flash-exp) fails
    ↓
Fallback Model (gemini-1.5-flash)
    ↓
If both fail → HTTP 500 with error details
```

### Graceful Degradation

- **No chunks retrieved**: LLM still generates response with warning card
- **Invalid JSON from LLM**: Parse error logged, HTTP 500 returned
- **FAISS index missing**: Health endpoint shows unhealthy, reindex required
- **API key invalid**: Connection test fails, health endpoint shows unhealthy

## Logging Strategy

### Log Levels

- **INFO**: Request received, chunks retrieved, response generated
- **DEBUG**: Detailed retrieval scores, prompt content, raw LLM responses
- **WARNING**: Fallback triggered, no chunks retrieved, equipment out of spec
- **ERROR**: API failures, parsing errors, validation failures

### Log Destinations

1. **Console (stderr)**: Colorized structured logs for development
2. **File (`logs/biyoR_YYYY-MM-DD.log`)**: Persistent logs with daily rotation

### Critical Logging Points

```python
logger.info(f"[{session_id}] Received rules query")
logger.info(f"[{session_id}] Retrieved {len(chunks)} chunks")
logger.info(f"[{session_id}] Calling Gemini model: {model_name}")
logger.info(f"[{session_id}] Generated {len(cards)} cards in {time_ms}ms")
```

## Security & Performance Considerations

### API Key Management

- Store in `.env` (never commit)
- Validate on startup
- Test connection during health checks

### Rate Limiting

- Google AI Studio: 60 requests/minute (free tier)
- 1500 requests/day (free tier)
- Consider implementing request queue for high load

### Performance Optimization

- **FAISS Index in Memory**: Loaded once at startup, kept in RAM
- **Batch Embedding**: Embed documents in batches during indexing
- **No Async Overhead**: Current Google SDK is sync, no unnecessary async wrappers
- **Metadata Caching**: Documents loaded once, pickled to disk

### Scalability Considerations

Current design is for single-server deployment. For scaling:
- **Horizontal**: Load balance multiple FastAPI instances, shared FAISS index (NFS/S3)
- **Vertical**: FAISS can handle millions of vectors on single machine
- **Distributed**: Consider FAISS GPU index or distributed vector DB (Weaviate, Qdrant)

## Testing Strategy

### Unit Tests

- Pydantic model validation
- Query construction logic
- Chunk retrieval logic
- JSON parsing

### Integration Tests

- End-to-end API calls with mock FAISS index
- Mock Gemini responses
- Error handling paths

### Manual Testing

- Sample rulebook indexing
- Various game situations
- Edge cases (no chunks, invalid equipment, fouls)

## Future Extensions

### Multilingual Support

1. Add rulebooks in Nepali, Hindi, etc.
2. Update prompts to respect `language_preference`
3. Gemini natively supports 100+ languages

### Advanced Features

- **Historical Queries**: Store session queries for analytics
- **Personalized Guidance**: Adapt to player skill level
- **Video Analysis Integration**: Accept video clips for automated foul detection
- **Live Game Streaming**: Real-time rule enforcement

### Optimization

- **Semantic Caching**: Cache responses for similar situations
- **Hybrid Search**: Combine vector search with keyword search
- **Fine-tuned Embeddings**: Custom embeddings for Dandi Biyo terminology

---

**Document Version:** 1.0  
**Last Updated:** December 2024  
**For:** BiyoR Development Team
