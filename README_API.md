# Map Poster Generator API

A FastAPI-based web service for generating beautiful city map posters using OpenStreetMap data.

## Features

- **RESTful API** for poster generation
- **Asynchronous job processing** with SQLite database storage
- **Multiple output formats**: PNG, SVG, PDF
- **Coordinate support**: Use lat/lon or geocode city/country
- **17+ themes** including noir, blueprint, sunset, and more
- **Docker support** with docker-compose for easy deployment
- **Persistent storage** for jobs, posters, and cache

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Setup and build
.\setup_docker.ps1

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Test the API
.\test_api.ps1
```

See [DOCKER.md](DOCKER.md) for detailed Docker deployment guide.

### Option 2: Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the API server:
```bash
python api.py
```

Or using uvicorn directly:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### General

#### `GET /`
Root endpoint with API information.

**Response:**
```json
{
  "name": "Map Poster Generator API",
  "version": "1.0.0",
  "documentation": "/docs",
  "health": "/api/health"
}
```

#### `GET /api/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "themes_available": 17,
  "fonts_loaded": true
}
```

---

### Posters

#### `POST /api/posters`
Create a new map poster (asynchronous operation).

**Request Body:**
```json
{
  "city": "Paris",
  "country": "France",
  "lat": 48.8566,
  "lon": 2.3522,
  "theme": "noir",
  "distance": 15000,
  "format": "png",
  "country_label": "FRANCE"
}
```

**Parameters:**
- `city` (string, required): City name for the poster text
- `country` (string, required): Country name for the poster text
- `lat` (float, optional): Latitude coordinate (-90 to 90)
- `lon` (float, optional): Longitude coordinate (-180 to 180)
- `theme` (string, optional): Theme name (default: "feature_based")
- `distance` (integer, optional): Map radius in meters (1000-50000, default: 29000)
- `format` (string, optional): Output format - "png", "svg", or "pdf" (default: "png")
- `country_label` (string, optional): Override country text on poster

**Note:** If `lat` and `lon` are not provided, the API will geocode the city and country.

**Response (202 Accepted):**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "message": "Poster generation started",
  "status_url": "/api/jobs/123e4567-e89b-12d3-a456-426614174000"
}
```

**Example with curl:**
```bash
curl -X POST "http://localhost:8000/api/posters" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "New York",
    "country": "USA",
    "theme": "midnight_blue",
    "distance": 12000
  }'
```

**Example with coordinates:**
```bash
curl -X POST "http://localhost:8000/api/posters" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Tokyo",
    "country": "Japan",
    "lat": 35.6762,
    "lon": 139.6503,
    "theme": "japanese_ink",
    "distance": 15000,
    "format": "pdf"
  }'
```

---

### Jobs

#### `GET /api/jobs/{job_id}`
Check the status of a poster generation job.

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "created_at": "2026-01-21T10:30:00",
  "completed_at": "2026-01-21T10:31:45",
  "error": null,
  "download_url": "/api/jobs/123e4567-e89b-12d3-a456-426614174000/download",
  "poster_path": "posters/paris_noir_20260121_103145.png"
}
```

**Status values:**
- `pending`: Job is queued
- `processing`: Poster is being generated
- `completed`: Poster is ready for download
- `failed`: An error occurred

**Example:**
```bash
curl "http://localhost:8000/api/jobs/123e4567-e89b-12d3-a456-426614174000"
```

#### `GET /api/jobs/{job_id}/download`
Download the generated poster file.

**Response:** Binary file (PNG, SVG, or PDF)

**Example:**
```bash
curl -O -J "http://localhost:8000/api/jobs/123e4567-e89b-12d3-a456-426614174000/download"
```

Or with wget:
```bash
wget --content-disposition "http://localhost:8000/api/jobs/123e4567-e89b-12d3-a456-426614174000/download"
```

---

### Themes

#### `GET /api/themes`
List all available themes.

**Response:**
```json
{
  "themes": [
    "autumn",
    "blueprint",
    "contrast_zones",
    "feature_based",
    "midnight_blue",
    "noir",
    "sunset"
  ],
  "count": 7
}
```

**Example:**
```bash
curl "http://localhost:8000/api/themes"
```

#### `GET /api/themes/{theme_name}`
Get details for a specific theme.

**Response:**
```json
{
  "theme": {
    "name": "noir",
    "display_name": "Film Noir",
    "description": "High contrast black and white theme inspired by classic film noir",
    "colors": {
      "bg": "#FFFFFF",
      "text": "#000000",
      "water": "#E0E0E0",
      "parks": "#F5F5F5",
      "road_motorway": "#000000",
      "road_primary": "#1A1A1A",
      "road_secondary": "#333333",
      "road_tertiary": "#4D4D4D",
      "road_residential": "#666666",
      "road_default": "#808080",
      "gradient_color": "#FFFFFF"
    }
  }
}
```

**Example:**
```bash
curl "http://localhost:8000/api/themes/noir"
```

---

### Utilities

#### `POST /api/geocode`
Geocode a city and country to coordinates.

**Request Body:**
```json
{
  "city": "London",
  "country": "United Kingdom"
}
```

**Response:**
```json
{
  "latitude": 51.5074,
  "longitude": -0.1278,
  "city": "London",
  "country": "United Kingdom",
  "address": "London, Greater London, England, United Kingdom"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/geocode" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Barcelona",
    "country": "Spain"
  }'
```

---

## Complete Workflow Example

### 1. Check available themes
```bash
curl "http://localhost:8000/api/themes"
```

### 2. Get coordinates (optional)
```bash
curl -X POST "http://localhost:8000/api/geocode" \
  -H "Content-Type: application/json" \
  -d '{"city": "Paris", "country": "France"}'
```

### 3. Create a poster
```bash
curl -X POST "http://localhost:8000/api/posters" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Paris",
    "country": "France",
    "lat": 48.8566,
    "lon": 2.3522,
    "theme": "pastel_dream",
    "distance": 10000,
    "format": "png"
  }'
```

**Response:**
```json
{
  "job_id": "abc123...",
  "status": "pending",
  "message": "Poster generation started",
  "status_url": "/api/jobs/abc123..."
}
```

### 4. Check job status
```bash
curl "http://localhost:8000/api/jobs/abc123..."
```

### 5. Download poster when ready
```bash
curl -O -J "http://localhost:8000/api/jobs/abc123.../download"
```

---

## Python Client Example

```python
import requests
import time

# API base URL
BASE_URL = "http://localhost:8000"

# Create a poster
response = requests.post(
    f"{BASE_URL}/api/posters",
    json={
        "city": "Tokyo",
        "country": "Japan",
        "theme": "japanese_ink",
        "distance": 15000,
        "format": "png"
    }
)

job = response.json()
job_id = job["job_id"]
print(f"Job created: {job_id}")

# Poll for completion
while True:
    status_response = requests.get(f"{BASE_URL}/api/jobs/{job_id}")
    status = status_response.json()
    
    print(f"Status: {status['status']}")
    
    if status["status"] == "completed":
        # Download the poster
        download_response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/download")
        filename = f"poster_{job_id}.png"
        
        with open(filename, "wb") as f:
            f.write(download_response.content)
        
        print(f"Poster saved to {filename}")
        break
    
    elif status["status"] == "failed":
        print(f"Error: {status['error']}")
        break
    
    time.sleep(5)  # Wait 5 seconds before checking again
```

---

## JavaScript/TypeScript Client Example

```javascript
const BASE_URL = "http://localhost:8000";

async function generatePoster() {
  // Create poster
  const createResponse = await fetch(`${BASE_URL}/api/posters`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      city: "Barcelona",
      country: "Spain",
      theme: "warm_beige",
      distance: 8000,
      format: "png"
    })
  });
  
  const job = await createResponse.json();
  console.log(`Job created: ${job.job_id}`);
  
  // Poll for completion
  while (true) {
    const statusResponse = await fetch(`${BASE_URL}/api/jobs/${job.job_id}`);
    const status = await statusResponse.json();
    
    console.log(`Status: ${status.status}`);
    
    if (status.status === "completed") {
      console.log(`Download URL: ${BASE_URL}${status.download_url}`);
      break;
    } else if (status.status === "failed") {
      console.error(`Error: ${status.error}`);
      break;
    }
    
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
}

generatePoster();
```

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "error": "ValidationError",
  "message": "Theme 'invalid_theme' not found",
  "details": {
    "available_themes": ["noir", "blueprint", "sunset"]
  }
}
```

**Common HTTP Status Codes:**
- `200 OK`: Successful request
- `202 Accepted`: Request accepted for async processing
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Configuration

### Environment Variables

- `CACHE_DIR`: Cache directory path (default: "cache")
- `DB_DIR`: Database directory path (default: "data")

### Database

Jobs are stored in a SQLite database (`data/jobs.db`) with the following schema:
- `job_id`: Unique job identifier (UUID)
- `status`: Job status (pending, processing, completed, failed)
- `created_at`: Job creation timestamp
- `completed_at`: Job completion timestamp
- `error`: Error message if failed
- `poster_path`: Path to generated poster file
- `request_data`: Original request parameters (JSON)

The database is automatically created on first run and persists across restarts.

### CORS Configuration

By default, CORS is configured to allow all origins. For production, update the CORS middleware in `api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specify allowed origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## Performance Notes

- Poster generation typically takes 30-90 seconds depending on:
  - Map complexity (city size, street density)
  - Distance parameter (larger radius = more data)
  - Network speed (downloading OSM data)
  - Server resources

- Generated posters are cached in the `posters/` directory
- OpenStreetMap data is cached in the `cache/` directory
- The API respects OSM's rate limits with built-in delays

---

## Production Deployment

### Using Gunicorn with Uvicorn Workers

```bash
gunicorn api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

### Using Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t map-poster-api .
docker run -p 8000:8000 -v $(pwd)/posters:/app/posters map-poster-api
```

### Recommendations for Production

1. **Job Storage**: Replace in-memory job dict with Redis or database
2. **File Cleanup**: Implement TTL-based cleanup for old posters
3. **Authentication**: Add API key authentication
4. **Rate Limiting**: Add rate limiting middleware
5. **Monitoring**: Add logging, metrics, and health checks
6. **Reverse Proxy**: Use nginx or Traefik in front of the API

---

## Troubleshooting

### "Theme not found" error
- Run `curl http://localhost:8000/api/themes` to see available themes
- Ensure the `themes/` directory exists and contains `.json` files

### "Font not found" warning
- Ensure the `fonts/` directory contains Roboto font files
- The API will fall back to system fonts if custom fonts aren't available

### Slow generation
- Reduce the `distance` parameter for faster generation
- First-time generation for a location is slower (downloads OSM data)
- Subsequent requests use cached data

### Job stuck in "processing"
- Check server logs for errors
- Ensure sufficient disk space for poster output
- Verify network connectivity for OSM data downloads

---

## CLI Tool

The original CLI tool is still available:

```bash
python create_map_poster.py --city "Paris" --country "France" --theme noir
```

See the main README.md for CLI documentation.
