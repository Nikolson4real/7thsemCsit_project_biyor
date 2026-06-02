"""
BiyoR AI Rules Engine - FastAPI Application
Main entry point for the backend server.
"""

import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.routes import rules, game, chat
from app import __version__


# Configure logging
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level
)
logger.add(
    "logs/biyoR_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Handles initialization of RAG pipeline and LLM client.
    """
    # Startup
    logger.info("=" * 60)
    logger.info("BiyoR AI Rules Engine Starting...")
    logger.info(f"Version: {__version__}")
    logger.info(f"API Version: {settings.api_version}")
    logger.info("=" * 60)
    
    try:
        # Initialize dependencies
        rules.initialize_dependencies()
        
        # Set dependencies for game routes
        game.set_dependencies(rules.rag_pipeline, rules.llm_client)
        
        # Initialize chat referee (no dependencies needed - uses Groq directly)
        if settings.groq_api_key:
            from app.chat_referee import get_chat_referee
            chat_referee = get_chat_referee()
            logger.info(f"Chat referee initialized with model: {chat_referee.model}")
        else:
            logger.warning("GROQ_API_KEY not set - chat referee disabled")
        
        logger.info("Application started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down BiyoR AI Rules Engine...")


# Create FastAPI app
app = FastAPI(
    title="BiyoR AI Rules Engine",
    description="Backend RAG system for Dandi Biyo AR mobile app - provides real-time rules, guidance, and scoring",
    version=__version__,
    lifespan=lifespan,
    docs_url=f"/api/{settings.api_version}/docs",
    redoc_url=f"/api/{settings.api_version}/redoc",
    openapi_url=f"/api/{settings.api_version}/openapi.json"
)


# Configure CORS for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions globally."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": str(exc) if settings.log_level == "DEBUG" else None
            }
        }
    )


# Include routers
app.include_router(rules.router)
app.include_router(game.router)
app.include_router(chat.router, prefix=f"/api/{settings.api_version}/chat", tags=["Chat Referee"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "BiyoR AI Rules Engine",
        "version": __version__,
        "description": "Backend RAG system for Dandi Biyo AR mobile app",
        "docs_url": f"/api/{settings.api_version}/docs",
        "status": "operational"
    }


# Legacy health endpoint (in addition to /api/v1/rules/health)
@app.get("/health")
async def simple_health():
    """Simple health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting development server...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )
