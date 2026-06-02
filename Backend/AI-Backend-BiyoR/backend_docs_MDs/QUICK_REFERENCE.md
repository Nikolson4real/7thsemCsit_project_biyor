# BiyoR AI Rules Engine - Quick Reference

## What This Backend Does

Takes game situations from your Flutter AR app → Returns AR-ready instruction cards based on official Dandi Biyo rules.

```
Flutter App Input          Backend Processing              Flutter App Output
─────────────────         ──────────────────             ──────────────────
"Player hit Biyo      →   1. Embed query          →     [Card 1] Valid Strike
 15m, is this valid?"     2. Search FAISS                [Card 2] Score: 25pts
                          3. Get top-5 rules             [Card 3] Next: Team B
Equipment: 60cm Dandi     4. Call Gemini                 + Overall summary
Surface: Grass            5. Generate cards              + Rule references
Players: 4                6. Return JSON                 + AR visual hints
```

---

## File Purpose Quick Reference

| File | Purpose | Lines |
|------|---------|-------|
| `app/main.py` | FastAPI app, CORS, logging, startup | 120 |
| `app/config.py` | Environment settings, validation | 70 |
| `app/models.py` | Request/response schemas | 500+ |
| `app/llm_client.py` | Gemini API wrapper | 250+ |
| `app/rag_pipeline.py` | FAISS + embeddings + retrieval | 350+ |
| `app/routes/rules.py` | API endpoints (query, reindex, health) | 300+ |
| `requirements.txt` | Dependencies | 25 |
| `.env.example` | Config template | 20 |
| `setup.py` | Setup helper | 150 |
| `test_api.py` | API tests | 200 |
| `README.md` | User docs | 400+ |
| `ARCHITECTURE.md` | Tech docs | 600+ |

---

## Essential Commands

### First-Time Setup
```powershell
# 1. Create venv
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env, add GOOGLE_API_KEY

# 4. Create directories
mkdir data\rulebooks, data\faiss_index, logs

# 5. Add rulebooks to data/rulebooks/
```

### Daily Development
```powershell
# Start server
uvicorn app.main:app --reload

# View docs (in browser)
http://localhost:8000/api/v1/docs

# Run tests
python test_api.py
```

### Rebuilding Index
```powershell
# After adding/updating rulebooks
$body = @{ force_rebuild = $true } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/rules/reindex" -Method Post -Body $body -ContentType "application/json"
```

---

## API Endpoints

### 1. POST /api/v1/rules/query
**Purpose:** Get rules and guidance for a game situation

**Input:**
```json
{
  "situation_summary": "Player A struck Biyo, landed 15m away",
  "equipment_dimensions": {
    "dandi_length_cm": 60,
    "biyo_length_cm": 8
  },
  "ground_description": {
    "surface_type": "grass",
    "field_length_m": 30
  },
  "num_players_available": 4,
  "game_phase": "scoring"
}
```

**Output:**
```json
{
  "cards": [
    {
      "id": "card_1",
      "title": "Valid Strike Confirmed",
      "type": "RULE",
      "priority": 1,
      "body": "The strike is valid...",
      "related_rule_refs": [{"source": "...", "section": "4.2.2"}]
    }
  ],
  "overall_summary": "Award 25 points to Team A",
  "model_metadata": {...}
}
```

### 2. POST /api/v1/rules/reindex
**Purpose:** Rebuild FAISS index from rulebooks

**Input:**
```json
{"force_rebuild": true}
```

**Output:**
```json
{
  "success": true,
  "documents_processed": 1,
  "chunks_created": 47
}
```

### 3. GET /api/v1/rules/health
**Purpose:** Check if backend is ready

**Output:**
```json
{
  "status": "healthy",
  "faiss_index_loaded": true,
  "gemini_api_accessible": true
}
```

---

## Configuration (.env)

```bash
# Required
GOOGLE_API_KEY=your_key_here

# Optional (defaults shown)
GEMINI_PRIMARY_MODEL=gemini-2.0-flash-exp
GEMINI_FALLBACK_MODEL=gemini-1.5-flash
GOOGLE_EMBEDDINGS_MODEL=models/text-embedding-004

RETRIEVAL_TOP_K=5
CHUNK_SIZE=600
CHUNK_OVERLAP=100
LLM_TEMPERATURE=0.1
```

---

## Understanding Card Types

| Type | Purpose | Example |
|------|---------|---------|
| `RULE` | Core rule application | "Valid strike requires Biyo to be airborne" |
| `SCORING` | Score calculation | "Distance: 15m ÷ 0.6m = 25 points" |
| `ACTION_STEP` | What to do next | "Record score, Team B's turn" |
| `WARNING` | Foul or caution | "Dandi touched ground - invalid strike" |
| `TIP` | Helpful advice | "Aim for 45° angle for maximum distance" |
| `EXPLANATION` | Rule clarification | "Anchor circle is where Biyo is struck from" |

---

## Common Issues & Fixes

### "RAG pipeline not initialized"
**Cause:** Server startup failed  
**Fix:** Check logs/, verify .env has GOOGLE_API_KEY

### "No chunks retrieved from FAISS"
**Cause:** Index not built  
**Fix:** POST /api/v1/rules/reindex with force_rebuild: true

### "Failed to parse LLM response as JSON"
**Cause:** Gemini returned non-JSON  
**Fix:** Lower LLM_TEMPERATURE to 0.0-0.2

### "Gemini API connection test failed"
**Cause:** Invalid API key or quota exceeded  
**Fix:** Verify GOOGLE_API_KEY in .env, check Google AI Studio quotas

### "FAISS dimension mismatch"
**Cause:** Changed embeddings model  
**Fix:** Delete data/faiss_index/, rebuild index

---

## Response Time Breakdown

| Operation | Typical Time |
|-----------|--------------|
| Query embedding | 50-100ms |
| FAISS retrieval | 10-50ms |
| Gemini API call | 1-3 seconds |
| JSON parsing | <10ms |
| **Total** | **1.5-3.5 seconds** |

---

## Example Flutter Integration

```dart
// Flutter service class
class BiyoRBackendService {
  final String baseUrl = "http://your-server:8000";
  
  Future<List<InstructionCard>> queryRules({
    required String situation,
    required Equipment equipment,
    required GroundInfo ground,
  }) async {
    final response = await http.post(
      Uri.parse("$baseUrl/api/v1/rules/query"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "situation_summary": situation,
        "equipment_dimensions": equipment.toJson(),
        "ground_description": ground.toJson(),
        // ... other fields
      }),
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return (data['cards'] as List)
          .map((card) => InstructionCard.fromJson(card))
          .toList();
    }
    throw Exception('Failed to query rules');
  }
}
```

---

## Deployment Checklist

- [ ] Update CORS origins in `app/main.py` (restrict to your Flutter app domain)
- [ ] Set `LOG_LEVEL=WARNING` in production .env
- [ ] Add authentication middleware
- [ ] Implement rate limiting
- [ ] Set up monitoring (health checks, metrics)
- [ ] Configure HTTPS/SSL
- [ ] Use production ASGI server (gunicorn + uvicorn workers)
- [ ] Set up log aggregation
- [ ] Configure firewall (allow only necessary ports)
- [ ] Backup FAISS index regularly

---

## Key Documentation

- **README.md** - User guide, installation, API docs
- **ARCHITECTURE.md** - Technical deep-dive, design decisions
- **IMPLEMENTATION_SUMMARY.md** - What was built, verification
- **This file** - Quick reference for daily use

---

## Pro Tips

1. **Testing Prompts:** Use `/api/v1/docs` Swagger UI to test queries interactively
2. **Debugging:** Set `LOG_LEVEL=DEBUG` to see full prompts and LLM responses
3. **Performance:** Reduce `RETRIEVAL_TOP_K` to 3 for faster responses
4. **Accuracy:** Increase `RETRIEVAL_TOP_K` to 7-10 for more comprehensive answers
5. **Consistency:** Keep `LLM_TEMPERATURE` at 0.1 or lower for deterministic rules
6. **Multilingual:** Add rulebooks in target language, Gemini handles translation

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────┐
│                  Flutter Mobile App                      │
│         (Sends game situation, equipment, field)         │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP POST
                         ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Routes (rules.py)                               │  │
│  │  - Validate request                              │  │
│  │  - Build retrieval query                         │  │
│  └──────────────┬───────────────────────────────────┘  │
│                 │                                        │
│                 ▼                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  RAG Pipeline (rag_pipeline.py)                  │  │
│  │  - Embed query (Google AI Studio)                │  │
│  │  - Search FAISS index (top-5 chunks)             │  │
│  └──────────────┬───────────────────────────────────┘  │
│                 │                                        │
│                 ▼                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  LLM Client (llm_client.py)                      │  │
│  │  - Build prompt with chunks                      │  │
│  │  - Call Gemini (Google AI Studio)                │  │
│  │  - Parse JSON response                           │  │
│  └──────────────┬───────────────────────────────────┘  │
│                 │                                        │
└─────────────────┼────────────────────────────────────────┘
                  │
                  ▼
        ┌──────────────────┐
        │   JSON Response   │
        │   - Cards array   │
        │   - Summary       │
        │   - Metadata      │
        └──────────────────┘
```

---

**Questions?** Check README.md for detailed docs or ARCHITECTURE.md for technical details.

**Ready to build!**
