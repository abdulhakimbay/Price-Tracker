# Price Tracker

A robust, asynchronous price monitoring service built with FastAPI, SQLAlchemy, Celery, and PostgreSQL. It allows users to track product prices from e-commerce websites and receive automated notifications via Email and Telegram when the price drops below their target threshold.

> **Note:** This project is currently in a prototype/pet-project state. 
> - **Parser:** The web scraper is currently a stub (`DemoParser`) that generates random deterministic prices for testing. It does not actually parse real e-commerce websites yet.
> - **Telegram Bot:** A full Telegram bot interface is not yet implemented. The application only uses the Telegram Bot API token to send outgoing notifications to users who have linked their Telegram `user_id`.

## Architecture & Tech Stack

- **Web Framework:** FastAPI (Async)
- **Database:** PostgreSQL with SQLAlchemy 2.0 (Asyncpg) + Alembic for migrations
- **Task Queue & Background Jobs:** Celery with Redis backend/broker
- **Authentication:** JWT (JSON Web Tokens), OAuth2 password bearer
- **Testing:** Pytest, aiosqlite (In-memory SQLite for blazing fast isolated tests)
- **Dependency Management:** `uv`

## Core Features

- **User Management:** Registration, login, and profile management.
- **Telegram Authentication:** Users can link their accounts via Telegram Login.
- **Subscriptions:** Users can subscribe to product URLs and set a target price.
- **Price Monitoring:** A background Celery worker periodically parses tracked URLs to check for price drops.
- **Notifications:** When a price hits or drops below the target, users are notified via Telegram or Email.
- **Price History:** The system keeps a historical record of price changes for tracked products.

## Prerequisites

- Python 3.12+
- PostgreSQL
- Redis
- [uv](https://github.com/astral-sh/uv) package manager

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/abdulhakimbay/Price-Tracker.git
   cd price_tracker
   ```

2. **Install dependencies:**
   We use `uv` for lightning-fast dependency resolution.
   ```bash
   uv sync
   # For development dependencies (pytest, etc.)
   uv sync --group dev
   ```

3. **Configure Environment Variables:**
   Copy the example environment file and fill in your credentials.
   ```bash
   cp .env.example .env
   ```
   You will need to configure your database credentials, an SMTP server for email delivery, and a Telegram Bot token.

4. **Run Database Migrations:**
   ```bash
   uv run alembic upgrade head
   ```

## Running the Application

You need to run the API server and the Celery worker concurrently. You can either run them manually or use Docker Compose.

### Running Manually

**Start the FastAPI Server:**
```bash
uv run fastapi dev app/main.py
```

**Start the Celery Worker:**
```bash
uv run celery -A app.worker.celery_app worker --loglevel=info
```

**Start the Celery Beat (Scheduler):**
```bash
uv run celery -A app.worker.celery_app beat --loglevel=info
```

### Running with Docker Compose (Recommended)

The easiest way to get the entire stack (PostgreSQL, Redis, API, and Celery) running is via Docker Compose:

```bash
docker compose up -d --build
```

## Running Tests

The test suite is fully isolated and does not require PostgreSQL or Redis to be running. It uses `aiosqlite` for fast, in-memory testing.

```bash
uv run pytest tests/ -v --tb=short
```

## Future Roadmap

1. **Implement Real Parsers:** Replace `DemoParser` with actual scrapers using `selectolax` and `httpx` to parse real e-commerce stores (e.g., Amazon, local retailers).
2. **Full Telegram Bot:** Implement a proper long-polling or webhook-based Telegram bot to allow users to add subscriptions directly via Telegram messages.
3. **Frontend Dashboard:** Build a simple web UI for users to manage their tracked items easily.
