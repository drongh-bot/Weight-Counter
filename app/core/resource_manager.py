# app/core/resource_manager.py
import sys
from pathlib import Path


class ResourceManager:
    """
    ResourceManager handles two types of paths:
    1. Static resources (read-only): icons / qss / sounds / images
       - Dev mode: project root directory
       - Frozen mode: PyInstaller's _MEIPASS directory

    2. External files (read-write): config.toml / logs / exported files
       - Dev mode: project root directory
       - Frozen mode: directory alongside the EXE
    """

    # Cached paths to avoid redundant computation
    _resource_root_cache: Path | None = None
    _external_root_cache: Path | None = None

    # ---------------------------------------------------------
    # Basic checks
    # ---------------------------------------------------------
    @staticmethod
    def is_frozen() -> bool:
        """Check if running as a PyInstaller-frozen executable."""
        return getattr(sys, "frozen", False)

    # ---------------------------------------------------------
    # Static resource root directory (read-only)
    # ---------------------------------------------------------
    @staticmethod
    def get_resource_root() -> Path:
        """
        Static resource root directory:
        - Frozen: _MEIPASS
        - Dev: auto-detect by walking up to the directory containing app/
        """
        if ResourceManager._resource_root_cache is not None:
            return ResourceManager._resource_root_cache

        if ResourceManager.is_frozen():
            root = Path(getattr(sys, "_MEIPASS", ""))
            ResourceManager._resource_root_cache = root
            return root

        # Dev mode: walk up to find the project root directory
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "app").exists():
                ResourceManager._resource_root_cache = parent
                return parent

        # Fallback (should never be reached in practice)
        fallback = Path.cwd()
        ResourceManager._resource_root_cache = fallback
        return fallback

    # ---------------------------------------------------------
    # External file root directory (read-write)
    # ---------------------------------------------------------
    @staticmethod
    def get_external_root() -> Path:
        """
        External file root directory:
        - Frozen: directory alongside the EXE
        - Dev: project root directory
        """
        if ResourceManager._external_root_cache is not None:
            return ResourceManager._external_root_cache

        if ResourceManager.is_frozen():
            root = Path(sys.executable).resolve().parent
            ResourceManager._external_root_cache = root
            return root

        # Dev mode: external files share the same root as resource files
        root = ResourceManager.get_resource_root()
        ResourceManager._external_root_cache = root
        return root

    # ---------------------------------------------------------
    # Get static resource path
    # ---------------------------------------------------------
    @staticmethod
    def get_resource(rel_path: str | Path) -> str:
        """
        Get static resource path (icons / qss / sounds).
        Automatically strips leading slashes to avoid Path overriding the root.
        """
        clean = str(rel_path).lstrip("\\/")
        return str(ResourceManager.get_resource_root() / clean)

    # ---------------------------------------------------------
    # Get external file path (config / logs)
    # ---------------------------------------------------------
    @staticmethod
    def get_external(rel_path: str | Path) -> Path:
        """
        Get external read-write file path (config.toml / logs).
        """
        clean = str(rel_path).lstrip("\\/")
        return ResourceManager.get_external_root() / clean
