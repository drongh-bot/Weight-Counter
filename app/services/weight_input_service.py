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
        """持有共享 Params，并用其构造稳重器（窗口参数在构造时拷贝）。"""
        self._params = params
        self._stabilizer = WeightStabilizer(
            short_maxlen=params.stability_short_win,
            long_maxlen=params.stability_long_win,
            stable_count=params.stability_stable_count,
            unlock_confirm=params.stability_unlock_confirm,
            unlock_factor=params.stability_unlock_factor,
            stability_threshold=params.stability_threshold,
        )

    def parse(self, raw: str) -> float | None:
        """解析串口重量字符串；成功返回 float，失败返回 None。"""
        # str() 兜底：万一上游传了非字符串，也不会在这儿抛 AttributeError，
        # 会一路走到下面的 float() 失败分支，老实返回 None
        text = str(raw).strip().upper()
        if not text:
            return None

        # 逗号分隔时取最后一段（秤可能先发状态码，如 "ST,+123.4"）
        if "," in text:
            text = text.split(",")[-1].strip()
        if not text:
            return None

        # "+  1.234" → "+1.234"；其余词（ST、KG…）float 失败就跳过
        while "+ " in text:
            text = text.replace("+ ", "+")
        while "- " in text:
            text = text.replace("- ", "-")

        values: list[float] = []
        for part in text.split():
            try:
                values.append(float(part))
            except ValueError:
                continue
        if len(values) != 1:
            logger.warning("解析失败: %s", text)
            return None
        return values[0]

    def stabilize(self, weight: float) -> float | None:
        """稳定则返回稳定重量，否则 None。"""
        return self._stabilizer.stabilize(weight)

    def reset(self) -> None:
        """重置稳重器窗口与锁定状态。"""
        self._stabilizer.reset()

    def apply_start_params(self) -> None:
        """点 Start 时把共享 Params 的稳定阈值拷进稳重器（中途改了要再 Start）。"""
        self._stabilizer.apply_start_params(self._params)

    @property
    def stability_threshold(self) -> float:
        """当前生效的稳定阈值（Start 快照）。"""
        return self._stabilizer.stability_threshold

