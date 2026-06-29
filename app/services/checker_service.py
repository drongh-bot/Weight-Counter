# app/services/checker_service.py
import logging

from app.models.params import Params
from app.models.weight_stability_checker import WeightStabilityChecker

logger = logging.getLogger(__name__)


class CheckerService:
    """
    CheckerService (refactored version)
    - Responsible for weight parsing + stability checking
    - No dependency on UI or Controller
    - Provides parse() / check() / reset()
    """

    def __init__(self, params: Params) -> None:
        self.params = params

        # initialize stability checker (thresholds set once)
        self._stability_checker = WeightStabilityChecker(
            short_win=params.stability_short_win,
            long_win=params.stability_long_win,
            stable_count=params.stability_stable_count,
            unlock_confirm=params.stability_unlock_confirm,
            unlock_factor=params.stability_unlock_factor,
            base_threshold=params.stability_threshold,
        )

    # ============================================================
    # Parse weight (string -> float)
    # ============================================================
    def parse(self, raw: str) -> float | None:
        """
        Returns the parsed weight, or None if parsing fails
        """
        try:
            raw = raw.strip().upper()
            if not raw or not any(c.isdigit() for c in raw):
                return None

            if "," in raw:
                raw = raw.split(",")[-1].strip()

            for ch in ["KG", "G", "NT", "N", " "]:
                raw = raw.replace(ch, "")

            weight = float(raw)
            return weight

        except (ValueError, AttributeError):
            logger.warning("解析失败: %s", raw)
            return None

    # ============================================================
    # Stability check
    # ============================================================
    def check(self, weight: float) -> float | None:
        """
        Returns the stable weight, or None if unstable
        """
        return self._stability_checker.check_stability(weight)

    # ============================================================
    # Reset
    # ============================================================
    def reset(self) -> None:
        self._stability_checker.reset()

    def apply_params(self) -> None:
        self._stability_checker.set_base_threshold(self.params.stability_threshold)

    # ============================================================
    # Last stable value
    # ============================================================
    @property
    def last_stable_weight(self) -> float | None:
        return self._stability_checker.last_stable_weight
