# AI Portfolio Assistant — Hudson’s Intelligent Personal Chatbot

AI Portfolio Assistant is a Django-based chatbot that answers questions **only about Hudson Mathew** (skills, projects, education, internship, and goals). It uses **GPT-4o-mini via the OpenRouter API** and loads its knowledge from a single editable `data.json` file, so updates go live instantly without code changes. The assistant supports multi-turn chat, trims history to control token usage, and uses strict prompt rules to prevent off-topic answers and hallucinations. Deployed as a standalone web app (linked from the portfolio site).

---

## Features
- Portfolio-focused Q&A (Hudson-only scope)
- `data.json` knowledge base (easy updates, no database)
- Multi-turn conversation support (history included per request)
- Token control (knowledge compression + history trimming)
- Strict refusal for off-topic questions
- Robust error handling (timeouts, missing key, API errors)

## Tech Stack
- **Backend:** Python, Django
- **AI:** OpenRouter API + GPT-4o-mini
- **HTTP:** `requests`
- **Static:** WhiteNoise
- **Config:** python-dotenv
- **Data store:** `data.json` (no models / no database)
- **Deployment:** Replit (can also run on Render)

## How It Works (High Level)
1. Client sends message + recent chat history to `/api/chat/`
2. Server loads `data.json` on every request
3. Data is compacted and history is sanitized to stay within token limits
4. A strict system prompt enforces Hudson-only answers
5. Request is sent to OpenRouter, response is returned as JSON

## Author
Hudson Mathew — March 2026
