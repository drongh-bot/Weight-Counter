# Weight Counter

Industrial piece-counting desktop application built with **PySide6 + manual DI**.

Connects to an electronic scale via serial port, performs real-time weight stability
detection, automatic piece counting, anomaly detection, and production logging —
all with live chart and table visualization.

---

## Data Flow

```
Serial Port
  → SerialService         (port I/O + timeout; single data_received outlet)
  → WeightInputService    (parse + stabilize via dual-window algorithm)
  → CounterService        (PieceCounter FSM + rising-edge events)
  → UiBridge              (to_count_view + signals for count/bar/button/weight)
  → MainWindow            (pure rendering — labels, table, scatter chart)
```

## Architecture

```
app/
├── core/                  Drivers (csv_writer, sound_player, log_config, resources)
├── models/                Pure business logic (PieceCounter, Thresholds, Tolerance, WeightLearner, WeightStabilizer, Params)
├── services/              serial, weight_input, counter, csv_log, config
├── controllers/           MainController — sequential per-frame orchestration
├── presentation/          UiBridge, StatusBar, to_count_view, view_models, styles
├── views/                 UI rendering (MainWindow, PieceTable, PieceChart)
│   ├── widgets/           Custom widgets
│   └── ui_generated/      Qt Designer generated
└── resources/             Icons, sounds
```

### Key Design Principles

- **Dependency Injection** — all objects created and wired in `main.py`
- **FSM vs facade** — `PieceCounter.on_stable_weight` mutates state; `CounterService.process` detects edges and builds `CountFrame`
- **Signal-driven UI** — `UiBridge` emits view snapshots; MainWindow renders only (not Qt Designer `Ui_MainWindow`)
- **No bare attribute access** — Controller communicates with services through methods only
- **Model layer is Qt-free** — unit-testable without a GUI; `CounterService` and `WeightInputService` are also Qt-free
- **Params freshness** — most UI count params copied on Start; `target_pieces` follows the UI anytime and is not persisted

### Core Algorithms

**WeightStabilizer**

- Dual sliding windows (5-frame short, 10-frame long — configurable via `[stability]` in `config.toml`)
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

`config.toml` is the only configuration file. It is managed by:

- **`Params`** (`app/models/params.py`) — pure `@dataclass` holding all application parameters, no I/O
- **`ConfigService`** (`app/services/config_service.py`) — loads/saves a **subset** of `Params` ↔ `config.toml`

### Runtime-only parameters (not in `config.toml`)

Some UI fields live on `Params` but are **not persisted** — they apply to the current production run only:

| Field | Purpose |
| ----- | ------- |
| `target_pieces` | Batch target count; editable anytime during counting via the UI spinbox |

`CounterService` reads `target_pieces` live from the shared `Params` object on every stable weight frame (no restart or Start click required). The default is `100` (`Params.target_pieces`); it is not written back to disk on exit.

### Persisted parameters

Edit `config.toml`:

```toml
[parameters]
initial_min_weight = 0.5
tolerance_percent = 20.0
stability_threshold = 0.02
max_batch_pieces = 1
initial_single_pieces = 5
decimal_places = 2

[stability]
stability_short_win = 5
stability_long_win = 10
stability_stable_count = 3
stability_unlock_confirm = 2
stability_unlock_factor = 2.5

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
uv run pytest tests/ -v          # 148 tests
uv run mypy app                  # Type check
```

详见 `AGENTS.md` 中的测试文件表。

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
| UV           | Package manager         |
| PyInstaller  | Application packaging   |

---

## License

MIT
