# Suraksha Chakra 🛡️
**Labour rights intelligence for India's 450M informal workers**

A crowdsourced, AI-powered system that:
- Tells workers their **fair wage** before they start a job (RAG on BOCW data)
- Builds an anonymous **contractor risk score** from worker reports  
- **Alerts NGOs** when a contractor crosses the bad-report threshold
- **Predicts vulnerability windows** before climate disasters hit (IMD + NCRB)

---

## Quick Start

```bash
# 1. Clone and setup
cd backend
pip install -r requirements.txt

# 2. Copy and fill env
cp ../.env.example .env
# → Add your OpenAI key at minimum. Everything else is optional for demo.

# 3. Start a local Postgres (or use SQLite for pure demo)
# For demo without Postgres, change DATABASE_URL in .env to:
# sqlite:///./suraksha.db

# 4. Run
uvicorn backend.main:app --reload --port 8000
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhook/whatsapp` | Twilio WhatsApp webhook |
| POST | `/api/wages/query` | Query fair wage (PWA) |
| GET  | `/api/wages/occupations` | Occupation list |
| POST | `/api/reports/submit` | Submit wage report |
| POST | `/api/reports/contractor-check` | Check contractor risk |
| GET  | `/api/reports/contractors/high-risk` | High-risk contractor list |
| GET  | `/api/dashboard/overview` | Dashboard summary stats |
| GET  | `/api/dashboard/district-heatmap` | Per-district report data |
| GET  | `/api/dashboard/vulnerability-scores` | Predictive scores |
| GET  | `/api/dashboard/recent-alerts` | Alert activity feed |

## Architecture

```
Worker (WhatsApp voice) → Sarvam AI (Hindi STT) → NLP Intent Extractor
                                                          ↓
                                              RAG Wage Engine (BOCW PDFs + FAISS)
                                                          ↓
                                              Contractor Risk Score DB
                                                          ↓
                                        (threshold crossed) → NGO Alert (SendGrid)

Parallel: IMD + NCRB + Migration data → Vulnerability Scorer → Predictive NGO Alerts
```

## Data Sources (all free, all public)

- **BOCW wage schedules**: labour.gov.in (state-wise PDFs)
- **NCRB crime data**: ncrb.gov.in (district CSVs, download manually)
- **IMD weather**: api.imd.gov.in
- **NDMA displacement**: ndma.gov.in
- **Migration flows**: Census 2011 + PLFS (mospi.gov.in)

## Running the Vulnerability Scorer (cron)

```python
from backend.db.database import SessionLocal
from backend.services.vulnerability_scorer import run_full_vulnerability_update

db = SessionLocal()
run_full_vulnerability_update(db)
db.close()
```

Set this up as a daily cron or APScheduler task.
