# BiyoR AI Backend - Docker Quick Start

## Running with Docker

### Prerequisites
- Docker Desktop installed
- Docker Compose installed
- Google AI Studio API key

### Quick Start

1. **Set up environment variables**
   ```powershell
   # Create .env file
   cp .env.example .env
   
   # Edit .env and add your Google API key
   # GOOGLE_API_KEY=your_actual_key_here
   ```

2. **Ensure rulebooks are in place**
   ```powershell
   # Rulebooks should be in data/rulebooks/
   # A sample rulebook is already included
   ```

3. **Build and run**
   ```powershell
   # Build and start the container
   docker-compose up --build -d
   
   # View logs
   docker-compose logs -f
   ```

4. **Access the API**
   - API Documentation: http://localhost:8000/api/v1/docs
   - Health Check: http://localhost:8000/health

5. **Build FAISS index**
   ```powershell
   # In PowerShell
   $body = @{ force_rebuild = $true } | ConvertTo-Json
   Invoke-RestMethod -Uri "http://localhost:8000/api/v1/rules/reindex" -Method Post -Body $body -ContentType "application/json"
   ```

### Docker Commands

```powershell
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f biyoR-backend

# Restart service
docker-compose restart

# Rebuild after code changes
docker-compose up --build -d

# Remove everything (including volumes)
docker-compose down -v
```

### Environment Variables

All environment variables can be set in `.env` file:

```env
# Required
GOOGLE_API_KEY=your_google_ai_studio_api_key

# Optional (defaults shown)
GEMINI_PRIMARY_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODEL=gemini-2.0-flash-exp
RETRIEVAL_TOP_K=5
LOG_LEVEL=INFO
```

### Volume Mounts

- `./data/rulebooks` → `/app/data/rulebooks` (read-only)
- `faiss_data` volume → `/app/data/faiss_index` (persistent)
- `./logs` → `/app/logs` (logs accessible on host)

### Health Check

The container includes a health check that runs every 30 seconds:
```powershell
# Check container health
docker-compose ps
```

### Troubleshooting

**Container won't start:**
```powershell
# Check logs
docker-compose logs biyoR-backend

# Check if port 8000 is already in use
netstat -ano | findstr :8000
```

**API key issues:**
```powershell
# Verify .env file exists and has correct key
cat .env

# Restart after changing .env
docker-compose down
docker-compose up -d
```

**Rebuild FAISS index:**
```powershell
# The FAISS index persists in a Docker volume
# To rebuild, call the reindex endpoint or delete the volume
docker-compose down -v  # Removes volume
docker-compose up -d    # Recreate everything
```

### Production Deployment

For production, consider:

1. **Use production-ready ASGI server:**
   ```dockerfile
   CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
   ```

2. **Add resource limits in docker-compose.yml:**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 4G
       reservations:
         memory: 2G
   ```

3. **Use Docker secrets for API key:**
   ```yaml
   secrets:
     - google_api_key
   ```

4. **Enable HTTPS with reverse proxy (nginx/traefik)**

---

**Ready to run!**
