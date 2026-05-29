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

## Admin Dashboard

Add to `.env` (or `templates/.env`):

```env
ADMIN_USERNAME=your_admin_id
ADMIN_PASSWORD=your_admin_password
ADMIN_SESSION_SECRET=long-random-secret-string
```

Supabase: ensure `inquiries` has a status column:

```sql
alter table inquiries add column if not exists status text default 'new';

create table if not exists portfolio (
    id bigint generated always as identity primary key,
    title text not null,
    description text,
    image_url text,
    project_url text,
    is_visible boolean default true,
    created_at timestamptz default now()
);
```

Admin URLs:

| Path | Description |
|------|-------------|
| `/admin/login` | Admin login |
| `/admin` | Dashboard |
| `/admin/inquiries` | Inquiry list |
| `/admin/inquiries/{id}` | Inquiry detail |
| `/admin/portfolio` | Portfolio list |
| `/admin/portfolio/new` | Add portfolio item |
| `/admin/portfolio/{id}/edit` | Edit portfolio item |
