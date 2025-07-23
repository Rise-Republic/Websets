# 📊 Websets Mining Job Tracking & Monitoring Guide

## Overview

This guide provides comprehensive methods for tracking and monitoring mining jobs in the Websets system. Whether you're running jobs via CLI or API, this document covers all available monitoring approaches from real-time logs to database queries.

## 🚀 Running Mining Jobs (Prerequisites)

### Correct Execution Method

**✅ Always run inside Docker container** (has all dependencies):
```bash
docker exec -it websets-app-1 python scripts/run_job.py "Your mining prompt here"
```

**❌ Don't run directly on host** (missing dependencies):
```bash
python scripts/run_job.py "Your prompt"  # This will fail
```

### Container Status Check

Before running jobs, ensure all containers are running:
```bash
docker ps --filter "name=websets"
```

Expected containers:
- `websets-app-1` - Main FastAPI application
- `websets-worker-1` - Celery background worker
- `websets-beat-1` - Celery beat scheduler
- `websets-db-1` - PostgreSQL database
- `websets-redis-1` - Redis cache/queue

## 📈 Real-time Job Monitoring Methods

### 1. Container Logs (Primary Method)

#### Monitor Worker Container (Most Important)
```bash
# Real-time worker logs (where jobs execute)
docker logs websets-worker-1 --tail 20 -f

# Get recent worker logs without following
docker logs websets-worker-1 --tail 50
```

#### Monitor Main Application
```bash
# Real-time app logs
docker logs websets-app-1 --tail 20 -f

# Recent app logs
docker logs websets-app-1 --tail 50
```

#### Monitor All Services
```bash
# All containers simultaneously
docker compose logs -f

# Specific services only
docker compose logs -f app worker beat
```

#### Monitor Beat Scheduler
```bash
# Job scheduling logs
docker logs websets-beat-1 --tail 20 -f
```

### 2. Log Analysis Patterns

#### Job Progress Indicators
Look for these log patterns to track job stages:

```bash
# Job Creation
"Created job {job_id} for user {user_email}"
"Prompt: {your_prompt}"

# Planning Phase
"Planning data mining strategy for: {prompt}"
"Generated plan with {N} estimated URLs"

# URL Discovery
"Discovered {N} prioritized URLs"
"Search engine discovery completed"

# Crawling Phase
"Starting crawl for URL: {url}"
"Crawl completed for {url}: {status}"
"Page content extracted: {data_size} characters"

# Schema Inference
"Inferring schema for extracted data"
"Schema inference completed: {fields}"

# Job Completion
"Job {job_id} completed successfully"
"Data stored: {record_count} records"
```

#### Error Patterns
```bash
# Database Connection Issues
"sqlalchemy.exc.OperationalError"
"connection was closed unexpectedly"

# LLM API Issues
"OpenAI API rate limit exceeded"
"Anthropic API authentication failed"

# Crawling Issues
"Playwright timeout"
"HTTP 403 Forbidden"
"robots.txt disallowed"
```

## 🌐 Web Interface Monitoring

### API Documentation Interface
- **URL**: http://localhost:8000/docs
- **Features**: Interactive API testing, endpoint documentation
- **Usage**: Test API endpoints, view request/response schemas

### Main Application Interface
- **URL**: http://localhost:8000
- **Features**: Web-based job management (if frontend implemented)

### Health Check Endpoints
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed system health
curl http://localhost:8000/health/detailed
```

## 🔐 API-Based Job Tracking

### User Registration & Authentication

#### Register New User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "full_name": "Your Name"
  }'
```

#### Login & Get JWT Token
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepassword123"
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Job Management Endpoints

#### List All Jobs
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "http://localhost:8000/jobs/"
```

#### Get Specific Job Details
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "http://localhost:8000/jobs/{JOB_ID}"
```

#### Create New Job via API
```bash
curl -X POST "http://localhost:8000/jobs/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Your mining prompt here",
    "estimated_urls": 100,
    "complexity": "medium"
  }'
```

#### Cancel Running Job
```bash
curl -X DELETE "http://localhost:8000/jobs/{JOB_ID}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🗄️ Database Direct Monitoring

### Connect to PostgreSQL
```bash
# Connect to database container
docker exec -it websets-db-1 psql -U postgres -d webset_miner
```

### Useful SQL Queries

#### List Recent Jobs
```sql
SELECT 
    id, 
    prompt, 
    status, 
    created_at,
    updated_at
FROM jobs 
ORDER BY created_at DESC 
LIMIT 10;
```

#### Find Jobs by Prompt Keywords
```sql
SELECT * FROM jobs 
WHERE prompt ILIKE '%DePIN%' 
OR prompt ILIKE '%infrastructure%'
ORDER BY created_at DESC;
```

#### Check Job Status Distribution
```sql
SELECT 
    status, 
    COUNT(*) as count 
FROM jobs 
GROUP BY status;
```

#### Get Job Execution Times
```sql
SELECT 
    id,
    prompt,
    status,
    created_at,
    updated_at,
    (updated_at - created_at) as execution_time
FROM jobs 
WHERE status IN ('completed', 'failed')
ORDER BY execution_time DESC;
```

#### Check User Activity
```sql
SELECT 
    u.email,
    u.full_name,
    COUNT(j.id) as job_count,
    MAX(j.created_at) as last_job
FROM users u
LEFT JOIN jobs j ON u.id = j.user_id
GROUP BY u.id, u.email, u.full_name
ORDER BY job_count DESC;
```

### Dataset Queries

#### List Generated Datasets
```sql
SELECT 
    id,
    name,
    description,
    record_count,
    created_at
FROM datasets
ORDER BY created_at DESC;
```

#### Check Dataset Records
```sql
SELECT 
    d.name as dataset_name,
    COUNT(dr.id) as record_count,
    AVG(LENGTH(dr.content::text)) as avg_content_size
FROM datasets d
LEFT JOIN dataset_records dr ON d.id = dr.dataset_id
GROUP BY d.id, d.name
ORDER BY record_count DESC;
```

## 📊 Job Status Lifecycle

### Status Values
- **`pending`** - Job created, waiting to start
- **`running`** - Job is actively processing
- **`completed`** - Job finished successfully
- **`failed`** - Job encountered an error
- **`cancelled`** - Job was manually cancelled

### Typical Job Timeline

1. **Job Creation** (0-5 seconds)
   - User submits prompt
   - Job record created in database
   - Status: `pending`

2. **Planning Phase** (30-120 seconds)
   - PlannerAgent analyzes prompt
   - Creates execution strategy
   - Status: `running`

3. **URL Discovery** (60-300 seconds)
   - DiscoveryAgent finds relevant URLs
   - Prioritizes and filters URLs
   - Status: `running`

4. **Crawling Phase** (300-1800 seconds)
   - Playwright crawls discovered URLs
   - Extracts page content
   - Status: `running`

5. **Schema Inference** (60-300 seconds)
   - Analyzes extracted content
   - Infers data structure
   - Status: `running`

6. **Data Storage** (30-120 seconds)
   - Stores structured data
   - Creates dataset records
   - Status: `completed`

## 🔍 Troubleshooting Common Issues

### Database Connection Errors

#### Symptoms
```
sqlalchemy.exc.OperationalError: connection was closed unexpectedly
```

#### Solutions
```bash
# Check database container
docker logs websets-db-1 --tail 20

# Restart database if needed
docker restart websets-db-1

# Check database connectivity
docker exec -it websets-app-1 python -c "from app.database import engine; print(engine.execute('SELECT 1').scalar())"
```

### Worker Not Processing Jobs

#### Symptoms
- Jobs stuck in `pending` status
- No worker logs

#### Solutions
```bash
# Check worker container
docker logs websets-worker-1 --tail 20

# Restart worker
docker restart websets-worker-1

# Check Redis connectivity
docker exec -it websets-app-1 python -c "import redis; r=redis.Redis(host='redis'); print(r.ping())"
```

### LLM API Issues

#### Symptoms
```
OpenAI API rate limit exceeded
Anthropic API authentication failed
```

#### Solutions
```bash
# Check environment variables
docker exec -it websets-app-1 env | grep -E "(OPENAI|ANTHROPIC)"

# Update Vault secrets if keys are invalid
# Restart containers after updating Vault entries
docker compose restart
```

### Crawling Failures

#### Symptoms
```
Playwright timeout
HTTP 403 Forbidden
robots.txt disallowed
```

#### Solutions
- Check if target sites are accessible
- Verify robots.txt compliance
- Adjust crawl delays in configuration
- Consider using different user agents

## 📈 Performance Monitoring

### Key Metrics to Track

#### Job Success Rate
```sql
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_jobs,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_jobs,
    ROUND(100.0 * SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM jobs
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

#### Average Processing Time
```sql
SELECT 
    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_seconds,
    MIN(EXTRACT(EPOCH FROM (updated_at - created_at))) as min_seconds,
    MAX(EXTRACT(EPOCH FROM (updated_at - created_at))) as max_seconds
FROM jobs 
WHERE status = 'completed'
AND updated_at > created_at;
```

#### Resource Usage
```bash
# Container resource usage
docker stats websets-app-1 websets-worker-1 websets-beat-1

# Database size
docker exec -it websets-db-1 psql -U postgres -d webset_miner -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

## 🚨 Alerting & Notifications

### Log-based Monitoring

#### Monitor for Errors
```bash
# Watch for error patterns
docker logs websets-worker-1 -f | grep -i "error\|exception\|failed"

# Count recent errors
docker logs websets-worker-1 --since="1h" | grep -i "error" | wc -l
```

#### Monitor Job Completion
```bash
# Watch for job completions
docker logs websets-worker-1 -f | grep "Job.*completed"

# Monitor job creation rate
docker logs websets-app-1 --since="1h" | grep "Created job" | wc -l
```

### Database-based Alerts

#### Jobs Stuck in Running State
```sql
SELECT 
    id,
    prompt,
    created_at,
    NOW() - created_at as running_time
FROM jobs 
WHERE status = 'running'
AND created_at < NOW() - INTERVAL '2 hours';
```

#### High Failure Rate
```sql
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
    ROUND(100.0 * SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) / COUNT(*), 2) as failure_rate
FROM jobs
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE(created_at)
HAVING failure_rate > 20;
```

## 🔧 Advanced Monitoring Setup

### Custom Monitoring Script

Create a monitoring script for continuous job tracking:

```bash
#!/bin/bash
# save as scripts/monitor_jobs.sh

echo "=== Websets Job Monitor ==="
echo "Time: $(date)"
echo

echo "=== Container Status ==="
docker ps --filter "name=websets" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo

echo "=== Recent Jobs ==="
docker exec -it websets-db-1 psql -U postgres -d webset_miner -c "
SELECT 
    id,
    LEFT(prompt, 50) || '...' as prompt,
    status,
    created_at
FROM jobs 
ORDER BY created_at DESC 
LIMIT 5;"
echo

echo "=== Job Status Summary ==="
docker exec -it websets-db-1 psql -U postgres -d webset_miner -c "
SELECT 
    status,
    COUNT(*) as count
FROM jobs 
GROUP BY status;"
echo

echo "=== Recent Worker Logs ==="
docker logs websets-worker-1 --tail 5
```

### Continuous Monitoring

```bash
# Run monitoring every 30 seconds
watch -n 30 ./scripts/monitor_jobs.sh

# Or create a simple loop
while true; do
    clear
    ./scripts/monitor_jobs.sh
    sleep 30
done
```

## 📋 Quick Reference Commands

### Essential Commands
```bash
# Start job
docker exec -it websets-app-1 python scripts/run_job.py "Your prompt"

# Monitor worker
docker logs websets-worker-1 -f

# Check job status
docker exec -it websets-db-1 psql -U postgres -d webset_miner -c "SELECT id, status, prompt FROM jobs ORDER BY created_at DESC LIMIT 5;"

# Health check
curl http://localhost:8000/health

# Container status
docker ps --filter "name=websets"
```

### Emergency Commands
```bash
# Restart all services
docker compose restart

# Stop stuck job (find PID first)
docker exec -it websets-worker-1 pkill -f "celery worker"

# Clear Redis queue
docker exec -it websets-redis-1 redis-cli FLUSHALL

# Database backup
docker exec -it websets-db-1 pg_dump -U postgres webset_miner > backup.sql
```

This comprehensive guide covers all aspects of monitoring and tracking mining jobs in the Websets system. Use the appropriate method based on your needs: real-time logs for active monitoring, API endpoints for programmatic access, or database queries for detailed analysis.
