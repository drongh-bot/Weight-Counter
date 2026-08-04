# app/services/weight_input_service.py
import logging

from app.models.params import Params
from app.models.weight_stabilizer import WeightStabilizer

logger = logging.getLogger(__name__)


class WeightInputService:
    """
    重量输入服务：
    - 解析串口重量字符串
    - 经 WeightStabilizer 稳定化
    - 不依赖 UI 或 Controller
    - 提供 parse() / stabilize() / reset()
    """

    def __init__(self, params: Params) -> None:
        """用共享 Params 构造稳重器（窗口参数在构造时拷贝）。"""
        self.params = params
        self._stabilizer = WeightStabilizer.from_params(params)

    def parse(self, raw: str) -> float | None:
        """解析串口重量字符串；成功返回 float，失败返回 None。"""
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
        """稳定则返回稳定重量，否则 None。"""
        return self._stabilizer.stabilize(weight)

    def reset(self) -> None:
        """重置稳重器窗口与锁定状态。"""
        self._stabilizer.reset()

    def apply_start_params(self) -> None:
        """Start 时将 START_SYNC 稳定阈值复制进 stabilizer。"""
        self._stabilizer.apply_start_params(self.params)

    @property
    def stability_threshold(self) -> float:
        """当前生效的稳定阈值（Start 快照）。"""
        return self._stabilizer.stability_threshold

