# app/models/formatting.py
"""数值的统一格式化（纯函数、无 Qt）。界面和日志共用，免得每处各写一遍 f-string。"""


def format_weight(value: float, decimal_places: int) -> str:
    """按指定小数位格式化重量，例如 ``format_weight(10.0, 2)`` → ``"10.00"``。"""
    return f"{value:.{decimal_places}f}"
