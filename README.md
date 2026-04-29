# wupbro


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.1.10-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$0.15-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-1.0h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $0.1500 (1 commits)
- 👤 **Human dev:** ~$100 (1.0h @ $100/h, 30min dedup)

Generated on 2026-04-29 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---



FastAPI backend + minimal HTML dashboard for the WUP regression watcher.

## Architecture

```
┌──────────────────────┐   POST /events    ┌──────────────────────┐
│  WUP agent (shell)   │ ───────────────▶  │  wupbro (FastAPI)    │
│  - file watcher      │                   │  - /events (sink)    │
│  - testql runner     │                   │  - /drivers/*        │
│  - visual diff       │                   │  - /dashboard (UI)   │
└──────────────────────┘                   └──────────────────────┘
                                                      │
                                                      ▼
                                            ┌─────────────────┐
                                            │ Browser UI      │
                                            │ (auto-refresh)  │
                                            └─────────────────┘
```

## Endpoints

| Path                              | Method | Purpose                                     |
|-----------------------------------|--------|---------------------------------------------|
| `/events`                         | POST   | Receive event from a WUP agent              |
| `/events`                         | GET    | List recent events (filter by type/service) |
| `/events/stats`                   | GET    | Aggregate counts by type                    |
| `/events`                         | DELETE | Clear store (admin/debug)                   |
| `/drivers/dom-diff/capture`       | POST   | One-shot Playwright DOM snapshot + diff     |
| `/drivers/browserless/screenshot` | POST   | Proxy to a `browserless/chrome` container   |
| `/drivers/anomaly/report`         | POST   | Record numeric anomaly as ANOMALY event     |
| `/drivers/health`                 | GET    | Driver capability discovery                 |
| `/`, `/dashboard`                 | GET    | HTML dashboard                              |
| `/healthz`                        | GET    | Liveness probe                              |
| `/openapi.json`, `/docs`          | GET    | OpenAPI spec + Swagger UI                   |

## Event types

`REGRESSION`, `PASS`, `ANOMALY`, `VISUAL_DIFF`, `HEALTH_TRANSITION`.

Schema (Pydantic):

```json
{
  "type": "REGRESSION",
  "service": "users-web",
  "file": "app/users/routes.py",
  "endpoint": "/api/users",
  "status": "fail",
  "stage": "quick",
  "reason": "TestQL exit code 1",
  "timestamp": 1730000000
}
```

Extra fields are preserved via `model_config = {"extra": "allow"}`.

## Run

```bash
# Install
pip install -e wupbro/

# Dev server (auto-reload)
wupbro --reload --port 8000

# Or directly
uvicorn wupbro.main:app --host 0.0.0.0 --port 8000 --reload
```

Dashboard: <http://localhost:8000/>

OpenAPI docs: <http://localhost:8000/docs>

## Configure WUP agent to send events

In your `wup.yaml`:

```yaml
web:
  enabled: true
  endpoint: "http://localhost:8000"
  endpoint_env: "WUPBRO_ENDPOINT"   # fallback if endpoint is empty
  timeout_s: 2.0                     # short — must not block watcher
  api_key: ""                        # optional bearer token
```

Or via environment variable:

```bash
export WUPBRO_ENDPOINT=http://localhost:8000
wup watch . --mode testql
```

The agent will POST events fire-and-forget on:

- service health transitions (up ↔ down)
- regressions (when TestQL fails)
- visual DOM diffs (when significant changes detected)

## Browserless integration

```bash
docker run -d --name browserless -p 3000:3000 browserless/chrome
export BROWSERLESS_URL=http://localhost:3000
wupbro
```

Then:

```bash
curl -X POST http://localhost:8000/drivers/browserless/screenshot \
  -H "Content-Type: application/json" \
  -d '{"url": "http://example.com", "full_page": true}'
```

## Storage

Events are kept in an in-memory ring buffer (capacity 1000) and persisted to `.wupbro/events.jsonl` for restart durability.

## Tests

```bash
PYTHONPATH=wupbro python3 -m pytest wupbro/tests/ -v
```

17 tests covering events router, drivers (anomaly, browserless, dom-diff, health), dashboard HTML, OpenAPI schema.

## License

Licensed under Apache-2.0.
