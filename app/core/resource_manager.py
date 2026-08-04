# app/core/resource_manager.py
import sys
from pathlib import Path


class ResourceManager:
    """开发 / 打包两套根目录，统一用相对路径取文件。

    两类路径（都返回 ``Path``）：

    - ``get_resource(...)``：只读静态资源（图标、音效等）
      - 开发：项目根（含 ``pyproject.toml`` + ``app/``）
      - 打包：PyInstaller ``_MEIPASS``
    - ``get_external(...)``：可读写外部文件（``config.toml``、日志等）
      - 开发：同上项目根
      - 打包：EXE 所在目录

    用法::

        ResourceManager.get_resource("app/resources/icons/app.ico")
        ResourceManager.get_external("config.toml")
        ResourceManager.get_external("log")  # 日志目录

    需要 ``str`` 时再 ``str(...)``（如 ``QIcon``、``winsound``）。
    一般直接用上面两个方法，不必自己拼 ``get_*_root() / ...``。
    """

    _resource_root_cache: Path | None = None
    _external_root_cache: Path | None = None

    @classmethod
    def _is_frozen(cls) -> bool:
        return getattr(sys, "frozen", False)

    @classmethod
    def get_resource_root(cls) -> Path:
        """
        静态资源根目录：
        - 打包：_MEIPASS
        - 开发：含 pyproject.toml 与 app/ 的项目根
        """
        if cls._resource_root_cache is not None:
            return cls._resource_root_cache

        if cls._is_frozen():
            meipass = getattr(sys, "_MEIPASS", None)
            if not meipass:
                raise RuntimeError("打包运行缺少 sys._MEIPASS")
            cls._resource_root_cache = Path(meipass)
            return cls._resource_root_cache

        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "pyproject.toml").is_file() and (parent / "app").is_dir():
                cls._resource_root_cache = parent
                return parent

        raise RuntimeError(f"找不到项目根目录（从 {current} 向上查找）")

    @classmethod
    def get_external_root(cls) -> Path:
        """
        外部文件根目录：
        - 打包：EXE 所在目录
        - 开发：项目根目录
        """
        if cls._external_root_cache is not None:
            return cls._external_root_cache

        if cls._is_frozen():
            cls._external_root_cache = Path(sys.executable).resolve().parent
        else:
            cls._external_root_cache = cls.get_resource_root()
        return cls._external_root_cache

    @classmethod
    def get_resource(cls, rel_path: str | Path) -> Path:
        """静态资源绝对路径（图标 / qss / 音效）。"""
        clean = str(rel_path).lstrip("\\/")
        return cls.get_resource_root() / clean

    @classmethod
    def get_external(cls, rel_path: str | Path) -> Path:
        """外部读写文件绝对路径（config.toml / 日志等）。"""
        clean = str(rel_path).lstrip("\\/")
        return cls.get_external_root() / clean
