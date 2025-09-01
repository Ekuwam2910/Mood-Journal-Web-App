# Mood Journal – AI Emotion Tracker

Beginner-friendly full‑stack project: HTML/CSS/JS (Chart.js) + Flask + MySQL (or SQLite fallback) + Hugging Face Inference API.

## Features
- Write journal entries → AI sentiment (label + confidence score)
- Store entries in DB and display history
- Mood trend chart over time (Chart.js)
- CRUD: Create, Read, Delete

## Quick Start

### 1) Install
```bash
cd mood-journal
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Database
**MySQL (preferred)**:
```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS moodjournal;"
mysql -u root -p moodjournal < schema.sql
```
Set env var:
```
export MYSQL_URL="mysql+pymysql://<user>:<pass>@localhost/moodjournal"
```

_No MySQL?_ App falls back to SQLite file `mood.db` automatically.

### 3) Hugging Face token
Create a free token at https://huggingface.co/settings/tokens and set:
```
export HF_API_TOKEN="hf_..."
export HF_MODEL="cardiffnlp/twitter-roberta-base-sentiment-latest"
```

### 4) Run
```bash
python app.py
```
Open http://localhost:5000

## API
- `GET /` – UI
- `GET /api/entries` – list entries
- `POST /api/entries` – create + analyze (JSON: `{ "text": "..." }`)
- `DELETE /api/entries/<id>` – delete

## Deploy
- On Render/Railway: set env `MYSQL_URL`, `HF_API_TOKEN` (and `PORT` if required).
- Use a managed MySQL (PlanetScale/Aiven/etc.).

Good luck at the hackathon! 🚀
