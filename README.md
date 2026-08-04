# Weight Counter（称重计数）

工业计件桌面应用：**PySide6 + 手工依赖注入**。

通过串口连接电子秤，实时稳重判定、自动计件、异常检测与生产日志，并带表格与散点图展示。

---

## 数据流

```
串口
  → SerialService         （读写 + 超时；统一 data_received）
  → WeightInputService    （解析 + 双窗口稳重）
  → CounterService        （PieceCounter 状态机 + 上升沿）
  → UiBridge              （to_count_view + 件数/状态栏/按钮/当前重量信号）
  → MainWindow            （只负责渲染标签、表、图）
```

## 架构

```
app/
├── core/                  驱动（csv_writer、sound_player、log_config、resource_manager）
├── models/                纯业务（PieceCounter、Thresholds、Tolerance、WeightLearner、WeightStabilizer、Params）
├── services/              串口、重量输入、计件、生产 CSV、配置
├── controllers/           MainController — 每帧顺序编排
├── presentation/          UiBridge、StatusBar、to_count_view、view_models、styles
├── views/                 MainWindow、PieceTable、PieceChart
│   ├── widgets/
│   └── ui_generated/      Qt Designer 生成
└── resources/             图标、音效
```

### 设计要点

- **依赖注入** — 对象在 `main.py` 创建并接线
- **FSM 与门面** — `PieceCounter.on_stable_weight` 改状态；`CounterService.process` 认边沿并产出 `CountFrame`
- **信号驱动 UI** — `UiBridge` 推送界面数据；`MainWindow` 只渲染（勿与 `Ui_MainWindow` 混淆）
- **禁止乱穿属性** — Controller 只调服务方法
- **Model / 计件服务无 Qt** — 可脱离界面单测
- **参数生效时机** — 多数界面计件参数点 Start 才拷进算法；`target_pieces` 随时跟界面，且不写入配置文件

### 核心算法

**稳重（WeightStabilizer）**

- 双滑动窗口（默认短 5 / 长 10，见 `config.toml` 的 `[stability]`）
- 三重判定：速度（短窗极差）、趋势（长窗极差）、标准差
- 锁定后滞回解锁（默认 2.5 倍阈值、连续 2 帧确认）
- 锁定期间窗口仍更新，避免解锁时数据过旧

**计件（PieceCounter）**

- 三态：ZERO → NORMAL → ABNORMAL
- EMA 学均重，跳变检测（约 50% 变化、连续 2 帧确认）
- √n 统计公差做批量匹配
- 异常可按方向自动恢复

---

## 快速开始

```bash
pip install uv
uv sync
uv run main.py
```

---

## 配置

唯一配置文件为 `config.toml`，由下列两者配合：

- **`Params`**（`app/models/params.py`）— 纯数据，无 I/O
- **`ConfigService`**（`app/services/config_service.py`）— 按 `_SECTION_MAP` 读写其中一部分字段

### 路径（ResourceManager）

| 方法 | 用途 | 开发 | 打包 |
| ---- | ---- | ---- | ---- |
| `get_resource` | 图标、音效等只读资源 | 项目根 | `_MEIPASS` |
| `get_external` | `config.toml`、日志等可写文件 | 项目根 | EXE 所在目录 |

均返回 `Path`；需要字符串时再 `str(...)`。

### 仅运行时有效（不写进 config.toml）

| 字段 | 含义 |
| ----- | ------- |
| `target_pieces` | 目标件数；计件过程中可随时改，读共享 `Params`，退出不保存（默认 100） |

### 可持久化参数示例

编辑 `config.toml`：

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

## 测试

```bash
uv run pytest tests/ -v          # 约 148 条
uv run mypy app                  # 类型检查
```

测试文件分层表见 `AGENTS.md`。

---

## 硬件

需串口电子秤；`config.toml` 的 `[serial].port` 设为有效 COM 口。无硬件时串口相关操作会失败。

---

## 打包

```bash
uv run pyinstaller main.spec --clean -y
```

产物：`dist/WeightCounter/`。

`main.spec` 关掉默认 Qt hooks，只收集用到的 PySide6 模块，平台插件只打入 `qwindows.dll`，并踢掉多余 DLL。务必用 spec，不要裸跑 `pyinstaller main.py`。

---

## 技术栈

| 技术 | 用途 |
| ------------ | ----------------------- |
| Python 3.13+ | 语言 |
| PySide6 | Qt for Python 界面 |
| PyQtGraph | 实时散点图 |
| TOML | 配置 |
| UV | 包管理 |
| PyInstaller | 打包 |

---

## License

MIT
