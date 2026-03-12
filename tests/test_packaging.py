"""Tests for build_plugin_zip packaging utility."""

import io
import json
import zipfile
from pathlib import Path

import pytest

from cadence_sdk import build_plugin_zip
from cadence_sdk.utils.packaging import _should_exclude, _find_plugin_class

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MINIMAL_PLUGIN_SRC = '''\
from cadence_sdk import BasePlugin, BaseAgent, PluginMetadata, uvtool

class _PackTestAgent(BaseAgent):
    def get_tools(self):
        @uvtool
        def noop(x: str) -> str:
            """No-op tool."""
            return x
        return [noop]
    def get_system_prompt(self) -> str:
        return "pack test"

class PackTestPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.pack.test",
            name="Pack Test",
            version="2.3.4",
            description="Packaging test plugin",
        )
    @staticmethod
    def create_agent() -> BaseAgent:
        return _PackTestAgent()
'''


def _make_plugin_dir(tmp_path: Path, src: str = _MINIMAL_PLUGIN_SRC) -> Path:
    """Write a minimal plugin.py into tmp_path and return tmp_path."""
    (tmp_path / "plugin.py").write_text(src)
    return tmp_path


# ---------------------------------------------------------------------------
# build_plugin_zip — happy path
# ---------------------------------------------------------------------------


class TestBuildPluginZipHappyPath:
    """build_plugin_zip produces a valid zip with the correct contents."""

    def test_returns_bytes(self, tmp_path):
        _make_plugin_dir(tmp_path)
        result = build_plugin_zip(tmp_path)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_zip_contains_plugin_py(self, tmp_path):
        _make_plugin_dir(tmp_path)
        result = build_plugin_zip(tmp_path)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            names = zf.namelist()
        assert "plugin.py" in names

    def test_zip_contains_manifest(self, tmp_path):
        _make_plugin_dir(tmp_path)
        result = build_plugin_zip(tmp_path)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            names = zf.namelist()
        assert "plugin_manifest.json" in names

    def test_manifest_has_correct_pid_and_version(self, tmp_path):
        _make_plugin_dir(tmp_path)
        result = build_plugin_zip(tmp_path)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            manifest = json.loads(zf.read("plugin_manifest.json"))
        assert manifest["pid"] == "com.pack.test"
        assert manifest["version"] == "2.3.4"

    def test_accepts_string_path(self, tmp_path):
        _make_plugin_dir(tmp_path)
        result = build_plugin_zip(str(tmp_path))
        assert isinstance(result, bytes)

    def test_excludes_pycache_files(self, tmp_path):
        _make_plugin_dir(tmp_path)
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "plugin.cpython-313.pyc").write_bytes(b"\x00")
        result = build_plugin_zip(tmp_path)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            names = zf.namelist()
        assert not any("__pycache__" in n for n in names)
        assert not any(n.endswith(".pyc") for n in names)

    def test_includes_subdirectory_files(self, tmp_path):
        _make_plugin_dir(tmp_path)
        subdir = tmp_path / "services"
        subdir.mkdir()
        (subdir / "helper.py").write_text("x = 1")
        result = build_plugin_zip(tmp_path)
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            names = zf.namelist()
        assert any("helper.py" in n for n in names)

    def test_extra_exclude_patterns_respected(self, tmp_path):
        _make_plugin_dir(tmp_path)
        (tmp_path / "debug.log").write_text("log")
        result = build_plugin_zip(tmp_path, exclude_patterns=["*.log"])
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            names = zf.namelist()
        assert not any(n.endswith(".log") for n in names)


# ---------------------------------------------------------------------------
# build_plugin_zip — error cases
# ---------------------------------------------------------------------------


class TestBuildPluginZipErrors:
    """build_plugin_zip raises appropriate errors for bad inputs."""

    def test_raises_file_not_found_for_missing_dir(self, tmp_path):
        missing = tmp_path / "does_not_exist"
        with pytest.raises(FileNotFoundError, match="Plugin directory not found"):
            build_plugin_zip(missing)

    def test_raises_value_error_when_no_plugin_py(self, tmp_path):
        # Directory exists but no plugin.py
        with pytest.raises(ValueError, match="plugin.py not found"):
            build_plugin_zip(tmp_path)

    def test_raises_value_error_when_no_baseplugin_subclass(self, tmp_path):
        # plugin.py exists but defines no BasePlugin subclass
        (tmp_path / "plugin.py").write_text("x = 1  # no plugin here\n")
        with pytest.raises(ValueError, match="No BasePlugin subclass found"):
            build_plugin_zip(tmp_path)


# ---------------------------------------------------------------------------
# _should_exclude
# ---------------------------------------------------------------------------


class TestShouldExclude:
    """_should_exclude correctly identifies files to omit from zip."""

    def test_excludes_pycache_subdir(self, tmp_path):
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        f = pycache / "mod.pyc"
        f.write_bytes(b"")
        assert _should_exclude(f, tmp_path, []) is True

    def test_excludes_pyc_files(self, tmp_path):
        f = tmp_path / "mod.cpython-313.pyc"
        f.write_bytes(b"")
        assert _should_exclude(f, tmp_path, []) is True

    def test_includes_regular_py_file(self, tmp_path):
        f = tmp_path / "plugin.py"
        f.write_text("x = 1")
        assert _should_exclude(f, tmp_path, []) is False

    def test_extra_pattern_excludes_file(self, tmp_path):
        f = tmp_path / "debug.log"
        f.write_text("log")
        assert _should_exclude(f, tmp_path, ["*.log"]) is True

    def test_non_matching_pattern_does_not_exclude(self, tmp_path):
        f = tmp_path / "plugin.py"
        f.write_text("x = 1")
        assert _should_exclude(f, tmp_path, ["*.log"]) is False


# ---------------------------------------------------------------------------
# _find_plugin_class
# ---------------------------------------------------------------------------


class TestFindPluginClass:
    """_find_plugin_class returns the correct class from a module."""

    def test_finds_plugin_class(self):
        import types
        from cadence_sdk import BasePlugin, BaseAgent, PluginMetadata

        class _Agent(BaseAgent):
            def get_tools(self):
                return []

            def get_system_prompt(self):
                return "x"

        class _Plugin(BasePlugin):
            @staticmethod
            def get_metadata():
                return PluginMetadata(
                    pid="com.find.test", name="F", version="1.0.0", description="d"
                )

            @staticmethod
            def create_agent():
                return _Agent()

        mod = types.ModuleType("fake_plugin")
        mod.MyPlugin = _Plugin
        result = _find_plugin_class(mod)
        assert result is _Plugin

    def test_returns_none_when_no_plugin(self):
        import types

        mod = types.ModuleType("empty_module")
        mod.x = 42
        result = _find_plugin_class(mod)
        assert result is None
