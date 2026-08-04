# app/core/resource_manager.py
import sys
from pathlib import Path


class ResourceManager:
    """
    管理两类路径：
    1. 静态资源（只读）：图标 / qss / 音效 / 图片
       - 开发模式：项目根目录
       - 打包模式：PyInstaller 的 _MEIPASS 目录

    2. 外部文件（读写）：config.toml / 日志 / 导出文件
       - 开发模式：项目根目录
       - 打包模式：EXE 所在目录
    """

    # 缓存路径，避免重复计算
    _resource_root_cache: Path | None = None
    _external_root_cache: Path | None = None

    @staticmethod
    def is_frozen() -> bool:
        """是否以 PyInstaller 打包后的可执行文件运行。"""
        return getattr(sys, "frozen", False)

    @staticmethod
    def get_resource_root() -> Path:
        """
        静态资源根目录：
        - 打包：_MEIPASS
        - 开发：向上查找含 app/ 的项目根
        """
        if ResourceManager._resource_root_cache is not None:
            return ResourceManager._resource_root_cache

        if ResourceManager.is_frozen():
            root = Path(getattr(sys, "_MEIPASS", ""))
            ResourceManager._resource_root_cache = root
            return root

        # 开发模式：向上查找项目根
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "app").exists():
                ResourceManager._resource_root_cache = parent
                return parent

        # 兜底（正常不应走到）
        fallback = Path.cwd()
        ResourceManager._resource_root_cache = fallback
        return fallback

    @staticmethod
    def get_external_root() -> Path:
        """
        外部文件根目录：
        - 打包：EXE 所在目录
        - 开发：项目根目录
        """
        if ResourceManager._external_root_cache is not None:
            return ResourceManager._external_root_cache

        if ResourceManager.is_frozen():
            root = Path(sys.executable).resolve().parent
            ResourceManager._external_root_cache = root
            return root

        # 开发模式：与静态资源共用根目录
        root = ResourceManager.get_resource_root()
        ResourceManager._external_root_cache = root
        return root

    @staticmethod
    def get_resource(rel_path: str | Path) -> str:
        """
        获取静态资源绝对路径（图标 / qss / 音效）。
        自动去掉前导斜杠，避免 Path 覆盖根目录。
        """
        clean = str(rel_path).lstrip("\\/")
        return str(ResourceManager.get_resource_root() / clean)

    @staticmethod
    def get_external(rel_path: str | Path) -> Path:
        """获取外部读写文件路径（config.toml / 日志等）。"""
        clean = str(rel_path).lstrip("\\/")
        return ResourceManager.get_external_root() / clean
