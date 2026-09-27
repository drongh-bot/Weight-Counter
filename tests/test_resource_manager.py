# tests/test_resource_manager.py
"""ResourceManager：开发 / 打包两套根目录。

打包分支（`sys.frozen` + `_MEIPASS`）平时永远走不到，只有打出 exe 才会执行 ——
所以这里用 monkeypatch 伪造环境，把它提前测掉。
"""

import sys

import pytest

from app.core.resource_manager import ResourceManager


@pytest.fixture(autouse=True)
def _clear_root_cache():
    """根目录是**类级缓存**，一个测试设了会串到下一个，前后都清掉。"""
    ResourceManager._resource_root_cache = None
    ResourceManager._external_root_cache = None
    yield
    ResourceManager._resource_root_cache = None
    ResourceManager._external_root_cache = None


def _fake_frozen(monkeypatch, *, meipass: str | None, executable: str) -> None:
    """伪造 PyInstaller 的运行环境：有/无 _MEIPASS 都能测。"""
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", executable, raising=False)
    if meipass is None:
        monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    else:
        monkeypatch.setattr(sys, "_MEIPASS", meipass, raising=False)


class TestDevelopmentMode:
    """开发模式：根目录 = 含 pyproject.toml + app/ 的项目根。"""

    def test_resource_root_is_project_root(self):
        root = ResourceManager.get_resource_root()
        assert (root / "pyproject.toml").is_file()
        assert (root / "app").is_dir()

    def test_external_root_mirrors_resource_root(self):
        assert (
            ResourceManager.get_external_root() == ResourceManager.get_resource_root()
        )

    def test_root_is_cached(self):
        first = ResourceManager.get_resource_root()
        assert first is ResourceManager.get_resource_root()

    def test_not_frozen_by_default(self):
        assert ResourceManager._is_frozen() is False

    def test_resource_path_points_to_existing_icon(self):
        icon = ResourceManager.get_resource("app/resources/icons/app.ico")
        assert icon.is_file()

    def test_external_path_lives_under_external_root(self):
        cfg = ResourceManager.get_external("config.toml")
        assert cfg.name == "config.toml"
        assert cfg.parent == ResourceManager.get_external_root()

    def test_leading_separators_are_stripped(self):
        """`/x` 和 `\\x` 要和 `x` 拼出同一个绝对路径。"""
        expected = ResourceManager.get_resource("app/resources/icons/app.ico")
        assert ResourceManager.get_resource("/app/resources/icons/app.ico") == expected
        assert (
            ResourceManager.get_resource("\\app\\resources\\icons\\app.ico") == expected
        )


class TestFrozenMode:
    """打包模式：静态资源进 _MEIPASS，可写文件放 EXE 旁边。"""

    def test_resource_root_is_meipass(self, monkeypatch, tmp_path):
        _fake_frozen(
            monkeypatch, meipass=str(tmp_path), executable=str(tmp_path / "wc.exe")
        )
        assert ResourceManager.get_resource_root() == tmp_path

    def test_external_root_is_exe_directory(self, monkeypatch, tmp_path):
        exe = tmp_path / "dist" / "wc.exe"
        _fake_frozen(
            monkeypatch,
            meipass=str(tmp_path / "_internal"),
            executable=str(exe),
        )
        assert ResourceManager.get_external_root() == exe.resolve().parent

    def test_resource_and_external_split_apart(self, monkeypatch, tmp_path):
        """打包后两者分家：资源只读进 _MEIPASS，配置/日志写 EXE 旁。"""
        meipass = tmp_path / "_internal"
        exe = tmp_path / "dist" / "wc.exe"
        _fake_frozen(monkeypatch, meipass=str(meipass), executable=str(exe))

        assert ResourceManager.get_resource("x.ico").parent == meipass
        assert (
            ResourceManager.get_external("config.toml").parent == exe.resolve().parent
        )

    def test_missing_meipass_raises(self, monkeypatch, tmp_path):
        """PyInstaller 漏配 _MEIPASS 时要给出明确错误，而不是静默用错根。"""
        _fake_frozen(monkeypatch, meipass=None, executable=str(tmp_path / "wc.exe"))
        with pytest.raises(RuntimeError, match="_MEIPASS"):
            ResourceManager.get_resource_root()
