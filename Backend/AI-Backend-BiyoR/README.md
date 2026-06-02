# BiyoR AI Rules Engine

Backend RAG (Retrieval-Augmented Generation) system for **BiyoR**, an AR mobile app that modernizes the traditional Nepali sport **Dandi Biyo**.

## Overview

The BiyoR AI Rules Engine is an intelligent backend that powers real-time rule guidance, scoring, and foul detection for Dandi Biyo players. It uses a **2-phase game flow** architecture to handle all game scenarios efficiently.

### What is Dandi Biyo?

Dandi Biyo is a traditional Nepali stick game where players:
1. Place a small wooden piece (Biyo, ~8cm) on an anchor point
2. Strike it with a larger stick (Dandi, ~60cm) to launch it
3. Score points based on how far the Biyo travels
4. Take turns between teams until a winning score is reached

### How BiyoR Helps

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BIYOAR SYSTEM                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Mobile App (Flutter AR)                                                   │
│     │                                                                       │
│     │  • AR camera detects hits                                             │
│     │  • Measures distances                                                 │
│     │  • Displays rules & scores                                            │
│     │                                                                       │
│     ▼                                                                       │
│   AI Rules Engine (This Backend)                                            │
│     │                                                                       │
│     │  • Retrieves relevant rules from rulebook (RAG)                       │
│     │  • Calculates scores based on distance                                │
│     │  • Detects fouls and violations                                       │
│     │  • Answers rule questions in real-time                                │
│     │                                                                       │
│     ▼                                                                       │
│   Players get instant, accurate rulings                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2-Phase Game Flow

The API uses a simplified 2-phase architecture:

### Phase 1: Initial Game (`/api/v1/game/initial`)
Called **once** when starting a new game:
- Returns essential rules briefing
- Provides AR field layout configuration
- Sets up scoring zones for display

### Phase 2: In-Game Queries (`/api/v1/game/query`)
Called **repeatedly** during gameplay:
- **Scoring** - Calculate points when player hits Biyo
- **Foul Check** - Determine if an action is a foul
- **Clarification** - Answer rule questions
- **General** - Any other game-related queries

See [docs/GAME_FLOW.md](docs/GAME_FLOW.md) for detailed flow documentation.

---

## Quick Start

### Prerequisites

- **Google AI Studio API Key** - [Get one free here](https://aistudio.google.com/app/apikey)
- **Option A**: Docker Desktop (recommended)
- **Option B**: Python 3.10+ for manual setup

---

## Setup with Docker (Recommended)

### Step 1: Clone the Repository

```bash
git clone https://github.com/BiyoR-idX/AI-Backend-BiyoR.git
cd AI-Backend-BiyoR
```

### Step 2: Configure Environment

```powershell
# Windows PowerShell
Copy-Item .env.example .env
notepad .env
```

```bash
# Linux/macOS
cp .env.example .env
nano .env
```

Edit the `.env` file and add your API key:
```env
# Required - Your Google AI Studio API Key
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Optional - Defaults are fine for most users
GEMINI_PRIMARY_MODEL=models/gemini-2.5-flash
GEMINI_FALLBACK_MODEL=models/gemini-2.0-flash
GOOGLE_EMBEDDINGS_MODEL=models/text-embedding-004
LOG_LEVEL=INFO
```

### Step 3: Build and Run

```bash
# Build and start the container
docker-compose up --build -d

# Check logs
docker-compose logs -f
```

### Step 4: Build the FAISS Index

Wait ~30 seconds for the container to fully start, then:

```powershell
# Windows PowerShell
$body = '{"force_rebuild": true}'
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/rules/reindex" -Method Post -Body $body -ContentType "application/json"
```

```bash
# Linux/macOS
curl -X POST "http://localhost:8000/api/v1/rules/reindex" \
  -H "Content-Type: application/json" \
  -d '{"force_rebuild": true}'
```

### Step 5: Verify Setup

```powershell
# Windows PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/rules/health"
```

```bash
# Linux/macOS
curl http://localhost:8000/api/v1/rules/health
```

Expected response:
```json
{
  "status": "healthy",
  "faiss_index_loaded": true,
  "gemini_api_accessible": true
}
```

### Step 6: Access API Documentation

Open http://localhost:8000/api/v1/docs in your browser.

**Done! Your backend is running.**

### Docker Commands Reference

```bash
# Start the service
docker-compose up -d

# Stop the service
docker-compose down

# View logs
docker-compose logs -f

# Rebuild after code changes
docker-compose up --build -d

# Remove all data and rebuild
docker-compose down -v
docker-compose up --build -d
```

---

## Manual Setup (Without Docker)

### Step 1: Clone the Repository

```bash
git clone https://github.com/BiyoR-idX/AI-Backend-BiyoR.git
cd AI-Backend-BiyoR
```

### Step 2: Create Virtual Environment

```powershell
# Windows PowerShell
python -m venv env_biyor
.\env_biyor\Scripts\Activate.ps1
```

```bash
# Linux/macOS
python3 -m venv env_biyor
source env_biyor/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment

```powershell
# Windows PowerShell
Copy-Item .env.example .env
notepad .env
```

```bash
# Linux/macOS
cp .env.example .env
nano .env
```

Edit the `.env` file:
```env
# Required
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Optional - Defaults are fine
GEMINI_PRIMARY_MODEL=models/gemini-2.5-flash
GEMINI_FALLBACK_MODEL=models/gemini-2.0-flash
GOOGLE_EMBEDDINGS_MODEL=models/text-embedding-004
FAISS_INDEX_PATH=./data/faiss_index
RULEBOOKS_DIR=./data/rulebooks
LOG_LEVEL=INFO
```

### Step 5: Create Required Directories

```powershell
# Windows PowerShell
New-Item -ItemType Directory -Force -Path data\rulebooks, data\faiss_index, logs
```

```bash
# Linux/macOS
mkdir -p data/rulebooks data/faiss_index logs
```

### Step 6: Start the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Step 7: Build the FAISS Index

In a new terminal (with venv activated):

```powershell
# Windows PowerShell
$body = '{"force_rebuild": true}'
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/rules/reindex" -Method Post -Body $body -ContentType "application/json"
```

```bash
# Linux/macOS
curl -X POST "http://localhost:8000/api/v1/rules/reindex" \
  -H "Content-Type: application/json" \
  -d '{"force_rebuild": true}'
```

### Step 8: Verify Setup

```bash
curl http://localhost:8000/api/v1/rules/health
```

**Done! Your backend is running at http://localhost:8000**

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/game/initial` | POST | Start new game, get rules & field layout |
| `/api/v1/game/query` | POST | In-game queries (scoring, fouls, clarifications) |
| `/api/v1/rules/health` | GET | Health check |
| `/api/v1/rules/reindex` | POST | Rebuild FAISS index from rulebooks |
| `/api/v1/rules/query` | POST | Legacy rules query endpoint |

### Example: Start a New Game

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

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/game/initial" -Method Post -Body $body -ContentType "application/json"
```

### Example: Calculate Score

```powershell
$body = @{
  query_type = "scoring"
  situation_summary = "Player hit the Biyo cleanly"
  estimated_distance_m = 12.0
  session_id = "game_001"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/game/query" -Method Post -Body $body -ContentType "application/json"
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Flutter Mobile App (AR)                     │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP/JSON
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Game Routes (/game/initial, /game/query)               │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                      │
│  ┌────────────────────────▼────────────────────────────────┐   │
│  │  RAG Pipeline                                            │   │
│  │  • Query embedding (text-embedding-004)                  │   │
│  │  • FAISS similarity search                               │   │
│  │  • Context retrieval from rulebooks                      │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                      │
│  ┌────────────────────────▼────────────────────────────────┐   │
│  │  LLM Client                                              │   │
│  │  • Gemini 2.5 Flash (primary)                           │   │
│  │  • Gemini 2.0 Flash (fallback)                          │   │
│  │  • JSON response generation                              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | File | Description |
|-----------|------|-------------|
| RAG Pipeline | `app/rag_pipeline.py` | Document ingestion, FAISS indexing, retrieval |
| LLM Client | `app/llm_client.py` | Gemini API wrapper with retry logic |
| Game Routes | `app/routes/game.py` | 2-phase game flow endpoints |
| Models | `app/models.py` | Pydantic request/response schemas |
| Config | `app/config.py` | Environment configuration |

---

## Tech Stack

- **Framework**: FastAPI
- **Vector Store**: FAISS (CPU)
- **Embeddings**: Google AI Studio `text-embedding-004`
- **LLM**: Gemini 2.5 Flash / 2.0 Flash
- **Document Processing**: PyPDF2, python-docx, markdown
- **Validation**: Pydantic v2
- **Logging**: Loguru

---

## Project Structure

```
AI-Backend-BiyoR/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry
│   ├── config.py            # Environment configuration
│   ├── models.py            # Pydantic schemas
│   ├── rag_pipeline.py      # RAG + FAISS logic
│   ├── llm_client.py        # Gemini API client
│   └── routes/
│       ├── game.py          # Game flow endpoints
│       └── rules.py         # Legacy endpoints
├── data/
│   ├── rulebooks/           # Dandi Biyo rulebook files
│   └── faiss_index/         # Generated FAISS index
├── docs/
│   └── GAME_FLOW.md         # Detailed game flow documentation
├── logs/                    # Application logs
├── .env.example             # Environment template
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # Docker compose configuration
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

---

## Testing

Run the comprehensive test script:

```bash
# Ensure server is running first
python test_game_flow.py
```

This tests:
- Health endpoint
- Initial game setup
- Scoring queries
- Foul checks
- Rule clarifications

---

## Documentation

- **[docs/GAME_FLOW.md](docs/GAME_FLOW.md)** - Complete game flow logic and frontend integration guide
- **[API Docs](http://localhost:8000/api/v1/docs)** - Interactive Swagger documentation (when server is running)

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `FAISS index not loaded` | Run the reindex endpoint to build the index |
| `Gemini API 429 error` | API quota exceeded, wait or upgrade plan |
| `Connection refused` | Ensure server is running on port 8000 |
| `Module not found` | Activate virtual environment and install requirements |

### Logs

Check logs for detailed error information:
```bash
# Docker
docker-compose logs -f

# Manual setup
cat logs/biyoR_*.log
```

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## Team

**BiyoR-idX** - Modernizing traditional Nepali sports with AR technology.

