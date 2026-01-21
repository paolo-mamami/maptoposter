#!/usr/bin/env pwsh
# Quick start script for the Map Poster API

Write-Host "Map Poster Generator API - Quick Start" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Check if fonts directory exists
if (-not (Test-Path "fonts")) {
    Write-Host "WARNING: fonts/ directory not found!" -ForegroundColor Red
    Write-Host "The API will use system fonts instead." -ForegroundColor Yellow
}

# Check if themes directory exists
if (-not (Test-Path "themes")) {
    Write-Host "WARNING: themes/ directory not found!" -ForegroundColor Red
    Write-Host "Please ensure themes directory exists with .json files." -ForegroundColor Yellow
}

# Create necessary directories
Write-Host "Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "cache" | Out-Null
New-Item -ItemType Directory -Force -Path "posters" | Out-Null

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To start the API server, run:" -ForegroundColor Cyan
Write-Host "  python api.py" -ForegroundColor White
Write-Host ""
Write-Host "Or use uvicorn directly:" -ForegroundColor Cyan
Write-Host "  uvicorn api:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host ""
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Interactive docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
