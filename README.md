# 称重计数系统（Weighing Counter System）

基于 **PySide6 + MVVM + 依赖注入** 的工业称重计数程序。
通过串口读取电子秤数据，进行稳定性判断、自动计数、异常检测、日志记录，并提供实时 UI 展示。

---

## 项目结构

```
robust1BigScale/
├── main.py                        # 入口 + 依赖注入
├── config.toml                    # 配置文件
├── pyproject.toml                 # 项目配置
├── main.spec                      # PyInstaller 打包配置
│
├── app/
│   ├── controllers/
│   │   └── main_controller.py     # 业务流程编排（管线模式）
│   │
│   ├── models/                    # 纯逻辑模型层（零 Qt 依赖）
│   │   ├── piece_counter.py       # 核心计数引擎（状态机 + EMA + sqrt(n) 容差）
│   │   ├── weight_stability_checker.py  # 稳定检测器（双窗口 + 锁定迟滞）
│   │   ├── parameter_manager.py   # 参数加载/保存
│   │   └── biz_result.py          # 跨层 DTO（BizResult + BizState）
│   │
│   ├── services/                  # 业务逻辑层
│   │   ├── serial_service.py      # 串口管理、数据收/发、超时检测
│   │   ├── checker_service.py     # 重量解析 + 稳定性判
│   │   ├── counter_service.py     # 计数逻辑、边缘触发、结果构建
│   │   ├── sound_service.py       # 声音播放
│   │   ├── log_service.py         # 异步日志（后台线程 + 队列）
│   │   └── ui/                    # ViewModel 层
│   │       ├── ui_service.py      # UI 状态管理（信号驱动）
│   │       ├── models.py          # 数据模型（UIData / BizData / StatusData / ButtonState）
│   │       ├── builders.py        # 数据构建器（BizBuilder / StatusBuilder）
│   │       └── styles.py          # 样式常量
│   │
│   ├── core/                      # 底层驱动层
│   │   ├── serial.py              # 串口驱动（QSerialPort 封装）
│   │   ├── logger.py              # CSV 日志（按日切分 + 线程安全）
│   │   ├── sound.py               # 声音播放（winsound）
│   │   ├── config_manager.py      # TOML 配置读写（单例 + 线程安全）
│   │   └── resource_manager.py    # 资源路径解析
│   │
│   ├── views/                     # UI 层
│   │   ├── main_window.py         # 主窗口
│   │   ├── ui_generated/          # Qt Designer 生成
│   │   │   ├── form.ui
│   │   │   └── form.py
│   │   └── widgets/
│   │       ├── piece_chart.py     # 散点图（pyqtgraph）
│   │       └── piece_table.py     # 数据表格
│   │
│   └── resources/                 # 资源文件
│       ├── icons/
│       └── sounds/
│
├── log/                           # 日志目录
│   ├── error/
│   ├── event/
│   └── production/
│
└── tools/                         # 工具脚本
```

---

## 架构

### 分层依赖（单向）

```
core/      驱动层    (serial, logger, sound, config)
  ↓
models/    模型层    (PieceCounter, WeightStabilityChecker)   零 Qt 依赖
  ↓
services/  业务层    (CheckerService, CounterService, ...)    透传 + 编排
  ↓
controllers/ 编排层  (MainController)                        管线模式
  ↓
views/     UI 层    (MainWindow, PieceChart, PieceTable)     纯渲染
```

### 数据流

```
串口硬件
  → SerialService  (data_received 信号)
  → MainController._handle_parse()      解析 + 通讯状态
  → MainController._handle_stability_check()  稳定检测
  → MainController._handle_pre_process()      预处理 (force_accept / clear_abnormal)
  → CounterService.process()           计数
  → MainController._handle_result()    UI 更新 + 声音 + 日志
```

### 核心算法

#### 稳定检测（WeightStabilityChecker）
- **双窗口滑动**：短窗 4 帧 + 长窗 8 帧
- **三重检测**：速度检测（短窗极差）、趋势检测（长窗极差）、标准差检测
- **锁定机制**：稳定后锁定重量，带迟滞解锁（2.5 倍阈值 + 2 帧确认）
- 锁定期间继续更新窗口，确保解锁后数据不陈旧

#### 计数引擎（PieceCounter）
- **三态状态机**：ZERO → NORMAL → ABNORMAL
- **EMA 平均片重学习**：动态调整学习率（5%~30%），自动跳变检测
- **sqrt(n) 容差模型**：基于统计学的批量容差判断
- **异常自动恢复**：动态方向跟踪 + 1.5 倍松弛恢复阈值

---

## 依赖注入（main.py）

```python
params = ParameterManager()
ui_service = UIService()
serial_service = SerialService()
counter_service = CounterService(params)
checker_service = CheckerService(params)
sound_service = SoundService()
log_service = LogService()

controller = MainController(ui_service, serial_service, counter_service,
                            checker_service, sound_service, log_service, params)
window = MainWindow(ui_service, controller, params)
```

---

## 设计原则

- **CQS**：PieceCounter 只做状态转换（Command），不返回值；CounterService 通过 before/after 快照构建 BizResult（Query）
- **无裸属性**：Controller 通过 `consume_*()` 方法消费边缘标志，不直接修改 Service 内部状态
- **信号驱动**：UIService 通过 `ui_changed` 信号驱动 View，Controller 不操作 UI 控件
- **类型现代化**：全程 `float | None` / `list[float]` / `deque[float]`，无 `typing.Optional` / `Deque` / `List`

---

## 🚀 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.13+ | 编程语言 |
| PySide6 | Qt for Python |
| PyQtGraph | 实时数据图表 |
| TOML | 配置文件 |
| PyInstaller | 应用打包 |

---

## 🧪 可测试性

Model 层完全解耦（零 Qt 依赖），可独立单元测试：

```python
checker = WeightStabilityChecker()
checker.update(10.0)     # → None (窗口未满)
# ... 8 帧后 ...
checker.update(10.01)    # → 10.0 (稳定锁定)

counter = PieceCounter(initial_mini_weight=0.5, tolerance_percent=10.0)
counter.process(10.5)    # 第一片
counter.process(20.3)    # 第二片
assert counter.total_pieces == 2
```
