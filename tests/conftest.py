"""Shared fixtures mirroring main.py DI wiring."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from app.controllers.main_controller import MainController
from app.models.params import Params
from app.services.counter_service import CounterService
from app.services.csv_log_service import CsvLogService
from app.services.serial_service import SerialService
from app.services.sound_service import SoundService
from app.presentation.ui_service import UIService
from app.services.weight_input_service import WeightInputService


@pytest.fixture
def make_controller(qapp) -> Callable[..., tuple[MainController, UIService]]:
    """Build MainController + UIService like main.py (params defaults for tests)."""

    def _factory(
        *,
        sound_service: SoundService | None = None,
        **param_overrides: object,
    ) -> tuple[MainController, UIService]:
        params = Params()
        params.target_pieces = 10
        params.max_batch_pieces = 4
        for key, value in param_overrides.items():
            setattr(params, key, value)

        ui = UIService()
        controller = MainController(
            ui_service=ui,
            serial_service=SerialService(2000),
            counter_service=CounterService(params),
            weight_input_service=WeightInputService(params),
            sound_service=sound_service or SoundService(),
            csv_log_service=CsvLogService(),
            params=params,
        )
        return controller, ui

    return _factory
