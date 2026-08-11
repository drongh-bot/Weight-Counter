# Weight Counter — 项目指南

工业计件桌面应用：PySide6 + 手工依赖注入。

## 架构

```
app/
├── core/                  驱动（csv_writer、sound_player、log_config、resource_manager）
├── models/                纯业务（PieceCounter、Thresholds、Tolerance、WeightLearner、WeightStabilizer、Params、CountSnapshot）
├── services/              串口、重量输入、计件、生产 CSV、配置
├── controllers/           MainController — 每帧顺序编排
├── presentation/          UiBridge、StatusBar、count_labels、view_models（含 Styles）
├── views/                 界面渲染（MainWindow、PieceTable、PieceChart）
│   ├── widgets/           自定义控件
│   └── ui_generated/      Qt Designer 生成代码
└── resources/             图标、音效
```

## 设计原则（必须遵守）

- **DI**：所有对象在 `main.py` 创建并接线
- **FSM 与门面**：`PieceCounter.on_stable_weight` 改状态；`CounterService.process` 认边沿并产出 `CountFrame`
- **信号驱动 UI**：`presentation.UiBridge` 发 `count_changed`（`CountSnapshot`）/ `bar_snapshot_changed` / `button_status_changed` / `actual_weight_changed`；`MainWindow` 只渲染并做计件区数字格式化，不碰业务。勿与 Qt Designer 的 `Ui_MainWindow` 混淆；注入属性名为 `ui_bridge`
- **状态栏**：对外只用 `StatusBar` 的 `on_*` → `BarSnapshot`；解析/通讯与消息锁存为内部细节
- **禁止裸属性乱穿**：Controller 只通过服务方法访问
- **Model 无 Qt**：可单测、无 I/O（`Params` 与 `ConfigService` 分工）
- **业务服务 / Controller 无 Qt**：`CounterService`、`WeightInputService`、`MainController` 为普通类；`SerialService`、`CsvLogService`、`UiBridge` 等继承 `QObject`
- **Presentation ≠ services**：`count_labels`（`state_label` / `delta_style`）/ `UiBridge` / `StatusBar` 放在 `presentation/`；计件区信号直接传 `CountSnapshot`，格式化在 `MainWindow`

## 技术栈

| 工具 | 用途 |
| ----------- | ----------------------- |
| Python 3.13 | 语言 |
| PySide6 | Qt for Python 界面 |
| PyQtGraph | 实时散点图 |
| TOML | 配置格式 |
| UV | 包管理 |
| PyInstaller | 打包 |

## 常用命令

```
uv sync                          # 安装依赖
uv run main.py                   # 运行
uv run pyinstaller main.spec     # 打包到 dist/WeightCounter/（建议加 --clean -y）
uv run pytest tests/ -v          # 全部测试
uv run mypy app                  # 类型检查
```

## 测试

Model 与 `CounterService` / `WeightInputService` 测试无 Qt；`UiBridge`、Controller 测试使用 pytest-qt 的 `qapp`。

| 文件 | 层级 | 约条数 |
|------|-------|-------|
| `tests/test_weight_stabilizer.py` | model | 12 |
| `tests/test_piece_counter.py` | model | 37 |
| `tests/test_count_labels.py` | presentation | 6 |
| `tests/test_weight_input_service.py` | service | 14 |
| `tests/test_counter_service.py` | service | 19 |
| `tests/test_config_service.py` | service | 7 |
| `tests/test_status_bar.py` | presentation | 13 |
| `tests/test_ui_bridge.py` | presentation | 11 |
| `tests/test_piece_table.py` | view | 4 |
| `tests/test_piece_chart.py` | view | 5 |
| `tests/test_controller.py` | controller | 27 |

合计约 **155** 条。

## PySide6 QSignalSpy 注意（6.8.3）

与网上多数 PyQt5/PySide2 示例不同：

- `spy.count()` — 方法，不是 `len(spy)`
- `spy.at(i)` — 按下标取，不是 `spy[i]`
- 没有 `.clear()` — 需要时新建 spy
- `spy.at(0)` 得到 `[arg]` — 单参数信号用 `spy.at(0)[0]`

## 硬件依赖

需要串口电子秤。无硬件时串口操作会失败。`config.toml` 的 `[serial].port` 须为有效 COM 口。

## Qt Designer 生成代码

`app/views/ui_generated/form.py` 由 Designer 生成，勿手改。

## PyInstaller 打包注意

`main.spec` 关掉默认 Qt hooks，只收集 `QtCore` / `QtGui` / `QtWidgets` / `QtSerialPort`；
平台插件**只打入** `qwindows.dll`（不再整目录再筛选）；并踢掉无关 DLL / 插件目录。
务必用 spec 打包：`uv run pyinstaller main.spec --clean -y`，不要裸跑 `pyinstaller main.py`。

## 路径（ResourceManager）

- `get_resource_root()` / `get_external_root()`：两类根目录（公开；需要根路径或自行拼接时用）
- `get_resource(...)`：只读静态资源（图标、音效）→ `Path`；打包用 `_MEIPASS`
- `get_external(...)`：可读写（`config.toml`、日志目录）→ `Path`；打包用 EXE 旁目录
- 开发根目录：含 `pyproject.toml` 与 `app/` 的项目根
- 需要 `str` 时再 `str(...)`（如 `QIcon`、`winsound`）

## 配置

`config.toml` 管串口、波特率、计件与稳重等参数。

- **`Params`**（`app/models/params.py`）：纯数据，无 I/O。窗口与服务共享一份（`CounterService` / `WeightInputService` 持有；`MainController` 不持有）。字段旁注释标明：多数界面计件参数点 Start 才拷进算法；`target_pieces` 改了立刻生效且不落盘。`__post_init__` 按界面范围与算法下限夹紧非法值（含手改 config / 代码赋值构造时）。
- **`ConfigService`**：只读写 `_SECTION_MAP` 里的键（不含 `target_pieces`）。文件损坏则加载抛错。
- **Start 拷贝**：服务层无参 `apply_start_params()` 从各自持有的共享 `Params` 把界面可调计件/稳定阈值拷进 `PieceCounter` / `WeightStabilizer`（模型层仍显式接收 `params`）。算法不持有共享 `Params` 引用；跑起来中途改这些字段，要再点 Start 才生效。
- **`target_pieces`**：`CounterService` 每帧稳重后从共享 `Params` 读取；默认 `100`；退出不保存。

## 核心算法

- **WeightStabilizer**：双滑动窗口（默认短 5 / 长 10，见 `[stability]`）+ 速度/趋势/标准差三重判定 + 滞回解锁
- **PieceCounter**：三态 FSM（ZERO → NORMAL → ABNORMAL）+ EMA 学均重 + √n 统计公差（`Tolerance.band` / `is_within_tolerance`；`min_tol` 仅在 `Tolerance`；异常恢复见 `_recover_limit`）。件数减到 0 时回 ZERO（保留当前空秤基准，便于非零皮重下重新计件）。跳变未确认前不写入 EMA。

## 计件结果类型

- **`CountSnapshot`**：当前件数、均重、公差、`decimal_places` 等（给界面；字段均必填）
- **`CountFrame`**：快照 + 本帧边沿（刚加件 / 刚异常 / 刚达目标）
- **UiBridge 去重**：计件信号只比较展示字段（去掉 Frame 边沿），避免无意义重绘
