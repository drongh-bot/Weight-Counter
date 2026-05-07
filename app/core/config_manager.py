# app/core/config_manager.py
from __future__ import annotations

import threading
from typing import Any

import toml

from app.core.resource_manager import ResourceManager


class ConfigManager:
    """
    Generic TOML config manager
    - Singleton
    - Initialization guard
    - Strong typing
    - Thread-safe writes
    - Auto-create sections
    """

    _instance: ConfigManager | None = None
    _lock = threading.Lock()

    def __new__(cls) -> "ConfigManager":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialization guard to prevent re-initialization."""
        if getattr(self, "_initialized", False):
            return

        self.path = ResourceManager.get_external_root() / "config.toml"
        self.data: dict[str, dict[str, Any]] = {}
        self._initialized = True

    # ------------------------------------------------------------
    # Load config
    # ------------------------------------------------------------
    def load(self) -> None:
        try:
            if self.path.exists():
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = toml.load(f)
            else:
                self.data = {}
        except Exception as e:
            raise RuntimeError(f"加载 TOML 配置失败: {e}") from e

    # ------------------------------------------------------------
    # Save config (thread-safe)
    # ------------------------------------------------------------
    def save(self) -> None:
        with self._lock:
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    toml.dump(self.data, f)
            except Exception as e:
                raise RuntimeError(f"保存 TOML 配置失败: {e}") from e

    # ------------------------------------------------------------
    # Get value (with default)
    # ------------------------------------------------------------
    def get_value(self, section: str, key: str, default=None) -> Any:
        return self.data.get(section, {}).get(key, default)

    # ------------------------------------------------------------
    # Set value (auto-create section)
    # ------------------------------------------------------------
    def set_value(self, section: str, key: str, value: Any) -> None:
        with self._lock:
            if section not in self.data:
                self.data[section] = {}
            self.data[section][key] = value
