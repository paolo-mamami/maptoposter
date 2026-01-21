# Docker Deployment Guide

This guide explains how to deploy the Map Poster Generator API using Docker and Docker Compose.

## Prerequisites

- Docker 20.10+
- Docker Compose 1.29+

## Quick Start

### Using Docker Compose (Recommended)

1. **Build and start the service:**
   ```bash
   docker-compose up -d
   ```

2. **Check the logs:**
   ```bash
   docker-compose logs -f
   ```

3. **Access the API:**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/api/health

4. **Stop the service:**
   ```bash
   docker-compose down
   ```

### Manual Docker Build

1. **Build the image:**
   ```bash
   docker build -t map-poster-api:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name map-poster-api \
     -p 8000:8000 \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/posters:/app/posters \
     -v $(pwd)/cache:/app/cache \
     -v $(pwd)/fonts:/app/fonts:ro \
     -v $(pwd)/themes:/app/themes:ro \
     -e DB_DIR=/app/data \
     -e CACHE_DIR=/app/cache \
     map-poster-api:latest
   ```

## Volume Mounts

The Docker setup uses several volume mounts to persist data:

| Local Path | Container Path | Purpose | Mode |
|------------|---------------|---------|------|
| `./data` | `/app/data` | SQLite database | read-write |
| `./posters` | `/app/posters` | Generated posters | read-write |
| `./cache` | `/app/cache` | OSM data cache | read-write |
| `./fonts` | `/app/fonts` | Font files | read-only |
| `./themes` | `/app/themes` | Theme configs | read-only |

### Create Required Directories

```bash
mkdir -p data posters cache fonts themes
```

## Environment Variables

Configure the API using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_DIR` | `data` | Directory for SQLite database |
| `CACHE_DIR` | `cache` | Directory for OSM data cache |
| `API_HOST` | `0.0.0.0` | API host address |
| `API_PORT` | `8000` | API port number |
| `ALLOWED_ORIGINS` | `*` | CORS allowed origins |

You can create a `.env` file for local development:
```bash
cp .env.example .env
```

## Testing the Deployment

### Health Check

```bash
curl http://localhost:8000/api/health
```

### Create a Poster

```bash
curl -X POST "http://localhost:8000/api/posters" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Paris",
    "country": "France",
    "theme": "noir",
    "distance": 10000
  }'
```

Response:
```json
{
  "job_id": "abc-123-def-456",
  "status": "pending",
  "message": "Poster generation started",
  "status_url": "/api/jobs/abc-123-def-456"
}
```

### Check Job Status

```bash
curl http://localhost:8000/api/jobs/abc-123-def-456
```

### Download Poster

```bash
curl -O -J http://localhost:8000/api/jobs/abc-123-def-456/download
```

## Managing the Container

### View Logs

```bash
# All logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100
```

### Restart the Service

```bash
docker-compose restart
```

### Rebuild After Code Changes

```bash
docker-compose up -d --build
```

### Access Container Shell

```bash
docker-compose exec map-poster-api /bin/bash
```

### Stop and Remove Everything

```bash
# Stop and remove containers
docker-compose down

# Stop, remove containers, and remove volumes
docker-compose down -v

# Stop, remove containers, volumes, and images
docker-compose down -v --rmi all
```

## Production Deployment

### Using a Reverse Proxy (nginx)

Example nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for long-running poster generation
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }
}
```

### HTTPS with Let's Encrypt

```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Obtain certificate
certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

### Resource Limits

Add resource limits to `docker-compose.yml`:

```yaml
services:
  map-poster-api:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Logging Configuration

Add logging to `docker-compose.yml`:

```yaml
services:
  map-poster-api:
    # ... existing config ...
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Backup and Restore

### Backup Database

```bash
# Copy database file
cp data/jobs.db data/jobs.db.backup

# Or use docker cp
docker cp map-poster-api:/app/data/jobs.db ./backup/jobs.db
```

### Backup Posters

```bash
# Tar and compress posters directory
tar -czf posters-backup-$(date +%Y%m%d).tar.gz posters/
```

### Restore Database

```bash
# Copy backup to data directory
cp backup/jobs.db data/jobs.db

# Restart container
docker-compose restart
```

## Troubleshooting

### Container Won't Start

1. Check logs:
   ```bash
   docker-compose logs map-poster-api
   ```

2. Verify directories exist:
   ```bash
   ls -la data posters cache fonts themes
   ```

3. Check permissions:
   ```bash
   chmod -R 755 data posters cache
   ```

### Database Locked Error

```bash
# Stop container
docker-compose down

# Remove database lock file
rm data/jobs.db-shm data/jobs.db-wal

# Restart
docker-compose up -d
```

### Port Already in Use

Change the port in `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"  # Use port 8080 instead
```

### Out of Disk Space

```bash
# Clean up old Docker images
docker system prune -a

# Remove old posters
find posters/ -name "*.png" -mtime +30 -delete

# Clean cache
rm -rf cache/*
```

## Monitoring

### Check Container Health

```bash
docker-compose ps
```

### Monitor Resource Usage

```bash
docker stats map-poster-api
```

### Database Size

```bash
du -h data/jobs.db
```

### Check Job Count

```bash
docker-compose exec map-poster-api python -c "
from database import get_all_jobs_db
jobs = get_all_jobs_db(limit=1000)
print(f'Total jobs: {len(jobs)}')
"
```

## Maintenance

### Clean Old Jobs

```bash
docker-compose exec map-poster-api python -c "
from database import delete_old_jobs_db
deleted = delete_old_jobs_db(days=30)
print(f'Deleted {deleted} old jobs')
"
```

### Clean Old Posters

```bash
# Delete posters older than 30 days
find posters/ -name "*.png" -mtime +30 -delete
find posters/ -name "*.svg" -mtime +30 -delete
find posters/ -name "*.pdf" -mtime +30 -delete
```

## Security Considerations

1. **CORS Configuration**: Update `allow_origins` in `api.py` for production
2. **API Authentication**: Consider adding API key authentication
3. **Rate Limiting**: Implement rate limiting for public deployments
4. **Network Security**: Use a firewall to restrict access
5. **Regular Updates**: Keep Docker images and dependencies updated

## Performance Tuning

### Increase Workers

For production, consider using Gunicorn with multiple workers:

Update `Dockerfile` CMD:
```dockerfile
CMD ["gunicorn", "api:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

Add gunicorn to `requirements.txt`:
```
gunicorn==21.2.0
```

### Enable Caching

The OSM data cache is already enabled. Ensure the cache directory is properly mounted and has sufficient space.

### Database Optimization

For high-volume deployments, consider:
- Using PostgreSQL instead of SQLite
- Adding database indexes
- Implementing job cleanup routines
