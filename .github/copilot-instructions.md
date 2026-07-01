# Copilot Instructions for this repository

- This repo is a Python Telegram bot template that runs on PythonAnywhere.
- The code has two runtime modes:
  - Local polling via `run_local.py` (`make run`)
  - Production webhook via `pythonanywhere_wsgi.py` -> `api/index.py`

## Key architecture

- `api/index.py` is the Flask entrypoint for `/api/webhook`, `/api/health`, and `/api/deploy`.
- `pythonanywhere_wsgi.py` loads `.env`, exposes `application`, and calls `bot.clients.register_webhook()` on boot.
- `bot/clients.py` constructs `telebot.TeleBot(threaded=False)` and an OpenAI-compatible `ai` client.
- `bot/handlers.py` defines Telegram commands and message handling. The text flow is: `should_respond()` -> `is_rate_limited()` -> `keep_typing()` -> `ask_ai()` -> `send_reply()`.
- `bot/providers.py` dispatches to `main` (OpenAI-compatible, retryable) or optional `hf` (Hugging Face Gradio). User preference is stored in `bot/preferences.py`.
- `bot/store.py` is a local SQLite KV store used by history, rate limits, preferences, and dedupe. When `SQLITE_PATH` is unset, all stateful features fall back safely to stateless mode.

## Important conventions

- Do not make `telebot.TeleBot` threaded. It must be `threaded=False` to avoid worker death and race issues.
- `bot/config.py` reads env vars at import time. `.env` is loaded manually by both `run_local.py` and `pythonanywhere_wsgi.py` using the same lightweight parser.
- `WEBHOOK_SECRET` is optional but recommended; `api/index.py` verifies `X-Telegram-Bot-Api-Secret-Token` before importing heavy modules.
- `DEPLOY_SECRET` is fail-closed: `/api/deploy` returns 403 if unset.
- `bot/helpers.py:send_reply()` retries on Markdown parse failure by sending plain text.
- `bot/dedupe.py` uses atomic `set_nx()` to prevent duplicate processing of the same Telegram update.

## Developer workflows

- Install deps and create venv: `make install`
- Run locally: `make run`
- Run tests: `make test` or `.venv/bin/pytest tests/ -v`
- First-time PythonAnywhere deploy: `make deploy-pa` (requires `.env` with `PA_USERNAME` and `PA_API_TOKEN`)
- GitHub Actions CI runs `pytest tests/ -v` on pushes and PRs to `main`.
- Auto-deploy on `main` pushes is configured in `.github/workflows/deploy.yml`. It calls `/api/deploy` with `PA_DEPLOY_URL` and `DEPLOY_SECRET`.

## What to change where

- Add new Telegram commands in `bot/handlers.py`.
- Change AI prompt behavior in `bot/config.py` or `bot/providers.py`.
- Change storage behavior in `bot/store.py`.
- Change webhook or deploy behavior in `api/index.py`.
- Use `pythonanywhere_wsgi.py` only for PA boot logic and `.env` loading.

## Quick gotchas

- Local polling and production webhook cannot coexist for the same bot token.
- `pythonanywhere_wsgi.py` must expose `application`.
- `WEBHOOK_URL` on PA is usually `https://<username>.pythonanywhere.com/api/webhook`.
- `HF_SPACE_ID` is optional; when unset, `/model` is not registered.
- `SQLITE_PATH` unset means no history, rate limit, preferences, or dedupe.

## Useful files

- `README.md` for student-facing setup and deployment flow
- `CLAUDE.md` for existing agent-readable architecture explanations
- `Makefile` for local commands
- `.github/workflows/ci.yml` and `deploy.yml` for CI/deploy behavior
