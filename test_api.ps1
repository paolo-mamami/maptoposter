#!/usr/bin/env pwsh
# Test script for Map Poster API

$BASE_URL = "http://localhost:8000"

Write-Host "Map Poster API - Test Suite" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green
Write-Host ""

# Test 1: Health Check
Write-Host "Test 1: Health Check" -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "$BASE_URL/api/health" -Method Get
    Write-Host "✓ Health check passed" -ForegroundColor Green
    Write-Host "  Status: $($health.status)" -ForegroundColor White
    Write-Host "  Themes: $($health.themes_available)" -ForegroundColor White
} catch {
    Write-Host "✗ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 2: List Themes
Write-Host "Test 2: List Themes" -ForegroundColor Cyan
try {
    $themes = Invoke-RestMethod -Uri "$BASE_URL/api/themes" -Method Get
    Write-Host "✓ Themes retrieved successfully" -ForegroundColor Green
    Write-Host "  Available themes: $($themes.count)" -ForegroundColor White
    Write-Host "  Themes: $($themes.themes -join ', ')" -ForegroundColor White
} catch {
    Write-Host "✗ Failed to retrieve themes: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Geocode Location
Write-Host "Test 3: Geocode Location" -ForegroundColor Cyan
try {
    $body = @{
        city = "Paris"
        country = "France"
    } | ConvertTo-Json

    $coords = Invoke-RestMethod -Uri "$BASE_URL/api/geocode" -Method Post -Body $body -ContentType "application/json"
    Write-Host "✓ Geocoding successful" -ForegroundColor Green
    Write-Host "  Latitude: $($coords.latitude)" -ForegroundColor White
    Write-Host "  Longitude: $($coords.longitude)" -ForegroundColor White
} catch {
    Write-Host "✗ Geocoding failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 4: Create Poster Job
Write-Host "Test 4: Create Poster Job" -ForegroundColor Cyan
try {
    $posterRequest = @{
        city = "Venice"
        country = "Italy"
        theme = "blueprint"
        distance = 4000
        format = "png"
    } | ConvertTo-Json

    $job = Invoke-RestMethod -Uri "$BASE_URL/api/posters" -Method Post -Body $posterRequest -ContentType "application/json"
    Write-Host "✓ Job created successfully" -ForegroundColor Green
    Write-Host "  Job ID: $($job.job_id)" -ForegroundColor White
    Write-Host "  Status: $($job.status)" -ForegroundColor White
    
    $jobId = $job.job_id
    
    # Test 5: Check Job Status
    Write-Host ""
    Write-Host "Test 5: Check Job Status" -ForegroundColor Cyan
    Write-Host "Waiting for job to complete (this may take 30-90 seconds)..." -ForegroundColor Yellow
    
    $maxAttempts = 30
    $attempt = 0
    $completed = $false
    
    while ($attempt -lt $maxAttempts -and -not $completed) {
        Start-Sleep -Seconds 3
        $attempt++
        
        try {
            $status = Invoke-RestMethod -Uri "$BASE_URL/api/jobs/$jobId" -Method Get
            Write-Host "  Attempt $attempt - Status: $($status.status)" -ForegroundColor Gray
            
            if ($status.status -eq "completed") {
                $completed = $true
                Write-Host "✓ Job completed successfully!" -ForegroundColor Green
                Write-Host "  Poster path: $($status.poster_path)" -ForegroundColor White
                Write-Host "  Download URL: $BASE_URL$($status.download_url)" -ForegroundColor White
                
                # Test 6: Download Poster
                Write-Host ""
                Write-Host "Test 6: Download Poster" -ForegroundColor Cyan
                try {
                    $outputFile = "test_poster.png"
                    Invoke-WebRequest -Uri "$BASE_URL$($status.download_url)" -OutFile $outputFile
                    
                    if (Test-Path $outputFile) {
                        $fileSize = (Get-Item $outputFile).Length
                        Write-Host "✓ Poster downloaded successfully" -ForegroundColor Green
                        Write-Host "  File: $outputFile" -ForegroundColor White
                        Write-Host "  Size: $([math]::Round($fileSize / 1MB, 2)) MB" -ForegroundColor White
                    }
                } catch {
                    Write-Host "✗ Download failed: $($_.Exception.Message)" -ForegroundColor Red
                }
                
            } elseif ($status.status -eq "failed") {
                Write-Host "✗ Job failed: $($status.error)" -ForegroundColor Red
                break
            }
        } catch {
            Write-Host "✗ Status check failed: $($_.Exception.Message)" -ForegroundColor Red
            break
        }
    }
    
    if (-not $completed -and $attempt -eq $maxAttempts) {
        Write-Host "⚠ Job did not complete within timeout period" -ForegroundColor Yellow
        Write-Host "  Job may still be processing. Check status manually:" -ForegroundColor Yellow
        Write-Host "  curl $BASE_URL/api/jobs/$jobId" -ForegroundColor White
    }
    
} catch {
    Write-Host "✗ Failed to create job: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================" -ForegroundColor Green
Write-Host "Test suite completed!" -ForegroundColor Green
Write-Host ""
