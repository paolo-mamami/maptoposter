"""
FastAPI web application for Map Poster Generator.
"""
import asyncio
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from models import (
    PosterRequest,
    GeocodeRequest,
    CoordinatesResponse,
    ThemeInfo,
    ThemesListResponse,
    ThemeResponse,
    JobStatusResponse,
    PosterResponse,
    ErrorResponse,
    HealthResponse,
)
from create_map_poster import (
    get_coordinates,
    get_available_themes,
    load_theme,
    create_poster,
    generate_output_filename,
    FONTS,
    POSTERS_DIR,
)
from database import (
    create_job_db,
    get_job_db,
    update_job_status_db,
    get_all_jobs_db,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Map Poster Generator API",
    description="Generate beautiful city map posters using OpenStreetMap data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_job(request_data: dict) -> str:
    """Create a new job and return job ID."""
    job_id = str(uuid.uuid4())
    create_job_db(job_id, request_data)
    logger.info(f"Created job {job_id}")
    return job_id


def update_job_status(job_id: str, status: str, **kwargs):
    """Update job status and other fields."""
    update_job_status_db(job_id, status, **kwargs)
    logger.info(f"Updated job {job_id}: status={status}")


async def generate_poster_task(job_id: str, request: PosterRequest):
    """Background task to generate poster."""
    try:
        logger.info(f"Starting poster generation for job {job_id}")
        update_job_status(job_id, "processing")
        
        # Get coordinates (either provided or geocoded)
        if request.lat is not None and request.lon is not None:
            coords = (request.lat, request.lon)
            logger.info(f"Using provided coordinates: {coords}")
        else:
            logger.info(f"Geocoding {request.city}, {request.country}")
            coords = await asyncio.to_thread(
                get_coordinates, request.city, request.country
            )
        
        # Load theme
        logger.info(f"Loading theme: {request.theme}")
        theme = await asyncio.to_thread(load_theme, request.theme)
        
        # Generate output filename
        output_file = generate_output_filename(
            request.city, request.theme, request.format
        )
        
        # Create poster (blocking operation, run in thread)
        logger.info(f"Generating poster for {request.city}")
        await asyncio.to_thread(
            create_poster,
            request.city,
            request.country,
            coords,
            request.distance,
            output_file,
            request.format,
            country_label=request.country_label,
        )
        
        # Update job as completed
        update_job_status(
            job_id,
            "completed",
            completed_at=datetime.now(),
            poster_path=output_file,
        )
        logger.info(f"Poster generation completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error generating poster for job {job_id}: {str(e)}", exc_info=True)
        update_job_status(
            job_id,
            "failed",
            completed_at=datetime.now(),
            error=str(e),
        )


@app.get("/", tags=["General"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Map Poster Generator API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint."""
    themes = await asyncio.to_thread(get_available_themes)
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        themes_available=len(themes),
        fonts_loaded=FONTS is not None,
    )


@app.post(
    "/api/posters",
    response_model=PosterResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Posters"],
)
async def create_poster_endpoint(
    request: PosterRequest,
    background_tasks: BackgroundTasks,
):
    """
    Create a new map poster (async operation).
    
    Returns a job ID that can be used to check status and download the poster.
    """
    # Validate coordinates if provided
    if (request.lat is None) != (request.lon is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both latitude and longitude must be provided together",
        )
    
    # Validate theme exists
    available_themes = await asyncio.to_thread(get_available_themes)
    if request.theme not in available_themes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Theme '{request.theme}' not found. Available: {', '.join(available_themes)}",
        )
    
    # Create job
    job_id = create_job(request.model_dump())
    
    # Start background task
    background_tasks.add_task(generate_poster_task, job_id, request)
    
    return PosterResponse(
        job_id=job_id,
        status="pending",
        message="Poster generation started",
        status_url=f"/api/jobs/{job_id}",
    )


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse, tags=["Jobs"])
async def get_job_status(job_id: str):
    """Check the status of a poster generation job."""
    job_obj = get_job_db(job_id)
    if not job_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    
    download_url = None
    if job_obj.status == "completed" and job_obj.poster_path:
        download_url = f"/api/jobs/{job_id}/download"
    
    return JobStatusResponse(
        job_id=job_obj.job_id,
        status=job_obj.status,
        created_at=job_obj.created_at,
        completed_at=job_obj.completed_at,
        error=job_obj.error,
        download_url=download_url,
        poster_path=job_obj.poster_path,
    )


@app.get("/api/jobs/{job_id}/download", tags=["Jobs"])
async def download_poster(job_id: str):
    """Download the generated poster file."""
    job_obj = get_job_db(job_id)
    if not job_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    
    if job_obj.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed yet. Current status: {job_obj.status}",
        )
    
    poster_path = job_obj.poster_path
    if not poster_path or not os.path.exists(poster_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Poster file not found",
        )
    
    # Determine media type based on file extension
    ext = Path(poster_path).suffix.lower()
    media_type_map = {
        ".png": "image/png",
        ".svg": "image/svg+xml",
        ".pdf": "application/pdf",
    }
    media_type = media_type_map.get(ext, "application/octet-stream")
    
    filename = os.path.basename(poster_path)
    return FileResponse(
        poster_path,
        media_type=media_type,
        filename=filename,
    )


@app.get("/api/themes", response_model=ThemesListResponse, tags=["Themes"])
async def list_themes():
    """List all available themes."""
    themes = await asyncio.to_thread(get_available_themes)
    return ThemesListResponse(
        themes=themes,
        count=len(themes),
    )


@app.get("/api/themes/{theme_name}", response_model=ThemeResponse, tags=["Themes"])
async def get_theme_details(theme_name: str):
    """Get details for a specific theme."""
    available_themes = await asyncio.to_thread(get_available_themes)
    if theme_name not in available_themes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Theme '{theme_name}' not found",
        )
    
    theme_data = await asyncio.to_thread(load_theme, theme_name)
    
    theme_info = ThemeInfo(
        name=theme_name,
        display_name=theme_data.get("name", theme_name),
        description=theme_data.get("description"),
        colors=theme_data,
    )
    
    return ThemeResponse(theme=theme_info)


@app.post("/api/geocode", response_model=CoordinatesResponse, tags=["Utilities"])
async def geocode_location(request: GeocodeRequest):
    """
    Geocode a city and country to coordinates.
    
    Useful for getting coordinates before creating a poster.
    """
    try:
        coords = await asyncio.to_thread(
            get_coordinates, request.city, request.country
        )
        return CoordinatesResponse(
            latitude=coords[0],
            longitude=coords[1],
            city=request.city,
            country=request.country,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Geocoding error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Geocoding failed: {str(e)}",
        )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            details={"error": str(exc)},
        ).model_dump(),
    )


# Mount static files for serving posters (optional)
if os.path.exists(POSTERS_DIR):
    app.mount("/posters", StaticFiles(directory=POSTERS_DIR), name="posters")


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Map Poster API server...")
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
