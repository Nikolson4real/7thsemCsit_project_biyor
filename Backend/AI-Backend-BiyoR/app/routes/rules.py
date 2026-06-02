"""
API routes for BiyoR AI Rules Engine.
Handles rules queries, reindexing, and health checks.
"""

import time
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from loguru import logger

from app.models import (
    RulesQueryRequest,
    RulesQueryResponse,
    ReindexRequest,
    ReindexResponse,
    HealthResponse,
    ErrorResponse,
    ErrorDetail,
    InstructionCard,
    ModelMetadata,
    RuleReference
)
from app.rag_pipeline import DandiBiyoRAGPipeline
from app.llm_client import GeminiRulesLLM
from app.config import settings


# Create router
router = APIRouter(prefix=f"/api/{settings.api_version}/rules", tags=["rules"])

# Global instances (will be injected via dependencies)
rag_pipeline: DandiBiyoRAGPipeline = None
llm_client: GeminiRulesLLM = None


def get_rag_pipeline() -> DandiBiyoRAGPipeline:
    """Dependency injection for RAG pipeline."""
    if rag_pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG pipeline not initialized"
        )
    return rag_pipeline


def get_llm_client() -> GeminiRulesLLM:
    """Dependency injection for LLM client."""
    if llm_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM client not initialized"
        )
    return llm_client


def _build_response_schema() -> Dict[str, Any]:
    """
    Build the JSON schema that Gemini should follow for responses.
    This defines the card-based structure for AR display.
    """
    return {
        "type": "object",
        "properties": {
            "cards": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "type": {
                            "type": "string",
                            "enum": ["RULE", "EXPLANATION", "ACTION_STEP", "WARNING", "TIP", "SCORING"]
                        },
                        "priority": {"type": "integer", "minimum": 1, "maximum": 10},
                        "body": {"type": "string"},
                        "reasoning_summary": {"type": "string"},
                        "related_rule_refs": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "source": {"type": "string"},
                                    "section": {"type": "string"},
                                    "page": {"type": "integer"}
                                },
                                "required": ["source", "section"]
                            }
                        },
                        "suggested_ar_visual": {"type": "string"}
                    },
                    "required": ["id", "title", "type", "priority", "body", "reasoning_summary"]
                }
            },
            "overall_summary": {"type": "string"}
        },
        "required": ["cards", "overall_summary"]
    }


@router.post("/query", response_model=RulesQueryResponse)
async def query_rules(
    request: RulesQueryRequest,
    pipeline: DandiBiyoRAGPipeline = Depends(get_rag_pipeline),
    llm: GeminiRulesLLM = Depends(get_llm_client)
) -> RulesQueryResponse:
    """
    Query Dandi Biyo rules for a given game situation.
    
    This endpoint:
    1. Constructs a retrieval query from the situation
    2. Retrieves relevant rule chunks from FAISS
    3. Calls Gemini to generate card-based guidance
    4. Returns structured AR-ready instruction cards
    
    Args:
        request: Game situation and context
        pipeline: RAG pipeline (injected)
        llm: Gemini LLM client (injected)
    
    Returns:
        Structured response with instruction cards
    
    Raises:
        HTTPException: If retrieval or generation fails
    """
    start_time = time.time()
    session_id = request.session_id or f"sess_{int(time.time())}"
    
    logger.info(f"[{session_id}] Received rules query: {request.situation_summary[:100]}...")
    
    try:
        # Build retrieval query from request
        retrieval_query = pipeline.build_retrieval_query(request.model_dump())
        
        # Retrieve relevant rule chunks
        logger.info(f"[{session_id}] Retrieving top-{settings.retrieval_top_k} chunks...")
        retrieved_chunks = pipeline.retrieve(
            query=retrieval_query,
            top_k=settings.retrieval_top_k
        )
        
        if not retrieved_chunks:
            logger.warning(f"[{session_id}] No chunks retrieved from FAISS")
        
        # Prepare situation data for LLM
        situation_data = request.model_dump()
        
        # Get response schema for Gemini
        response_schema = _build_response_schema()
        
        # Generate response using Gemini
        logger.info(f"[{session_id}] Generating response with Gemini...")
        llm_response, model_used = llm.generate_rules_response(
            situation=situation_data,
            retrieved_chunks=retrieved_chunks,
            response_schema=response_schema
        )
        
        # Extract retrieval scores
        retrieval_scores = [chunk.get('retrieval_score', 0.0) for chunk in retrieved_chunks]
        
        # Parse LLM response into structured cards
        cards = []
        for card_data in llm_response.get('cards', []):
            # Convert rule refs to proper model
            rule_refs = [
                RuleReference(**ref) for ref in card_data.get('related_rule_refs', [])
            ]
            
            card = InstructionCard(
                id=card_data['id'],
                title=card_data['title'],
                type=card_data['type'],
                priority=card_data['priority'],
                body=card_data['body'],
                reasoning_summary=card_data['reasoning_summary'],
                related_rule_refs=rule_refs,
                suggested_ar_visual=card_data.get('suggested_ar_visual')
            )
            cards.append(card)
        
        # Build metadata
        processing_time = (time.time() - start_time) * 1000  # milliseconds
        metadata = ModelMetadata(
            model_name=model_used,
            retrieved_chunk_count=len(retrieved_chunks),
            retrieval_scores=retrieval_scores,
            processing_time_ms=processing_time
        )
        
        # Build final response
        response = RulesQueryResponse(
            cards=cards,
            overall_summary=llm_response.get('overall_summary', ''),
            model_metadata=metadata,
            session_id=session_id
        )
        
        logger.info(
            f"[{session_id}] Successfully generated {len(cards)} cards "
            f"in {processing_time:.0f}ms"
        )
        
        return response
        
    except ValueError as e:
        # JSON parsing or validation error
        logger.error(f"[{session_id}] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse LLM response: {str(e)}"
        )
        
    except Exception as e:
        # General error
        logger.error(f"[{session_id}] Error processing query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )


@router.post("/reindex", response_model=ReindexResponse)
async def reindex_rulebooks(
    request: ReindexRequest,
    pipeline: DandiBiyoRAGPipeline = Depends(get_rag_pipeline)
) -> ReindexResponse:
    """
    Rebuild the FAISS index from Dandi Biyo rulebooks.
    
    This is an admin/dev endpoint to refresh the vector store
    when rulebooks are updated or added.
    
    Args:
        request: Reindex configuration
        pipeline: RAG pipeline (injected)
    
    Returns:
        Status and statistics of the reindexing operation
    
    Raises:
        HTTPException: If reindexing fails
    """
    logger.info(f"Reindexing request received (force_rebuild={request.force_rebuild})")
    
    try:
        # Build the index
        result = pipeline.build_index(force_rebuild=request.force_rebuild)
        
        if result['status'] == 'error':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['message']
            )
        
        # Reload the index into memory
        if result['status'] == 'success':
            pipeline.load_index()
        
        response = ReindexResponse(
            success=result['status'] == 'success',
            message=result['message'],
            documents_processed=result['documents_processed'],
            chunks_created=result['chunks_created'],
            index_path=result.get('index_path', str(settings.faiss_index_path))
        )
        
        logger.info(
            f"Reindexing completed: {result['chunks_created']} chunks "
            f"from {result['documents_processed']} documents"
        )
        
        return response
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Error during reindexing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reindexing failed: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check(
    pipeline: DandiBiyoRAGPipeline = Depends(get_rag_pipeline),
    llm: GeminiRulesLLM = Depends(get_llm_client)
) -> HealthResponse:
    """
    Health check endpoint.
    
    Verifies:
    - FAISS index is loaded
    - Gemini API is accessible
    
    Returns:
        Health status and component availability
    """
    logger.info("Health check requested")
    
    # Check FAISS index
    faiss_loaded = pipeline.index is not None and len(pipeline.documents) > 0
    
    # Check Gemini API
    try:
        gemini_accessible = llm.test_connection()
    except Exception as e:
        logger.error(f"Gemini API check failed: {str(e)}")
        gemini_accessible = False
    
    # Determine overall status
    overall_status = "healthy" if (faiss_loaded and gemini_accessible) else "unhealthy"
    
    response = HealthResponse(
        status=overall_status,
        version=settings.api_version,
        faiss_index_loaded=faiss_loaded,
        gemini_api_accessible=gemini_accessible
    )
    
    logger.info(f"Health check result: {overall_status}")
    return response


def initialize_dependencies():
    """
    Initialize global dependencies (RAG pipeline and LLM client).
    Called during app startup.
    """
    global rag_pipeline, llm_client
    
    logger.info("Initializing RAG pipeline...")
    rag_pipeline = DandiBiyoRAGPipeline()
    
    # Try to load existing index
    if not rag_pipeline.load_index():
        logger.warning(
            "No existing FAISS index found. "
            "Call POST /api/v1/rules/reindex to build the index."
        )
    
    logger.info("Initializing Gemini LLM client...")
    llm_client = GeminiRulesLLM()
    
    logger.info("Dependencies initialized successfully")
