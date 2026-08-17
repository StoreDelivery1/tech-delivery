# Tech Delivery

Tech Delivery is a backend platform for delivery operations built with FastAPI, PostgreSQL, and a Telegram bot workflow.

## Project Overview

The system provides API and bot interfaces for managing users, stores, orders, and courier operations in a single delivery workflow.

## Features

- JWT-based authentication and role-aware access control
- user, store, and order management
- courier assignment and order status transitions
- Telegram bot flows for admin, manager, and courier roles
- database versioning with Alembic migrations

## Architecture

The backend follows a modular service-oriented structure:

- `app/core`: configuration, security, and permissions
- `app/database`: SQLAlchemy session and base configuration
- `app/models`: ORM entities
- `app/schemas`: request and response schemas
- `app/services`: business use-cases
- `app/routers`: FastAPI route handlers
- `app/bot`: Telegram bot handlers, FSM states, keyboards, and utilities
- `alembic`: migration scripts and configuration

## Repository Structure

- `backend/`: FastAPI app, bot modules, migrations, scripts, and tests
- `docs/`: technical and operational documentation
- `docker/`: container-related assets
- `database/`: database-related assets
- `miniapp/`: miniapp/frontend area

## Technology Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- PostgreSQL
- Alembic
- aiogram (Telegram bot)
- Docker Compose

## Installation

From the repository root:

1. `cd backend`
2. `python -m venv .venv`
3. `.venv\\Scripts\\activate`
4. `pip install -r requirements.txt`

## Environment Variables

Create `backend/.env` (local only):

- `DATABASE_URL=postgresql+psycopg://<db_user>:<db_password>@<db_host>:5432/<db_name>`
- `SECRET_KEY=<strong_random_secret>`
- `ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=60`
- `BOT_TOKEN=<telegram_bot_token>`

Use only non-production placeholders in example files. Never commit real secrets.

## Database

- primary database: PostgreSQL
- ORM: SQLAlchemy
- migrations: Alembic

## Alembic

Run from `backend/`:

- apply migrations: `alembic upgrade head`
- create migration: `alembic revision --autogenerate -m "message"`
- inspect heads: `alembic heads`

## FastAPI

Run API server:

- `uvicorn main:app --reload`

API docs:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Telegram Bot

Run bot process from `backend/`:

- `python -m app.bot.run`

## Docker

Run PostgreSQL locally:

- `docker compose up -d`

Environment variables for compose are configured with safe defaults and should be overridden per environment.

## Testing

Run tests from `backend/`:

- `pytest -q`

Recommended CI steps:

- linting and formatting checks
- test execution
- dependency and secret scanning

## Security

- keep `.env`, virtual environments, and caches out of Git
- use strong per-environment secrets
- rotate credentials and tokens when exposed
- avoid hardcoded secrets in configuration and documentation

## Deployment

For production deployments:

- inject secrets via CI/CD or secret manager
- run migrations as part of deployment pipeline
- isolate database/network access
- enable monitoring and structured logging

## Troubleshooting

- DB connection errors:
    - verify `DATABASE_URL` and database reachability
- auth token errors:
    - verify `SECRET_KEY`, algorithm, and token expiration settings
- bot startup issues:
    - verify `BOT_TOKEN` and outbound network access
- migration problems:
    - verify Alembic head and migration chain

## Contributing

1. Create a feature branch.
2. Keep changes scoped and tested.
3. Run lint/tests locally before commit.
4. Open a pull request with a clear change summary.

## License

Internal Company Project.