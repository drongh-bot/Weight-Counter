# app/services/checker_service.py
from PySide6.QtCore import QObject

from app.models.weight_stability_checker import WeightStabilityChecker


class CheckerService(QObject):
    """
    CheckerService (refactored version)
    - Responsible for weight parsing + stability checking
    - No dependency on UI or Controller
    - Provides parse() / check() / reset()
    """

    def __init__(self, params):
        super().__init__()

        self.params = params

        # initialize stability checker (thresholds set once)
        self.checker = WeightStabilityChecker(base_threshold=params.stability_threshold)

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
            return None

    # ============================================================
    # Stability check
    # ============================================================
    def check(self, weight: float) -> float | None:
        """
        Returns the stable weight, or None if unstable
        """
        return self.checker.update(weight)

    # ============================================================
    # Reset
    # ============================================================
    def reset(self):
        self.checker.reset()

    # ============================================================
    # Last stable value
    # ============================================================
    @property
    def last_stable_weight(self):
        return self.checker.last_stable_weight
