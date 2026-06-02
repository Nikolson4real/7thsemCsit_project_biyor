"""
RAG Pipeline for BiyoR AI Rules Engine.
Handles document ingestion, chunking, FAISS indexing, and retrieval
using Google embeddings from Google AI Studio (NOT Vertex AI).
"""

import os
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import google.generativeai as genai
import faiss
import numpy as np
from loguru import logger

# Document loaders
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    Docx2txtLoader
)

from app.config import settings


class GoogleAIStudioEmbeddings:
    """
    Embeddings wrapper for Google AI Studio.
    Uses Google's text-embedding-004 model via AI Studio API.
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize Google AI Studio embeddings.
        
        Args:
            model_name: Name of the embeddings model (default from settings)
        """
        genai.configure(api_key=settings.google_api_key)
        self.model_name = model_name or settings.google_embeddings_model
        logger.info(f"Initialized Google AI Studio Embeddings: {self.model_name}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents.
        
        Args:
            texts: List of text strings to embed
        
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for i, text in enumerate(texts):
            try:
                result = genai.embed_content(
                    model=self.model_name,
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])
                
                if (i + 1) % 10 == 0:
                    logger.debug(f"Embedded {i + 1}/{len(texts)} documents")
                    
            except Exception as e:
                logger.error(f"Error embedding document {i}: {str(e)}")
                # Use zero vector as fallback
                embeddings.append([0.0] * 768)  # Default dimension for text-embedding-004
        
        logger.info(f"Successfully embedded {len(embeddings)} documents")
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query string.
        
        Args:
            text: Query text to embed
        
        Returns:
            Embedding vector
        """
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
            
        except Exception as e:
            logger.error(f"Error embedding query: {str(e)}")
            raise


class DandiBiyoRAGPipeline:
    """
    RAG pipeline for Dandi Biyo rules retrieval and indexing.
    Uses FAISS for vector storage and Google AI Studio for embeddings.
    """
    
    def __init__(self):
        """Initialize the RAG pipeline with FAISS and Google embeddings."""
        self.embeddings = GoogleAIStudioEmbeddings()
        self.index: Optional[faiss.Index] = None
        self.documents: List[Dict[str, Any]] = []
        self.index_path = settings.faiss_index_path
        self.rulebooks_dir = settings.rulebooks_dir
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        logger.info("Initialized DandiBiyoRAGPipeline")
    
    def _load_document(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Load a single document and return its content with metadata.
        
        Args:
            file_path: Path to the document file
        
        Returns:
            List of document dicts with content and metadata
        """
        suffix = file_path.suffix.lower()
        
        try:
            # Select appropriate loader based on file type
            if suffix == '.pdf':
                loader = PyPDFLoader(str(file_path))
            elif suffix == '.txt':
                loader = TextLoader(str(file_path))
            elif suffix == '.md':
                loader = UnstructuredMarkdownLoader(str(file_path))
            elif suffix == '.docx':
                loader = Docx2txtLoader(str(file_path))
            else:
                logger.warning(f"Unsupported file type: {suffix} for {file_path}")
                return []
            
            # Load document
            docs = loader.load()
            
            # Add source metadata
            for doc in docs:
                doc.metadata['source'] = file_path.name
                doc.metadata['file_path'] = str(file_path)
            
            logger.info(f"Loaded {len(docs)} pages from {file_path.name}")
            return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
            
        except Exception as e:
            logger.error(f"Error loading {file_path}: {str(e)}")
            return []
    
    def _chunk_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Split documents into smaller chunks for better retrieval.
        
        Args:
            documents: List of document dicts
        
        Returns:
            List of chunked document dicts with preserved metadata
        """
        chunked_docs = []
        
        for doc in documents:
            # Split the content
            chunks = self.text_splitter.split_text(doc['content'])
            
            # Create a document for each chunk with metadata
            for i, chunk in enumerate(chunks):
                chunked_doc = {
                    'content': chunk,
                    'metadata': {
                        **doc['metadata'],
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    }
                }
                chunked_docs.append(chunked_doc)
        
        logger.info(f"Created {len(chunked_docs)} chunks from {len(documents)} documents")
        return chunked_docs
    
    def build_index(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """
        Build FAISS index from Dandi Biyo rulebooks in the configured directory.
        
        Args:
            force_rebuild: If True, rebuild even if index exists
        
        Returns:
            Dict with build statistics
        """
        # Check if index already exists
        index_file = self.index_path / "faiss.index"
        metadata_file = self.index_path / "metadata.pkl"
        
        if index_file.exists() and metadata_file.exists() and not force_rebuild:
            logger.info("FAISS index already exists. Use force_rebuild=True to rebuild.")
            return {
                "status": "skipped",
                "message": "Index already exists",
                "documents_processed": 0,
                "chunks_created": 0
            }
        
        # Ensure directories exist
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.rulebooks_dir.mkdir(parents=True, exist_ok=True)
        
        # Load all documents from rulebooks directory
        all_documents = []
        supported_extensions = {'.pdf', '.txt', '.md', '.docx'}
        
        for file_path in self.rulebooks_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                docs = self._load_document(file_path)
                all_documents.extend(docs)
        
        if not all_documents:
            logger.warning(f"No documents found in {self.rulebooks_dir}")
            return {
                "status": "error",
                "message": f"No rulebooks found in {self.rulebooks_dir}",
                "documents_processed": 0,
                "chunks_created": 0
            }
        
        # Chunk documents
        chunked_documents = self._chunk_documents(all_documents)
        
        # Extract text content for embedding
        texts = [doc['content'] for doc in chunked_documents]
        
        # Generate embeddings using Google AI Studio
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.embeddings.embed_documents(texts)
        
        # Convert to numpy array
        embedding_matrix = np.array(embeddings, dtype=np.float32)
        dimension = embedding_matrix.shape[1]
        
        # Create FAISS index
        logger.info(f"Creating FAISS index with dimension {dimension}...")
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embedding_matrix)
        
        # Store documents for later retrieval
        self.documents = chunked_documents
        
        # Save index and metadata
        faiss.write_index(self.index, str(index_file))
        with open(metadata_file, 'wb') as f:
            pickle.dump(self.documents, f)
        
        logger.info(f"FAISS index built and saved to {index_file}")
        
        return {
            "status": "success",
            "message": "Index built successfully",
            "documents_processed": len(all_documents),
            "chunks_created": len(chunked_documents),
            "index_path": str(index_file)
        }
    
    def load_index(self) -> bool:
        """
        Load existing FAISS index from disk.
        
        Returns:
            True if successful, False otherwise
        """
        index_file = self.index_path / "faiss.index"
        metadata_file = self.index_path / "metadata.pkl"
        
        if not index_file.exists() or not metadata_file.exists():
            logger.warning("FAISS index files not found. Run build_index() first.")
            return False
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(index_file))
            
            # Load metadata
            with open(metadata_file, 'rb') as f:
                self.documents = pickle.load(f)
            
            logger.info(f"Loaded FAISS index with {len(self.documents)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error loading FAISS index: {str(e)}")
            return False
    
    def retrieve(
        self,
        query: str,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top-k most relevant rule chunks for a query.
        
        Args:
            query: Query string describing the game situation
            top_k: Number of chunks to retrieve (default from settings)
        
        Returns:
            List of retrieved chunks with content, metadata, and scores
        """
        if self.index is None:
            logger.error("Index not loaded. Call load_index() first.")
            raise ValueError("FAISS index not loaded")
        
        top_k = top_k or settings.retrieval_top_k
        
        # Embed the query
        logger.info(f"Embedding query for retrieval...")
        query_embedding = self.embeddings.embed_query(query)
        query_vector = np.array([query_embedding], dtype=np.float32)
        
        # Search FAISS index
        distances, indices = self.index.search(query_vector, top_k)
        
        # Retrieve documents with scores
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc['retrieval_score'] = float(distance)
                doc['rank'] = i + 1
                results.append(doc)
        
        logger.info(f"Retrieved {len(results)} chunks for query")
        return results
    
    def build_retrieval_query(self, request_data: Dict[str, Any]) -> str:
        """
        Build an optimized retrieval query from the API request.
        
        Args:
            request_data: Request data from RulesQueryRequest
        
        Returns:
            Formatted query string for retrieval
        """
        parts = []
        
        # Add situation summary (most important)
        if 'situation_summary' in request_data:
            parts.append(f"Situation: {request_data['situation_summary']}")
        
        # Add game phase context
        if 'game_phase' in request_data and request_data['game_phase']:
            parts.append(f"Game phase: {request_data['game_phase']}")
        
        # Add equipment context
        if 'equipment_dimensions' in request_data:
            equip = request_data['equipment_dimensions']
            parts.append(
                f"Equipment: Dandi {equip.get('dandi_length_cm')}cm, "
                f"Biyo {equip.get('biyo_length_cm')}cm"
            )
        
        # Add ground context
        if 'ground_description' in request_data:
            ground = request_data['ground_description']
            parts.append(f"Surface: {ground.get('surface_type', 'unknown')}")
            if ground.get('field_length_m'):
                parts.append(f"Field: {ground['field_length_m']}m x {ground.get('field_width_m', '?')}m")
        
        # Add player context
        if 'num_players_available' in request_data:
            parts.append(f"Players: {request_data['num_players_available']}")
        
        query = " | ".join(parts)
        logger.debug(f"Built retrieval query: {query}")
        return query
