"""与 main.py 相同的 DI 组装共享夹具。"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from app.controllers.main_controller import MainController
from app.models.count_result import CountResult
from app.models.counter_state import CounterState
from app.models.params import Params
from app.presentation.ui import UiBridge
from app.services.counter_service import CounterService
from app.services.csv_log_service import CsvLogService
from app.services.serial_service import SerialService
from app.core.sound import SoundService
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


def make_count_result(**overrides: object) -> CountResult:
    """构造 CountResult；未传字段用 ZERO 默认值。"""
    result = CountResult(
        added=False,
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
    )
    for key, value in overrides.items():
        setattr(result, key, value)
    return result


@pytest.fixture
def make_controller(qapp) -> Callable[..., tuple[MainController, UiBridge]]:
    """按 main.py 方式组装 MainController + UiBridge（测试用默认参数）。"""

    def _factory(
        *,
        sound_service: SoundService | None = None,
        **param_overrides: object,
    ) -> tuple[MainController, UiBridge]:
        params = Params()
        params.target_pieces = 10
        params.max_batch_pieces = 4
        for key, value in param_overrides.items():
            setattr(params, key, value)

        ui = UiBridge()
        controller = MainController(
            ui=ui,
            serial_service=SerialService(2000),
            counter_service=CounterService(params),
            weight_input_service=WeightInputService(params),
            sound_service=sound_service or SoundService(),
            csv_log_service=CsvLogService(),
        )
        return controller, ui

    return _factory
