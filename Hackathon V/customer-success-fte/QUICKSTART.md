# Quick Start Guide - Customer Success FTE

**TL;DR:** Get the MCP server prototype running in 5 minutes.

---

## Prerequisites Check

```bash
# Check Python version (need 3.11+)
python --version

# Check Docker is running
docker ps
```

---

## Step 1: Navigate to Project

```bash
cd "F:\GIAIC Q4 AGENTIC AI\Hackathon V\customer-success-fte"
```

---

## Step 2: Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Git Bash):**
```bash
python -m venv venv
source venv/Scripts/activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

---

## Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** The MCP server prototype requires the `mcp` package. Install it:

```bash
pip install mcp
```

---

## Step 4: Run the MCP Server Test

Test the prototype without any infrastructure:

```bash
python test_mcp_server.py
```

**Expected Output:**
```
======================================================================
   MCP SERVER TEST SUITE - Customer Success FTE
   Hackathon 5: Digital FTE Factory
======================================================================

Loaded 7 knowledge base entries.

============================================================
TEST SCENARIO 1: Password Reset (Email)
============================================================
...
✅ Scenario 1 Complete

... (all 7 scenarios)

✅ All tests passed!
```

---

## Step 5: Start Docker Infrastructure (Optional)

For full development with database:

```bash
# Start PostgreSQL and Kafka
docker-compose up -d postgres zookeeper kafka

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

---

## Step 6: Initialize Database

```bash
# Wait for PostgreSQL to be healthy (check docker-compose ps)
# Then run schema:
docker exec -i fte-postgres psql -U fte_user -d fte_db < database/schema.sql
```

---

## Common Commands

| Task | Command |
|------|---------|
| Activate venv | `source venv/bin/activate` or `.\venv\Scripts\Activate.ps1` |
| Run tests | `python test_mcp_server.py` |
| Start Docker | `docker-compose up -d` |
| Stop Docker | `docker-compose down` |
| View logs | `docker-compose logs -f` |
| Check DB | `docker exec -it fte-postgres psql -U fte_user -d fte_db` |

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'mcp'"
```bash
pip install mcp
```

### Docker won't start
- Ensure Docker Desktop is running
- Check `docker ps` works

### Port already in use
```bash
# Windows - find process using port 5432
netstat -ano | findstr :5432
# Kill it (replace PID)
taskkill /PID <PID> /F
```

---

## Next Steps

1. ✅ Run `test_mcp_server.py` to see the prototype in action
2. 📋 Review test output to understand tool behavior
3. 📝 Document findings in `specs/001-discovery-log.md`
4. 🔧 Start building the OpenAI Agents SDK version

---

## File Reference

| File | Purpose |
|------|---------|
| `mcp_server.py` | MCP server prototype with 6 tools |
| `test_mcp_server.py` | Test suite with 7 scenarios |
| `requirements.txt` | Python dependencies |
| `docker-compose.yml` | Docker services |
| `database/schema.sql` | PostgreSQL schema |

---

## Getting Help

- Full setup guide: `SETUP.md`
- Project specs: `specs/002-customer-success-fte-spec.md`
- Main README: `README.md`
