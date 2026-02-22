# Hosting checklist (Render, Railway, PythonAnywhere, etc.)

## 1. Environment variables (set on your host)

| Variable | Required | Example / Notes |
|----------|----------|------------------|
| `HUDDY_OPENROUTER_API_KEY_1` | **Yes** | Your OpenRouter API key for the chat |
| `DJANGO_SECRET_KEY` | **Yes** (production) | Long random string; generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DJANGO_DEBUG` | No | Set to `False` or `0` in production |
| `ALLOWED_HOSTS` | No | Comma-separated, e.g. `yourapp.onrender.com,www.yourapp.com` |

## 2. Build & run commands

- **Build:** `pip install -r requirements.txt`
- **Collect static:** `python manage.py collectstatic --noinput`
- **Run (Gunicorn):** `gunicorn portfolio_ai.wsgi --bind 0.0.0.0:$PORT`  
  (Use `$PORT` if the host provides it; otherwise e.g. `--bind 0.0.0.0:8000`)

If your host runs from the repo root and the app is in a subfolder (e.g. `portfolio_ai/`), run the above from that subfolder, or use:  
`gunicorn portfolio_ai.wsgi -c gunicorn.conf.py` from the folder that contains the `portfolio_ai` package.

## 3. Files that must be deployed

- `data.json` – must be in the same directory as `manage.py` (project root). Include it in the repo or upload it on the server.
- `.env` – do **not** commit; set the variables above in the host’s dashboard instead.

## 4. Quick checks before go-live

- [ ] `DJANGO_DEBUG=False` and `DJANGO_SECRET_KEY` set on the host
- [ ] `HUDDY_OPENROUTER_API_KEY_1` set on the host
- [ ] `ALLOWED_HOSTS` includes your app’s hostname(s)
- [ ] `data.json` is present in the project root on the server
- [ ] Static files: run `collectstatic` during build; WhiteNoise will serve them
