# wupbro

WUP Browser Dashboard — FastAPI backend for WUP regression watcher

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Code Analysis](#code-analysis)
- [Source Map](#source-map)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `wupbro`
- **version**: `0.1.10`
- **python_requires**: `>=3.9`
- **license**: {'text': 'Apache-2.0'}
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, testql(3), app.doql.less, goal.yaml, .env.example, src(4 mod), project/(2 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: wupbro;
  version: 0.1.10;
}

dependencies {
  runtime: "fastapi>=0.110, uvicorn[standard]>=0.27, httpx>=0.27, pydantic>=2.0, jinja2>=3.1";
  dev: "pytest>=8, pytest-asyncio>=0.23, httpx>=0.27, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
}

entity[name="Event"] {
  type: EventType!;
  service: string;
  file: string;
  endpoint: string;
  url: string;
  status: string;
  stage: string;
  reason: string;
  diff: Dict[str, Any];
  timestamp: int!;
}

entity[name="EventList"] {
  items: List[Event]!;
  total: int!;
}

entity[name="AnomalyReport"] {
  service: string!;
  metric: string!;
  value: float!;
  threshold: float!;
  timestamp: int!;
}

entity[name="NotificationConfig"] {
  enabled: bool!;
  regression_new: bool!;
  regression_diff: bool!;
  regression_diff_seconds: int!;
  status_transition: bool!;
  status_transition_type: StatusTransitionType!;
  anomaly_new: bool!;
  visual_diff_new: bool!;
  health_change: bool!;
  pass_recovery: bool!;
  cooldown_seconds: int!;
  services_include: List[str]!;
  services_exclude: List[str]!;
}

entity[name="NotificationSubscription"] {
  subscription_id: string!;
  config: NotificationConfig!;
  created_at: int!;
  last_notification_at: int;
}

interface[type="api"] {
  type: rest;
  framework: fastapi;
}

interface[type="cli"] {
  framework: argparse;
}
interface[type="cli"] page[name="wupbro"] {

}

deploy {
  target: pip;
}

environment[name="local"] {
  runtime: python;
  env_file: .env;
  python_version: >=3.9;
}
```

### Source Modules

- `wupbro.main`
- `wupbro.models`
- `wupbro.notifications`
- `wupbro.storage`

## Interfaces

### CLI Entry Points

- `wupbro`

### testql Scenarios

#### `testql-scenarios/generated-api-integration.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-api-integration.testql.toon.yaml
# SCENARIO: API Integration Tests
# TYPE: api
# GENERATED: true

CONFIG[3]{key, value}:
  base_url, http://localhost:8101
  timeout_ms, 30000
  retry_count, 3

API[4]{method, endpoint, expected_status}:
  GET, /health, 200
  GET, /api/v1/status, 200
  POST, /api/v1/test, 201
  GET, /api/v1/docs, 200

ASSERT[2]{field, operator, expected}:
  status, ==, ok
  response_time, <, 1000
```

#### `testql-scenarios/generated-api-smoke.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-api-smoke.testql.toon.yaml
# SCENARIO: Auto-generated API Smoke Tests
# TYPE: api
# GENERATED: true
# DETECTORS: FastAPIDetector

CONFIG[5]{key, value}:
  base_url, http://localhost:8101
  timeout_ms, 10000
  retry_count, 3
  retry_backoff_ms, 1000
  detected_frameworks, FastAPIDetector

# REST API Endpoints (1 unique)
API[1]{method, endpoint, expected_status}:
  GET, /, 200

ASSERT[2]{field, operator, expected}:
  _status, <, 500
  _status, >=, 200

# Summary by Framework:
#   fastapi: 1 endpoints
```

#### `testql-scenarios/generated-from-pytests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-from-pytests.testql.toon.yaml
# SCENARIO: Auto-generated from Python Tests
# TYPE: integration
# GENERATED: true

CONFIG[2]{key, value}:
  base_url, ${api_url:-http://localhost:8101}
  timeout_ms, 10000

# Converted 10 API calls from pytest
API[10]{method, endpoint, expected_status}:
  GET, /openapi.json, 200
  POST, /drivers/browserless/screenshot, 200
  POST, /drivers/dom-diff/capture, 200
  POST, /events, 200
  GET, /events, 200
  GET, /openapi.json, 200
  POST, /drivers/browserless/screenshot, 200
  POST, /drivers/dom-diff/capture, 200
  POST, /events, 200
  GET, /events, 200

# Converted 6 assertions from pytest
ASSERT[6]{field, operator, expected}:
  _status, ==, 200
  _status, ==, 503
  items[0].diff.counts.added, ==, 5
  _status, ==, 200
  _status, ==, 503
  items[0].diff.counts.added, ==, 5
```

## Configuration

```yaml
project:
  name: wupbro
  version: 0.1.10
  env: local
```

## Dependencies

### Runtime

```text markpact:deps python
fastapi>=0.110
uvicorn[standard]>=0.27
httpx>=0.27
pydantic>=2.0
jinja2>=3.1
```

### Development

```text markpact:deps python scope=dev
pytest>=8
pytest-asyncio>=0.23
httpx>=0.27
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

## Deployment

```bash markpact:run
pip install wupbro

# development install
pip install -e .[dev]
```

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `*(not set)*` | Required: OpenRouter API key (https://openrouter.ai/keys) |
| `LLM_MODEL` | `openrouter/qwen/qwen3-coder-next` | Model (default: openrouter/qwen/qwen3-coder-next) |
| `PFIX_AUTO_APPLY` | `true` | true = apply fixes without asking |
| `PFIX_AUTO_INSTALL_DEPS` | `true` | true = auto pip/uv install |
| `PFIX_AUTO_RESTART` | `false` | true = os.execv restart after fix |
| `PFIX_MAX_RETRIES` | `3` |  |
| `PFIX_DRY_RUN` | `false` |  |
| `PFIX_ENABLED` | `true` |  |
| `PFIX_GIT_COMMIT` | `false` | true = auto-commit fixes |
| `PFIX_GIT_PREFIX` | `pfix:` | commit message prefix |
| `PFIX_CREATE_BACKUPS` | `false` | false = disable .pfix_backups/ directory |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`wupbro`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `pyproject.toml:version`, `wupbro/__init__.py:__version__`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# wupbro | 19f 1395L | python:16,shell:2,less:1 | 2026-04-29
# stats: 47 func | 10 cls | 19 mod | CC̄=2.4 | critical:0 | cycles:0
# alerts[5]: CC test_anomaly_report_creates_event=7; CC test_openapi_schema_includes_routes=6; CC test_driver_health_reports_capabilities=6; CC test_list_events_returns_recent=6; CC test_event_stats=5
# hotspots[5]: notification_stream fan=13; dom_diff_capture fan=12; post_event fan=7; main fan=6; list_events fan=6
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[19]:
  app.doql.less,83
  project.sh,49
  tests/__init__.py,1
  tests/conftest.py,24
  tests/test_dashboard.py,36
  tests/test_drivers.py,51
  tests/test_events.py,96
  tree.sh,2
  wupbro/__init__.py,8
  wupbro/__main__.py,22
  wupbro/main.py,46
  wupbro/models.py,124
  wupbro/notifications.py,284
  wupbro/routers/__init__.py,2
  wupbro/routers/dashboard.py,25
  wupbro/routers/drivers.py,130
  wupbro/routers/events.py,66
  wupbro/routers/notifications.py,235
  wupbro/storage.py,111
D:
  tests/__init__.py:
  tests/conftest.py:
    e: fresh_store,client
    fresh_store()
    client(fresh_store)
  tests/test_dashboard.py:
    e: test_root_serves_dashboard,test_dashboard_alias,test_healthz,test_openapi_schema_includes_routes
    test_root_serves_dashboard(client)
    test_dashboard_alias(client)
    test_healthz(client)
    test_openapi_schema_includes_routes(client)
  tests/test_drivers.py:
    e: test_anomaly_report_creates_event,test_driver_health_reports_capabilities,test_browserless_unreachable_returns_503,test_dom_diff_endpoint_exists
    test_anomaly_report_creates_event(client)
    test_driver_health_reports_capabilities(client)
    test_browserless_unreachable_returns_503(client;monkeypatch)
    test_dom_diff_endpoint_exists(client)
  tests/test_events.py:
    e: test_post_event_accepted,test_post_event_invalid_type_rejected,test_list_events_returns_recent,test_list_events_filter_by_type,test_list_events_filter_by_service,test_list_events_limit,test_event_stats,test_clear_events,test_event_extra_fields_preserved
    test_post_event_accepted(client)
    test_post_event_invalid_type_rejected(client)
    test_list_events_returns_recent(client)
    test_list_events_filter_by_type(client)
    test_list_events_filter_by_service(client)
    test_list_events_limit(client)
    test_event_stats(client)
    test_clear_events(client)
    test_event_extra_fields_preserved(client)
  wupbro/__init__.py:
  wupbro/__main__.py:
    e: main
    main()
  wupbro/main.py:
    e: create_app
    create_app()
  wupbro/models.py:
    e: Event,EventList,DomDiffRequest,ScreenshotRequest,AnomalyReport,NotificationConfig,NotificationSubscription,NotificationPayload
    Event:  # Generic WUP event posted by an agent.
    EventList:
    DomDiffRequest:
    ScreenshotRequest:
    AnomalyReport:
    NotificationConfig:  # Konfiguracja powiadomień przeglądarkowych dla użytkownika.
    NotificationSubscription:  # Subskrypcja powiadomień dla konkretnego klienta (przeglądark
    NotificationPayload:  # Payload wysyłany jako powiadomienie przeglądarkowe.
  wupbro/notifications.py:
    e: get_notification_manager,set_notification_manager,NotificationManager
    NotificationManager: __init__(1),subscribe(2),unsubscribe(1),get_subscription(1),list_subscriptions(0),update_config(2),process_event(1),_detect_notification_types(2),_should_notify(2),_create_payload(2),register_sse_client(1),unregister_sse_client(1),push_to_sse(1)  # Manages browser notification subscriptions and event detecti
    get_notification_manager(store)
    set_notification_manager(manager)
  wupbro/routers/__init__.py:
  wupbro/routers/dashboard.py:
    e: root,dashboard
    root(request)
    dashboard(request)
  wupbro/routers/drivers.py:
    e: _store,dom_diff_capture,browserless_screenshot,anomaly_report,driver_health
    _store()
    dom_diff_capture(req;store)
    browserless_screenshot(req)
    anomaly_report(report;store)
    driver_health()
  wupbro/routers/events.py:
    e: _store,post_event,list_events,event_stats,clear_events
    _store()
    post_event(event;store)
    list_events(type;service;limit;store)
    event_stats(store)
    clear_events(store)
  wupbro/routers/notifications.py:
    e: subscribe,list_subscriptions,get_subscription,update_subscription,unsubscribe,get_default_config,get_notification_types,get_status_transition_types,notification_stream,send_test_notification
    subscribe(config)
    list_subscriptions()
    get_subscription(subscription_id)
    update_subscription(subscription_id;config)
    unsubscribe(subscription_id)
    get_default_config()
    get_notification_types()
    get_status_transition_types()
    notification_stream(subscription_id)
    send_test_notification(subscription_id;background_tasks)
  wupbro/storage.py:
    e: get_default_store,set_default_store,EventStore
    EventStore: __init__(2),_load_existing(0),add(1),list(3),clear(0),stats(0)  # Thread-safe ring buffer + JSONL persistence.
    get_default_store()
    set_default_store(store)
```

## Source Map

*Top 4 modules by symbol density — signatures for LLM orientation.*

### `wupbro.notifications` (`wupbro/notifications.py`)

```python
def get_notification_manager(store)  # CC=3, fan=2
def set_notification_manager(manager)  # CC=1, fan=0
class NotificationManager:  # Manages browser notification subscriptions and event detecti
    def __init__(event_store)  # CC=1
    def subscribe(subscription_id, config)  # CC=1
    def unsubscribe(subscription_id)  # CC=2
    def get_subscription(subscription_id)  # CC=1
    def list_subscriptions()  # CC=1
    def update_config(subscription_id, config)  # CC=2
    def process_event(event)  # CC=12 ⚠
    def _detect_notification_types(event, current_time)  # CC=14 ⚠
    def _should_notify(notif_type, config)  # CC=8
    def _create_payload(notif_type, event)  # CC=3
    def register_sse_client(client_id)  # CC=2
    def unregister_sse_client(client_id)  # CC=2
    def push_to_sse(notification)  # CC=2
```

### `wupbro.storage` (`wupbro/storage.py`)

```python
def get_default_store()  # CC=2, fan=2
def set_default_store(store)  # CC=1, fan=0
class EventStore:  # Thread-safe ring buffer + JSONL persistence.
    def __init__(jsonl_path, capacity)  # CC=2
    def _load_existing()  # CC=7
    def add(event)  # CC=3
    def list(type_filter, service_filter, limit)  # CC=7
    def clear()  # CC=4
    def stats()  # CC=2
```

### `wupbro.main` (`wupbro/main.py`)

```python
def create_app()  # CC=1, fan=4
```

### `wupbro.models` (`wupbro/models.py`)

```python
class Event:  # Generic WUP event posted by an agent.
class EventList:
class DomDiffRequest:
class ScreenshotRequest:
class AnomalyReport:
class NotificationConfig:  # Konfiguracja powiadomień przeglądarkowych dla użytkownika.
class NotificationSubscription:  # Subskrypcja powiadomień dla konkretnego klienta (przeglądark
class NotificationPayload:  # Payload wysyłany jako powiadomienie przeglądarkowe.
```

## Call Graph

*14 nodes · 12 edges · 5 modules · CC̄=2.6*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `notification_stream` *(in wupbro.routers.notifications)* | 2 | 0 | 14 | **14** |
| `get_notification_manager` *(in wupbro.notifications)* | 3 | 8 | 2 | **10** |
| `post_event` *(in wupbro.routers.events)* | 2 | 0 | 7 | **7** |
| `list` *(in wupbro.storage.EventStore)* | 7 | 2 | 5 | **7** |
| `send_test_notification` *(in wupbro.routers.notifications)* | 2 | 0 | 6 | **6** |
| `subscribe` *(in wupbro.routers.notifications)* | 2 | 0 | 6 | **6** |
| `get_default_store` *(in wupbro.storage)* | 2 | 3 | 2 | **5** |
| `unsubscribe` *(in wupbro.routers.notifications)* | 2 | 0 | 4 | **4** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/wupbro
# nodes: 14 | edges: 12 | modules: 5
# CC̄=2.6

HUBS[20]:
  wupbro.routers.notifications.notification_stream
    CC=2  in:0  out:14  total:14
  wupbro.notifications.get_notification_manager
    CC=3  in:8  out:2  total:10
  wupbro.routers.events.post_event
    CC=2  in:0  out:7  total:7
  wupbro.storage.EventStore.list
    CC=7  in:2  out:5  total:7
  wupbro.routers.notifications.send_test_notification
    CC=2  in:0  out:6  total:6
  wupbro.routers.notifications.subscribe
    CC=2  in:0  out:6  total:6
  wupbro.storage.get_default_store
    CC=2  in:3  out:2  total:5
  wupbro.routers.notifications.unsubscribe
    CC=2  in:0  out:4  total:4
  wupbro.routers.notifications.update_subscription
    CC=2  in:0  out:4  total:4
  wupbro.routers.notifications.get_subscription
    CC=2  in:0  out:4  total:4
  wupbro.routers.notifications.list_subscriptions
    CC=1  in:0  out:3  total:3
  wupbro.notifications.NotificationManager.list_subscriptions
    CC=1  in:0  out:2  total:2
  wupbro.routers.events._store
    CC=1  in:0  out:1  total:1
  wupbro.routers.drivers._store
    CC=1  in:0  out:1  total:1

MODULES:
  wupbro.notifications  [2 funcs]
    list_subscriptions  CC=1  out:2
    get_notification_manager  CC=3  out:2
  wupbro.routers.drivers  [1 funcs]
    _store  CC=1  out:1
  wupbro.routers.events  [2 funcs]
    _store  CC=1  out:1
    post_event  CC=2  out:7
  wupbro.routers.notifications  [7 funcs]
    get_subscription  CC=2  out:4
    list_subscriptions  CC=1  out:3
    notification_stream  CC=2  out:14
    send_test_notification  CC=2  out:6
    subscribe  CC=2  out:6
    unsubscribe  CC=2  out:4
    update_subscription  CC=2  out:4
  wupbro.storage  [2 funcs]
    list  CC=7  out:5
    get_default_store  CC=2  out:2

EDGES:
  wupbro.routers.drivers._store → wupbro.storage.get_default_store
  wupbro.routers.events._store → wupbro.storage.get_default_store
  wupbro.routers.events.post_event → wupbro.notifications.get_notification_manager
  wupbro.notifications.NotificationManager.list_subscriptions → wupbro.storage.EventStore.list
  wupbro.notifications.get_notification_manager → wupbro.storage.get_default_store
  wupbro.routers.notifications.subscribe → wupbro.notifications.get_notification_manager
  wupbro.routers.notifications.list_subscriptions → wupbro.notifications.get_notification_manager
  wupbro.routers.notifications.get_subscription → wupbro.notifications.get_notification_manager
  wupbro.routers.notifications.update_subscription → wupbro.notifications.get_notification_manager
  wupbro.routers.notifications.unsubscribe → wupbro.notifications.get_notification_manager
  wupbro.routers.notifications.notification_stream → wupbro.notifications.get_notification_manager
  wupbro.routers.notifications.send_test_notification → wupbro.notifications.get_notification_manager
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Api (2)

**`API Integration Tests`**
- `GET /health` → `200`
- `GET /api/v1/status` → `200`
- `POST /api/v1/test` → `201`
- assert `status == ok`
- assert `response_time < 1000`

**`Auto-generated API Smoke Tests`**
- assert `_status < 500`
- assert `_status >= 200`
- detectors: FastAPIDetector

### Integration (1)

**`Auto-generated from Python Tests`**
- `GET /openapi.json` → `200`
- `POST /drivers/browserless/screenshot` → `200`
- `POST /drivers/dom-diff/capture` → `200`
- assert `_status == 200`
- assert `_status == 503`
- assert `_status == 200`

## Intent

WUP Browser Dashboard — FastAPI backend for WUP regression watcher
