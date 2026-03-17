#!/usr/bin/env python3
"""
Regulatory Intelligence Agent - Standalone MCP Service
Exposes REST API for regulatory intelligence retrieval.
"""

import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import Optional
import types

# Local imports
from models import AgentRequest, AgentResponse, RegulatoryIntelligence
from query_processor import QueryProcessor
from chroma_client import ChromaRegulatoryClient
from retriever import RegulatoryRetriever
from context_builder import ContextBuilder
from gemini_reasoning import GeminiReasoningLayer
from confidence_scorer import ConfidenceScorer
from data_loader import RegulatoryDataLoader
import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Regulatory Intelligence Agent",
    description="Naive RAG agent for regulatory intelligence using ChromaDB and Gemini",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
chroma_client = None
retriever = None
query_processor = None
context_builder = None
gemini_layer = None
confidence_scorer = None


@app.on_event("startup")
async def startup_event():
    """Initialize all components on startup"""
    global chroma_client, retriever, query_processor, context_builder
    global gemini_layer, confidence_scorer
    
    logger.info("Starting Regulatory Intelligence Agent...")
    
    # Initialize ChromaDB
    try:
        chroma_client = ChromaRegulatoryClient()
        logger.info("ChromaDB client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        raise
    
    # Initialize retriever
    retriever = RegulatoryRetriever(chroma_client)
    
    # Initialize query processor
    query_processor = QueryProcessor(enable_expansion=True)
    
    # Initialize context builder
    context_builder = ContextBuilder()
    
    # Initialize Gemini (will use GOOGLE_API_KEY from environment)
    try:
        GEMINI_API_KEY = "AIzaSyCRKV0HMTVQ_TcPcqCd24noj6XCUG1tEkU"
        gemini_layer = GeminiReasoningLayer(api_key=GEMINI_API_KEY)
        logger.info("Gemini layer initialized")
    except Exception as e:
        logger.warning(f"Gemini initialization failed: {e}")
        logger.warning("Will use fallback extraction mode")
        gemini_layer = None
    
    # Initialize confidence scorer
    confidence_scorer = ConfidenceScorer()
    
    # Check if we need to load sample data
    stats = chroma_client.get_collection_stats()
    if stats.get("total_documents", 0) == 0:
        logger.info("No documents found in ChromaDB. Loading sample data...")
        loader = RegulatoryDataLoader(chroma_client)
        count = loader.load_sample_data()
        logger.info(f"Loaded {count} sample documents")
    
    logger.info("Regulatory Intelligence Agent started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Regulatory Intelligence Agent...")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Regulatory Intelligence Agent",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/stats")
async def get_stats():
    """Get collection statistics"""
    if not chroma_client:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        stats = chroma_client.get_collection_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/regulatory", response_model=AgentResponse)
async def get_regulatory_intelligence(request: AgentRequest):
    """
    Main endpoint: Get regulatory intelligence for a molecule
    """
    logger.info(f"Received request for molecule: {request.molecule}")
    
    try:
        # Step 1: Process query
        query = query_processor.process(request.molecule)
        logger.debug(f"Processed query: {query}")
        
        # Step 2: Retrieve relevant chunks
        chunks = retriever.retrieve(query)
        
        if not chunks:
            logger.warning(f"No regulatory data found for {request.molecule}")
            return AgentResponse(
                success=True,
                data=RegulatoryIntelligence(
                    drug=request.molecule,
                    regulatory_summary="No regulatory data found",
                    confidence=0.0
                )
            )
        
        # Step 3: Build context
        context = context_builder.build_context(chunks)
        
        # Step 4: Synthesize with Gemini (or fallback)
        # Step 4: Synthesize with Gemini (or fallback)
        if gemini_layer:
            try:
                intelligence = gemini_layer.synthesize(
                    drug_name=query.molecule,
                    context=context,
                    chunks=chunks
                )
            except Exception as e:
                logger.error(f"Gemini synthesis failed, using fallback: {e}")
                # Use fallback
                from gemini_reasoning import GeminiReasoningLayer
                intelligence = GeminiReasoningLayer.fallback_extraction(
                    query.molecule, chunks
                )
        else:
            # Fallback to simple extraction
            from gemini_reasoning import GeminiReasoningLayer
            intelligence = GeminiReasoningLayer.fallback_extraction(
                query.molecule, chunks
            )
        # Step 5: Calculate confidence
        confidence = confidence_scorer.calculate(chunks, intelligence)
        intelligence.confidence = confidence
        
        # Add retrieval metadata
        intelligence.retrieval_metadata = {
            "chunks_retrieved": len(chunks),
            "sections_found": list(set(ch.section.value for ch in chunks)),
            "query_expansion": query.expanded_queries[:3]  # First 3 for brevity
        }
        
        logger.info(f"Successfully processed {request.molecule} with confidence {confidence:.2f}")
        
        return AgentResponse(
            success=True,
            data=intelligence
        )
        
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return AgentResponse(
            success=False,
            error=str(e)
        )


@app.post("/reload-data")
async def reload_data(api_key: Optional[str] = None):
    """
    Reload sample regulatory data
    Note: In production, you'd want authentication here
    """
    try:
        loader = RegulatoryDataLoader(chroma_client)
        count = loader.load_sample_data()
        return {"message": f"Loaded {count} documents", "success": True}
    except Exception as e:
        logger.error(f"Failed to reload data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug-gemini")
async def debug_gemini():
    """Debug endpoint to test Gemini API key"""
    if not gemini_layer:
        return {"status": "error", "message": "Gemini not initialized"}
    
    try:
        # Simple test prompt
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="Say 'API key is working' if you can read this"),
                ],
            ),
        ]
        
        config = types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=50,
        )
        
        response_text = ""
        for chunk in gemini_layer.client.models.generate_content_stream(
            model=gemini_layer.model_name,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                response_text += chunk.text
        
        return {
            "status": "success", 
            "message": "Gemini API is working",
            "response": response_text
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Gemini API failed: {str(e)}"
        }

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=config.LOG_LEVEL.lower()
    )