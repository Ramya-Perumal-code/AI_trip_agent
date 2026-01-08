# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel, Field

# from llm_agent import TravelResearchAgent


# class FinalResponsePayload(BaseModel):
#     content: str = Field(..., description="Aggregated notes or retrieved context")
#     user_query: str | None = Field(
#         default=None,
#         description="Original end-user question for additional context",
#     )


# class AdditionalInfoPayload(BaseModel):
#     query: str = Field(..., min_length=3, description="Topic to research")


# class FinalResponseResult(BaseModel):
#     response: str


# class AdditionalInfoResult(BaseModel):
#     info: str


# app = FastAPI(
#     title="Trip Agent API",
#     description="HTTP interface that exposes the internal LLM agents to the frontend",
#     version="0.1.0",
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# @app.get("/health", summary="Service health probe")
# def health_check() -> dict[str, str]:
#     """Lightweight readiness / liveness probe for deployments."""
#     return {"status": "ok"}


# @app.post(
#     "/final-response",
#     response_model=FinalResponseResult,
#     summary="RunTravelResearchAgent",
# )
# def generate_final_response(payload: FinalResponsePayload) -> FinalResponseResult:
#     """

#     Invoke `FinalResponseAgent` to synthesize a final answer for the UI.
#     """
#     try:
#         response_text =TravelResearchAgent(
#             content=payload.content,
#             user_query=payload.user_query or "",
#         )
#         if not response_text:
#             raise HTTPException(
#                 status_code=502,
#                 detail="FinalResponseAgent returned empty output.",
#             )
#         return FinalResponseResult(response=response_text)
#     except HTTPException:
#         raise
#     except Exception as exc:  # pragma: no cover - defensive guard
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to generate final response: {exc}",
#         ) from exc


# @app.post(
#     "/additional-info",
#     response_model=AdditionalInfoResult,
#     summary="Run AdditionalInfoAgent",
# )
# def gather_additional_info(payload: AdditionalInfoPayload) -> AdditionalInfoResult:
#     """
#     Invoke `AdditionalInfoAgent` to perform RAG + web searches for the topic.
#     """
#     try:
#         info_text = AdditionalInfoAgent(query=payload.query)
#         if not info_text:
#             raise HTTPException(
#                 status_code=502,
#                 detail="AdditionalInfoAgent returned empty output.",
#             )
#         return AdditionalInfoResult(info=info_text)
#     except HTTPException:
#         raise
#     except Exception as exc:  # pragma: no cover - defensive guard
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to gather additional info: {exc}",
#         ) from exc


# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)


"""
FastAPI application for Trip Agent - Travel and Trip Information API

This module provides REST API endpoints to interact with the LLM agents
for trip planning, travel information, and attraction details.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import logging

# Import agents from llm_agent
from llm_agent import TravelResearchAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Trip Agent API",
    description="API for trip analysis and additional information using LLM agents",
    version="1.0.0"
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response Models ---

class FinalResponseRequest(BaseModel):
    """Request model for Final Response Agent endpoint"""
    content: Optional[str] = Field(default="", description="The gathered information/content to synthesize into a final response (optional - agent can gather info using tools)")
    user_query: Optional[str] = Field(default="", description="The original user query (required if content is empty)")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Las Vegas Strip is a famous boulevard with many attractions, hotels, and entertainment venues. It's approximately 4.2 miles long.",
                "user_query": "about San Diego Zoo Day Pass?"
            }
        }


class FinalResponseResponse(BaseModel):
    """Response model for Final Response Agent endpoint"""
    success: bool = Field(..., description="Whether the request was successful")
    response: str = Field(..., description="The generated final response")
    message: Optional[str] = Field(default=None, description="Additional message or status information")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "response": "San Diego Zoo offers day passes with access to various exhibits and attractions...",
                "message": "Final response generated successfully"
            }
        }


class AdditionalInfoRequest(BaseModel):
    """Request model for Additional Info Agent endpoint"""
    query: str = Field(..., description="The travel/trip-related query", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "query": "about San Diego Zoo Day Pass"
            }
        }


class AdditionalInfoResponse(BaseModel):
    """Response model for Additional Info Agent endpoint"""
    success: bool = Field(..., description="Whether the request was successful")
    info: str = Field(..., description="The comprehensive information gathered")
    query: str = Field(..., description="The original query that was analyzed")
    message: Optional[str] = Field(default=None, description="Additional message or status information")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "info": "San Diego Zoo offers day passes with access to various exhibits...",
                "query": "about San Diego Zoo Day Pass",
                "message": "Additional information gathered successfully"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Health check message")
    version: str = Field(default="1.0.0", description="API version")


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(default=False, description="Request failed")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")


# --- API Endpoints ---

@app.get("/", tags=["General"])
async def root():
    """
    Root endpoint - API information
    """
    return {
        "message": "Trip Agent API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "final_response": "/api/v1/final-response",
            "additional_info": "/api/v1/additional-info"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """
    Health check endpoint to verify API is running
    
    Returns:
        HealthResponse: Service status and health information
    """
    try:
        return HealthResponse(
            status="healthy",
            message="API is running and ready to process requests",
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is unavailable"
        )


@app.post(
    "/api/v1/final-response",
    response_model=FinalResponseResponse,
    status_code=status.HTTP_200_OK,
    tags=["Agents"],
    summary="Generate Final Response",
    description="Synthesizes gathered information into a comprehensive final response using theTravelResearchAgent"
)
async def generate_final_response(request: FinalResponseRequest):
    """
    Generate a comprehensive final response based on gathered information.
    
    This endpoint uses theTravelResearchAgent to synthesize all collected data
    into a clear, user-friendly answer. The agent can use tools to gather additional
    information if needed.
    
    Args:
        request: FinalResponseRequest containing:
            - content: Optional gathered information to synthesize (if empty, agent will gather info using tools)
            - user_query: The user query (required if content is empty)
    
    Returns:
        FinalResponseResponse: Contains the generated final response
    
    Raises:
        HTTPException: If the agent fails to generate a response
    """
    try:
        # Validate that either content or user_query is provided
        if not request.content and not request.user_query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'content' or 'user_query' must be provided"
            )
        
        logger.info(f"Received final response request with content length: {len(request.content or '')}, user_query: {request.user_query[:50] if request.user_query else 'None'}...")
        
        # Call theTravelResearchAgent
        final_response = TravelResearchAgent(
            query=request.user_query or ""
        )
        
        if not final_response or not final_response.strip():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Agent failed to generate a response"
            )
        
        logger.info("Final response generated successfully")
        
        return FinalResponseResponse(
            success=True,
            response=final_response,
            message="Final response generated successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating final response: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@app.post(
    "/api/v1/additional-info",
    response_model=AdditionalInfoResponse,
    status_code=status.HTTP_200_OK,
    tags=["Agents"],
    summary="Gather Additional Information",
    description="Gathers comprehensive travel and trip information using the AdditionalInfoAgent with tool calling"
)
async def gather_additional_info(request: AdditionalInfoRequest):
    """
    Gather additional information about travel, attractions, and trip planning.
    
    This endpoint uses the AdditionalInfoAgent which is specialized in gathering
    comprehensive information about travel, attractions, and trip planning. The agent
    uses LLM with tool calling to search RAG and web for comprehensive travel data.
    
    The agent can:
    - Search the local knowledge base (RAG) for relevant travel and attraction data
    - Search the web for additional current information using DuckDuckGo
    - Gather details about attractions, locations, pricing, hours, reviews, etc.
    
    Args:
        request: AdditionalInfoRequest containing:
            - query: The travel/trip-related query (e.g., "about San Diego Zoo Day Pass")
    
    Returns:
        AdditionalInfoResponse: Contains the comprehensive information gathered
    
    Raises:
        HTTPException: If the agent fails to gather additional information
    """
    try:
        logger.info(f"Received additional info request for query: {request.query}")
        
        # Call the AdditionalInfoAgent
        gathered_info = AdditionalInfoAgent(query=request.query)
        
        if not gathered_info or not gathered_info.strip():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Agent failed to gather additional information"
            )
        
        logger.info("Additional information gathered successfully")
        
        return AdditionalInfoResponse(
            success=True,
            info=gathered_info,
            query=request.query,
            message="Additional information gathered successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error gathering additional info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# --- Error Handlers ---

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return {
        "success": False,
        "error": "Internal server error",
        "detail": str(exc)
    }


# --- Application Startup/Shutdown ---

@app.on_event("startup")
async def startup_event():
    """
    Startup event handler
    """
    logger.info("Trip Agent API is starting up...")
    logger.info("API endpoints are ready to accept requests")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler
    """
    logger.info("Trip Agent API is shutting down...")


# --- Main Entry Point ---

if __name__ == "__main__":
    import uvicorn
    
    # Run the API server
    # Note: Using workers=1 to avoid Qdrant file lock conflicts
    # For production with multiple workers, use Qdrant server instead of local file
    # If you encounter file lock errors, try setting reload=False
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to False if you encounter Qdrant file lock issues
        workers=1,  # Single worker to avoid Qdrant file lock conflicts
        log_level="info"
    )

