"""与 main.py 相同的 DI 组装共享夹具。"""

from __future__ import annotations

from collections.abc import Callable, Iterator

import pytest

from app.controllers.main_controller import MainController
from app.models.count_snapshot import CountSnapshot
from app.models.counter_state import CounterState
from app.models.params import Params
from app.presentation.ui_bridge import UiBridge
from app.services.counter_service import CounterService
from app.services.csv_log_service import CsvLogService
from app.services.serial_service import SerialService
from app.core.sound_player import SoundPlayer
from app.services.weight_input_service import WeightInputService

# 默认稳重：long_win=10 + stable_count=3 → 连续同重约 12 帧可稳定锁定。
STABLE_FRAMES = 12


def feed_stable(
    controller: MainController,
    raw: str,
    *,
    frames: int = STABLE_FRAMES,
) -> None:
    """连续喂入相同原始重量串，直到稳重器锁定（默认 12 帧）。"""
    for _ in range(frames):
        controller._on_raw_data(raw)


def make_count_snapshot(**overrides: object) -> CountSnapshot:
    """构造 CountSnapshot；未传字段用 ZERO 默认值。"""
    snap = CountSnapshot(
        abnormal_high=False,
        abnormal_low=False,
        state=CounterState.ZERO,
        delta=0.0,
        avg_weight=0.0,
        tolerance_high=0.0,
        tolerance_low=0.0,
        total_pieces=0,
        last_stable_weight=0.0,
        baseline_weight=0.0,
        piece_weights=[],
        decimal_places=2,
    )
    for key, value in overrides.items():
        setattr(snap, key, value)
    return snap


@pytest.fixture
def make_controller(
    qapp,
) -> Iterator[Callable[..., tuple[MainController, UiBridge]]]:
    """按 main.py 方式组装 MainController + UiBridge（测试用默认参数）。"""

    controllers: list[MainController] = []

    def _factory(
        *,
        sound_player: SoundPlayer | None = None,
        **param_overrides: object,
    ) -> tuple[MainController, UiBridge]:
        params = Params()
        params.target_pieces = 10
        params.max_batch_pieces = 4
        for key, value in param_overrides.items():
            setattr(params, key, value)

        ui_bridge = UiBridge()
        controller = MainController(
            ui_bridge=ui_bridge,
            serial_service=SerialService(2000),
            counter_service=CounterService(params),
            weight_input_service=WeightInputService(params),
            sound_player=sound_player or SoundPlayer(),
            csv_log_service=CsvLogService(),
        )
        controllers.append(controller)
        return controller, ui_bridge

    yield _factory

    for controller in controllers:
        controller.shutdown()
