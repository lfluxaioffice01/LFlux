# LFlux

FastAPI application scaffold.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

## Endpoints

| Path | Description |
|------|-------------|
| `GET /health` | Health check |
| `GET /api/v1/` | API root |

## Test

```bash
pip install httpx pytest
pytest
```
