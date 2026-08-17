# Operational Quick Reference

## Environment Setup

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

## Migrations

```bash
cd backend
alembic heads
alembic current
alembic upgrade head
```

## Run Services

```bash
cd backend
uvicorn main:app --reload
python -m app.bot.run
```

## Testing

```bash
cd backend
pytest -q
```

## Common Checks

- API health endpoint: `GET /health`
- Swagger docs: `http://127.0.0.1:8000/docs`
- Bot startup log confirms dispatcher initialization
- Alembic head is a single revision

## Troubleshooting

- Migration issues: inspect `alembic current` and `alembic history`
- Bot startup errors: verify `BOT_TOKEN` and installed dependencies
- Auth errors: verify `SECRET_KEY`, token lifetime, and user role permissions
