#!/usr/bin/env pwsh
# Setup script for Map Poster API with Docker

Write-Host "Map Poster Generator API - Docker Setup" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# Check if Docker is installed
Write-Host "Checking Docker installation..." -ForegroundColor Yellow
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker is not installed!" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check if Docker Compose is available
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker Compose is not installed!" -ForegroundColor Red
    Write-Host "Please install Docker Compose or use Docker Desktop which includes it." -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Docker is installed" -ForegroundColor Green
Write-Host ""

# Create necessary directories
Write-Host "Creating directories..." -ForegroundColor Yellow
$dirs = @("data", "posters", "cache")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "✓ Created $dir/" -ForegroundColor Green
    } else {
        Write-Host "✓ Directory $dir/ already exists" -ForegroundColor Cyan
    }
}

# Check for fonts and themes directories
if (-not (Test-Path "fonts")) {
    Write-Host "⚠ WARNING: fonts/ directory not found!" -ForegroundColor Yellow
    Write-Host "  The API will use system fonts instead." -ForegroundColor Yellow
}

if (-not (Test-Path "themes")) {
    Write-Host "⚠ WARNING: themes/ directory not found!" -ForegroundColor Yellow
    Write-Host "  Please ensure themes directory exists with .json files." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Building Docker image..." -ForegroundColor Yellow
docker-compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✓ Docker image built successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "To start the API server:" -ForegroundColor Cyan
Write-Host "  docker-compose up -d" -ForegroundColor White
Write-Host ""
Write-Host "To view logs:" -ForegroundColor Cyan
Write-Host "  docker-compose logs -f" -ForegroundColor White
Write-Host ""
Write-Host "To stop the server:" -ForegroundColor Cyan
Write-Host "  docker-compose down" -ForegroundColor White
Write-Host ""
Write-Host "API will be available at:" -ForegroundColor Cyan
Write-Host "  http://localhost:8000" -ForegroundColor White
Write-Host "  http://localhost:8000/docs (Interactive documentation)" -ForegroundColor White
Write-Host ""
Write-Host "For more information, see DOCKER.md" -ForegroundColor Cyan
Write-Host ""

# Ask if user wants to start the service
$response = Read-Host "Do you want to start the service now? (y/n)"
if ($response -eq "y" -or $response -eq "Y") {
    Write-Host ""
    Write-Host "Starting service..." -ForegroundColor Yellow
    docker-compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ Service started successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Waiting for service to be ready..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        # Check health
        try {
            $health = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method Get -TimeoutSec 10
            Write-Host "✓ Service is healthy!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Service Status:" -ForegroundColor Cyan
            Write-Host "  Status: $($health.status)" -ForegroundColor White
            Write-Host "  Themes Available: $($health.themes_available)" -ForegroundColor White
            Write-Host "  Fonts Loaded: $($health.fonts_loaded)" -ForegroundColor White
        } catch {
            Write-Host "⚠ Service started but health check failed." -ForegroundColor Yellow
            Write-Host "  Check logs with: docker-compose logs -f" -ForegroundColor Yellow
        }
    } else {
        Write-Host "ERROR: Failed to start service!" -ForegroundColor Red
        Write-Host "Check logs with: docker-compose logs" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
