# Development Environment Setup Guide

**Last Updated:** 2026-03-17

---

## Prerequisites

Before starting, ensure you have:

- [ ] Python 3.11 or higher installed
- [ ] Docker Desktop installed and running
- [ ] Git installed (optional, for version control)
- [ ] A code editor (VS Code recommended)

---

## Step 1: Clone/Navigate to Project

```bash
cd "F:\GIAIC Q4 AGENTIC AI\Hackathon V\customer-success-fte"
```

---

## Step 2: Create Python Virtual Environment

### Windows (PowerShell/Git Bash)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# PowerShell:
.\venv\Scripts\Activate.ps1

# Git Bash:
source venv/Scripts/activate

# CMD:
venv\Scripts\activate.bat
```

### macOS/Linux

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

**Verify activation:** You should see `(venv)` in your terminal prompt.

---

## Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

**Verify installation:**
```bash
python -c "import fastapi; print(fastapi.__version__)"
```

---

## Step 4: Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# On Windows (PowerShell):
Copy-Item .env.example .env

# On Windows (CMD):
copy .env.example .env
```

**Edit `.env` and add your API keys:**
- Get OpenAI API key from: https://platform.openai.com/api-keys
- Get Gmail credentials from: Google Cloud Console
- Get Twilio credentials from: https://console.twilio.com

**Minimum required for local development:**
```
OPENAI_API_KEY=sk-...
POSTGRES_HOST=localhost
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

---

## Step 5: Start Docker Services

```bash
# Start PostgreSQL, Kafka, and Kafka UI
docker-compose up -d postgres zookeeper kafka kafka-ui

# Check if services are running
docker-compose ps

# View logs (optional)
docker-compose logs -f
```

**Expected output:**
```
NAME                STATUS              PORTS
fte-postgres        Up (healthy)        0.0.0.0:5432->5432/tcp
fte-zookeeper       Up                  2181/tcp
fte-kafka           Up (healthy)        0.0.0.0:9092->9092/tcp
fte-kafka-ui        Up                  0.0.0.0:8089->8080/tcp
```

---

## Step 6: Initialize Database

```bash
# Wait for PostgreSQL to be ready (check health)
docker-compose ps postgres

# Run the schema migration
docker exec -i fte-postgres psql -U fte_user -d fte_db < database/schema.sql
```

**Verify tables were created:**
```bash
docker exec -it fte-postgres psql -U fte_user -d fte_db -c "\dt"
```

You should see all tables: customers, conversations, messages, tickets, knowledge_base, etc.

---

## Step 7: Verify Kafka Topics

Open Kafka UI in your browser: http://localhost:8089

You should see the `fte-kafka` cluster. Topics will be auto-created when the application starts.

---

## Step 8: Test the Setup

### Test Database Connection

```bash
docker exec -it fte-postgres psql -U fte_user -d fte_db -c "SELECT COUNT(*) FROM customers;"
```

Expected: `0` (empty table)

### Test Python Environment

```bash
# Check if key packages are installed
python -c "import fastapi; import asyncpg; import openai; print('All packages installed!')"
```

---

## Step 9: Start the API Server (When Ready)

Once you've built the API in `production/api/main.py`:

```bash
# Start the API server
uvicorn production.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Verify:** Open http://localhost:8000/health in your browser.

---

## Step 10: Start the Message Processor (When Ready)

Once you've built the worker in `production/workers/message_processor.py`:

```bash
# In a new terminal (keep API server running)
python production/workers/message_processor.py
```

---

## Troubleshooting

### Docker Issues

**Problem:** Containers won't start
```bash
# Check Docker Desktop is running
docker ps

# Restart Docker Desktop if needed
```

**Problem:** Port already in use
```bash
# Check what's using the port
# Windows (PowerShell):
netstat -ano | findstr :5432

# Kill the process (replace PID)
taskkill /PID <PID> /F
```

### Database Issues

**Problem:** Connection refused
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Restart if needed
docker-compose restart postgres
```

**Problem:** Schema not applied
```bash
# Re-run the schema
docker exec -i fte-postgres psql -U fte_user -d fte_db < database/schema.sql
```

### Python Issues

**Problem:** Module not found
```bash
# Ensure virtual environment is activated
# Check (venv) is in your prompt

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## Development Workflow

### Daily Development

```bash
# 1. Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 2. Start Docker services
docker-compose up -d

# 3. Start API server with hot reload
uvicorn production.api.main:app --reload

# 4. Make changes, server auto-reloads

# 5. Run tests
pytest production/tests/ -v

# 6. Stop Docker when done
docker-compose down
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=production --cov-report=html

# Run specific test file
pytest production/tests/test_agent.py -v

# Run with live reload
pytest-watch
```

---

## Next Steps

After setup is complete:

1. ✅ Proceed to **Step 5: Build MCP Server Prototype**
2. 📋 Analyze sample tickets in `context/003-sample-tickets.json`
3. 📝 Document findings in `specs/001-discovery-log.md`

---

## Quick Reference

| Service | URL/Port | Purpose |
|---------|----------|---------|
| API Server | http://localhost:8000 | FastAPI application |
| PostgreSQL | localhost:5432 | Database |
| Kafka | localhost:9092 | Event streaming |
| Kafka UI | http://localhost:8089 | Kafka management |

| Command | Purpose |
|---------|---------|
| `docker-compose up -d` | Start all services |
| `docker-compose down` | Stop all services |
| `docker-compose logs -f` | View logs |
| `docker-compose ps` | Check service status |
| `pytest` | Run tests |
