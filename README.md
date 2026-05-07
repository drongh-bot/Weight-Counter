# Weight Counter

Industrial piece-counting desktop application built with **PySide6 + MVVM + Dependency Injection**.

Connects to an electronic scale via serial port, performs real-time weight stability
detection, automatic piece counting, anomaly detection, and production logging —
all with live chart and table visualization.

---

## Data Flow

```
Serial Port
  → SerialService         (raw data receive, timeout detection)
  → CheckerService        (parse + stability check via dual-window algorithm)
  → CounterService        (state machine ZERO→NORMAL→ABNORMAL + EMA weight learning)
  → UIService             (ViewModel — builds UIData, emits ui_changed signal)
  → MainWindow            (pure rendering — labels, table, scatter chart)
```

## Architecture

```
app/
├── core/                  Low-level drivers (serial, logger, sound, config, resources)
├── models/                Pure business logic (PieceCounter, WeightStabilityChecker)
├── services/              Service layer (serial, checker, counter, sound, log, ui)
├── controllers/           Flow orchestration (MainController — pipeline pattern)
├── views/                 UI rendering (MainWindow, PieceTable, PieceChart)
│   ├── widgets/           Custom widgets
│   └── ui_generated/      Qt Designer generated
└── resources/             Icons, sounds
```

### Key Design Principles

- **Dependency Injection** — all objects created and wired in `main.py`
- **CQS** — PieceCounter mutates state (Command), CounterService queries and builds results
- **Signal-driven UI** — UIService emits `ui_changed`; MainWindow renders, never touches business logic
- **No bare attribute access** — Controller communicates with services through methods only
- **Model layer is Qt-free** — unit-testable without a GUI

### Core Algorithms

**WeightStabilityChecker**

- Dual sliding windows (4-frame short, 8-frame long)
- Triple checks: speed (short-window range), trend (long-window range), standard deviation
- Lock mechanism with hysteresis unlock (2.5× threshold, 2-frame confirmation)
- Windows keep updating during lock to prevent stale data on unlock

**PieceCounter**

- Three-state FSM: ZERO → NORMAL → ABNORMAL
- EMA average weight learning with auto jump detection (50% change, 2-frame confirm)
- sqrt(n) statistical tolerance model for batch matching
- Abnormal auto-recovery with direction tracking

---

## Quick Start

```bash
pip install uv
uv sync
uv run main.py
```

---

## Config

Edit `config.toml`:

```toml
[parameters]
initial_mini_weight = 0.5
tolerance_percent = 10.0
stability_threshold = 0.02
max_batch_pieces = 1
initial_single_pieces = 1
force_pieces = 0
target_pieces = 100
decimal_places = 2

[stability]
short_win = 4
long_win = 8
stable_count = 3
unlock_confirm = 2
unlock_factor = 2.5

[counting]
dynamic_weight_ratio = 0.5
initial_min_ratio = 0.3
jump_threshold_ratio = 0.5
jump_confirm_times = 2
early_learn_pieces = 5
ema_alpha_min = 0.05
ema_alpha_max = 0.30
count_rounding_tolerance = 0.2
abnormal_recover_factor = 1.5

[serial]
port = "COM1"
baud_rate = 9600
timeout_millis = 2000

[ui]
splitter_sizes = [140, 199]
```

---
## Testing

```bash
uv run pytest tests/ -v          # 95 tests: model → service → controller
uv run mypy app                  # Type check
```

### Test coverage

| Layer | Tests |
|-------|-------|
| model | 43 (Qt-free, plain pytest) |
| service | 31 (uses `qapp` fixture from `pytest-qt`) |
| builder | 8 (Qt-free) |
| controller | 12 (uses `qapp` fixture) |

---
## Hardware Requirement

The app requires a serial port with a connected electronic scale. `config.toml` must set
`[serial].port` to a valid COM port. Without hardware, serial operations will fail.

---
## Packaging

```bash
uv run pyinstaller main.spec --clean
```

Output: `dist/WeightCounter/`

---

## Tech Stack

| Tech         | Purpose                 |
| ------------ | ----------------------- |
| Python 3.13+ | Language                |
| PySide6      | Qt for Python UI        |
| PyQtGraph    | Real-time scatter chart |
| TOML         | Configuration format    |
| UV          | Package manager         |
| PyInstaller  | Application packaging   |

---

## License

MIT
