"""
Pydantic models for the Map Poster API.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime


class PosterRequest(BaseModel):
    """Request model for creating a map poster."""
    city: str = Field(..., min_length=1, max_length=100, description="City name for the poster")
    country: str = Field(..., min_length=1, max_length=100, description="Country name for the poster")
    lat: Optional[float] = Field(None, ge=-90, le=90, description="Latitude (optional, skips geocoding)")
    lon: Optional[float] = Field(None, ge=-180, le=180, description="Longitude (optional, skips geocoding)")
    theme: str = Field(default="feature_based", description="Theme name")
    distance: int = Field(default=29000, ge=1000, le=50000, description="Map radius in meters")
    format: Literal["png", "svg", "pdf"] = Field(default="png", description="Output format")
    country_label: Optional[str] = Field(None, max_length=100, description="Override country text on poster")
    
    @field_validator('lat', 'lon')
    @classmethod
    def validate_coordinates(cls, v, info):
        """Ensure both lat and lon are provided together."""
        # This will be validated in the API endpoint logic
        return v


class GeocodeRequest(BaseModel):
    """Request model for geocoding a location."""
    city: str = Field(..., min_length=1, max_length=100, description="City name")
    country: str = Field(..., min_length=1, max_length=100, description="Country name")


class CoordinatesResponse(BaseModel):
    """Response model for coordinates."""
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    city: str = Field(..., description="City name")
    country: str = Field(..., description="Country name")
    address: Optional[str] = Field(None, description="Full address from geocoder")


class ThemeInfo(BaseModel):
    """Information about a single theme."""
    name: str = Field(..., description="Theme identifier")
    display_name: str = Field(..., description="Human-readable theme name")
    description: Optional[str] = Field(None, description="Theme description")
    colors: dict = Field(default_factory=dict, description="Color scheme")


class ThemesListResponse(BaseModel):
    """Response model for listing themes."""
    themes: list[str] = Field(..., description="List of available theme names")
    count: int = Field(..., description="Number of themes available")


class ThemeResponse(BaseModel):
    """Response model for a single theme."""
    theme: ThemeInfo = Field(..., description="Theme information")


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: str = Field(..., description="Unique job identifier")
    status: Literal["pending", "processing", "completed", "failed"] = Field(..., description="Job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")
    download_url: Optional[str] = Field(None, description="Download URL when completed")
    poster_path: Optional[str] = Field(None, description="File path to generated poster")


class PosterResponse(BaseModel):
    """Response model for poster creation."""
    job_id: str = Field(..., description="Job ID for tracking")
    status: str = Field(..., description="Initial job status")
    message: str = Field(..., description="Status message")
    status_url: str = Field(..., description="URL to check job status")


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    themes_available: int = Field(..., description="Number of themes available")
    fonts_loaded: bool = Field(..., description="Whether fonts are loaded")
