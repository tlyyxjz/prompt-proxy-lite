# PromptProxy Lite

[![tests](https://github.com/tlyyxjz/prompt-proxy-lite/actions/workflows/tests.yml/badge.svg)](https://github.com/tlyyxjz/prompt-proxy-lite/actions/workflows/tests.yml)
[![License MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> A minimal open-source OpenAI-compatible API proxy that injects system prompts server-side. The lite, single-tenant, plaintext-config cousin of [PromptProxy Pro](https://github.com/tlyyxjz/prompt-proxy-pro).

If you sell prompts, manage a small team, or want encrypted prompt storage + a full admin panel + multi-AI backends + usage analytics, check out the **Pro** edition linked above.

---

## Why

You wrote a great system prompt. You want to:
- Let your customers use it through ChatBox, Cursor, or any OpenAI-compatible client
- **Without** shipping the prompt text to them in plaintext
- **Without** writing a custom SDK or wrapper for every AI provider

PromptProxy Lite solves the simplest version of that problem: **the prompt lives on your server, the client only sees the API.**

## What Lite does

- OpenAI-compatible `/v1/chat/completions` endpoint (streaming + non-streaming)
- Server-side system prompt injection from a local `prompts.yaml`
- Bearer API key authentication (keys defined in `.env`)
- Forwards to any OpenAI-compatible backend (OpenAI, DeepSeek, OpenRouter, Groq, Together, ...)
- ~230 lines of plain Python across 5 small modules — readable in 5 minutes

## What Lite does NOT do (Pro does)

| Feature | Lite | Pro |
|---|---|---|
| Encrypted prompt storage (AES-256-GCM) | — | ✅ |
| Web admin panel (clients / prompts / usage) | — | ✅ |
| Multi-client management with expiry | — | ✅ |
| Per-client prompt assignment | — | ✅ |
| Usage analytics + error logs | — | ✅ |
| Multi-AI backend routing per prompt | — | ✅ |
| Rate limiting (per-key SHA-256 hashed) | — | ✅ |
| Docker multi-stage build + healthcheck | — | ✅ |

## Quick start

```bash
git clone https://github.com/tlyyxjz/prompt-proxy-lite.git
cd prompt-proxy-lite
pip install -r requirements.txt
cp .env.example .env
# edit .env with your upstream API key + client keys
uvicorn app.main:app --reload
```

Send a request:

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-my-client-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "hello"}],
    "stream": false
  }'
```

The server injects your system prompt from `prompts.yaml`, forwards the request to your upstream, and returns the response. The client never sees the system prompt.

## Configuration

### `.env`

```env
UPSTREAM_BASE_URL=https://api.deepseek.com/v1
UPSTREAM_API_KEY=sk-your-upstream-key
CLIENT_API_KEYS=sk-client-one,sk-client-two,sk-client-three
```

### `prompts.yaml`

```yaml
# Injected as system message before the user's messages
system_prompt: |
  You are a senior code reviewer. Be concise, direct, and
  point out the top 3 issues with any code snippet.

# Optional: override the model the client requested
# force_model: deepseek-chat
```

## Use with ChatBox / Cursor / any OpenAI client

In your client's settings:
- **API Base URL**: `http://your-server:8000/v1`
- **API Key**: any of the `CLIENT_API_KEYS` you configured
- **Model**: anything (Lite forwards to your upstream)

Your customer never sees the system prompt. They just hit your endpoint and get great results.

## Deploy

### Docker

```bash
docker build -t prompt-proxy-lite .
docker run -p 8000:8000 --env-file .env -v $(pwd)/prompts.yaml:/app/prompts.yaml prompt-proxy-lite
```

### Expose to the public internet

Use Cloudflare Tunnel, Tailscale Funnel, or any reverse proxy. Lite does not include TLS termination — put it behind a real proxy in production.

## Security notes

- Lite stores prompts in plaintext on disk. If you need encrypted storage, use Pro.
- Lite uses a constant-time comparison for API keys.
- Lite has no rate limiting. Use Pro or a reverse proxy (Caddy, Cloudflare) for rate limits.
- Never commit your `.env` file. The included `.gitignore` already excludes it.

## Tests

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

The suite covers the `/health` endpoint, bearer-key rejection (missing / wrong key),
server-side system-prompt injection and merge, and `CLIENT_API_KEYS` parsing.
It runs in CI on Python 3.10 and 3.12.

> `pytest-asyncio` is required — `pytest.ini` sets `asyncio_mode = auto` and the
> client fixture is async. Without the plugin those cases error instead of running.

## License

MIT — do whatever you want, no warranty, don't sue me.

## Author

Built by [@tlyyxjz](https://github.com/tlyyxjz). If you need the encrypted multi-tenant version, see [PromptProxy Pro](https://github.com/tlyyxjz/prompt-proxy-pro).

## FAQ

**Can I use this with Claude / Gemini?**
Only with OpenAI-compatible backends. Claude and Gemini have different schemas — Pro supports both via adapter classes.

**Can I sell prompts with Lite?**
Technically yes, but your customer could share their API key with anyone. Pro lets you rotate keys, set expiry, and track usage per client.

**Why open-source a stripped-down version?**
Because the lite version is genuinely useful for personal use, and the pro version solves a different problem (selling prompt access as a service). Different audiences.

**Is there a hosted version?**
Not yet. Pro is self-host only — your prompts stay on your server.
