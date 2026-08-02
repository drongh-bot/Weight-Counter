# app/services/weight_input_service.py
import logging

from app.models.params import Params
from app.models.weight_stabilizer import WeightStabilizer

logger = logging.getLogger(__name__)


class WeightInputService:
    """
    Weight input service:
    - Parse serial weight strings
    - Stabilize via WeightStabilizer
    - No dependency on UI or Controller
    - Provides parse() / stabilize() / reset()
    """

    def __init__(self, params: Params) -> None:
        self.params = params
        self._stabilizer = WeightStabilizer.from_params(params)

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

    def stabilize(self, weight: float) -> float | None:
        """
        Returns the stable weight, or None if unstable
        """
        return self._stabilizer.stabilize(weight)

    # ============================================================
    # Reset
    # ============================================================
    def reset(self) -> None:
        self._stabilizer.reset()

    def apply_start_params(self) -> None:
        self._stabilizer.apply_start_params(self.params)

