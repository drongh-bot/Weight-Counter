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
python main.py
```

---

## Config

Edit `config.toml`:

```toml
[serial]
port = "COM1"
baud_rate = 9600

[parameters]
initial_mini_weight = 0.5
tolerance_percent = 20.0
stability_threshold = 0.02
max_batch_pieces = 1
target_pieces = 12
decimal_places = 2
```

---

## Packaging

```bash
pyinstaller main.spec
```

Output: `dist/WeightCounter/`

---

## Tech Stack

| Tech | Purpose |
|------|---------|
| Python 3.13+ | Language |
| PySide6 | Qt for Python UI |
| PyQtGraph | Real-time scatter chart |
| TOML | Configuration format |
| PyInstaller | Application packaging |

---

## License

MIT
