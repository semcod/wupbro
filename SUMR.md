# wupbro

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Dependencies](#dependencies)
- [Source Map](#source-map)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `wupbro`
- **version**: `0.1.10`
- **python_requires**: `>=3.9`
- **license**: {'text': 'Apache-2.0'}
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, testql(3), app.doql.less, goal.yaml, .env.example, src(4 mod), project/(5 analysis files)

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

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

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

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 15f 1677L | python:11,shell:2,toml:1,yaml:1 | 2026-04-29
# CC̄=2.6 | critical:0/47 | dups:0 | cycles:1

HEALTH[0]: ok

REFACTOR[1]:
  1. break 1 circular dependencies

PIPELINES[37]:
  [1] Src [_store]: _store → get_default_store
      PURITY: 100% pure
  [2] Src [dom_diff_capture]: dom_diff_capture
      PURITY: 100% pure
  [3] Src [browserless_screenshot]: browserless_screenshot
      PURITY: 100% pure
  [4] Src [anomaly_report]: anomaly_report
      PURITY: 100% pure
  [5] Src [driver_health]: driver_health
      PURITY: 100% pure

LAYERS:
  wupbro/                         CC̄=2.6    ←in:10  →out:0
  │ notifications              283L  1C   15m  CC=14     ←2
  │ notifications              234L  0C   10m  CC=2      ←0
  │ drivers                    129L  0C    5m  CC=3      ←0
  │ models                     123L  8C    0m  CC=0.0    ←0
  │ storage                    110L  1C    8m  CC=7      ←3
  │ events                      65L  0C    5m  CC=2      ←0
  │ main                        45L  0C    1m  CC=1      ←0
  │ dashboard                   24L  0C    2m  CC=1      ←0
  │ __main__                    21L  0C    1m  CC=1      ←0
  │ __init__                     7L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! goal.yaml                  511L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              74L  0C    0m  CC=0.0    ←0
  │ project.sh                  49L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │

COUPLING:
                          wupbro  wupbro.routers
          wupbro              ──             ←10  hub
  wupbro.routers              10              ──  !! fan-out
  CYCLES: 1
  HUB: wupbro/ (fan-in=10)
  SMELL: wupbro.routers/ fan-out=10 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 0 groups | 11f 1042L | 2026-04-29

SUMMARY:
  files_scanned: 11
  total_lines:   1042
  dup_groups:    0
  dup_fragments: 0
  saved_lines:   0
  scan_ms:       4354
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 47 func | 8f | 2026-04-29

NEXT[0]: no refactoring needed

RISKS[0]: none

METRICS-TARGET:
  CC̄:          2.6 → ≤1.8
  max-CC:      14 → ≤7
  god-modules: 0 → 0
  high-CC(≥15): 0 → ≤0
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  (first run — no previous data)
```

## Intent

WUP Browser Dashboard — FastAPI backend for WUP regression watcher
