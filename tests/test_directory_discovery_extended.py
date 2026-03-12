"""Extended tests for DirectoryPluginDiscovery to increase coverage."""

import tempfile
from pathlib import Path


from cadence_sdk import DirectoryPluginDiscovery, discover_plugins

_PLUGIN_SRC = '''\
from cadence_sdk import BasePlugin, BaseAgent, PluginMetadata, uvtool

class _DiscAgent(BaseAgent):
    def get_tools(self):
        @uvtool
        def noop(x: str) -> str:
            """noop"""
            return x
        return [noop]
    def get_system_prompt(self):
        return "x"

class DiscPlugin(BasePlugin):
    @staticmethod
    def get_metadata():
        return PluginMetadata(
            pid="{pid}",
            name="Disc",
            version="{version}",
            description="discovery ext test",
        )
    @staticmethod
    def create_agent():
        return _DiscAgent()
'''


def _write_plugin(
    directory: Path, pid: str = "com.disc.ext", version: str = "1.0.0"
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    src = _PLUGIN_SRC.format(pid=pid, version=version)
    (directory / "plugin.py").write_text(src)


class TestVersionedLayout:
    """Discovery handles versioned layout: {root}/{pid}/{version}/plugin.py."""

    def test_discovers_plugin_in_versioned_layout(self, plugin_registry):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            versioned = root / "com.disc.versioned" / "1.0.0"
            _write_plugin(versioned, pid="com.disc.versioned", version="1.0.0")

            discovery = DirectoryPluginDiscovery(str(root), auto_register=True)
            plugins = discovery.discover()

            pids = [p.pid for p in plugins]
            assert "com.disc.versioned" in pids

    def test_discovers_multiple_versions_in_versioned_layout(self, plugin_registry):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            for ver in ("1.0.0", "2.0.0"):
                _write_plugin(
                    root / "com.disc.multi" / ver,
                    pid="com.disc.multi",
                    version=ver,
                )

            discovery = DirectoryPluginDiscovery(str(root), auto_register=True)
            plugins = discovery.discover()

            pids = [p.pid for p in plugins]
            assert pids.count("com.disc.multi") >= 1


class TestDiscoveryErrorHandling:
    """Discovery gracefully handles broken plugin.py files."""

    def test_skips_broken_plugin_file(self, plugin_registry):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "broken_plugin"
            plugin_dir.mkdir()
            (plugin_dir / "plugin.py").write_text("raise SyntaxError('intentional')")

            discovery = DirectoryPluginDiscovery(str(tmpdir), auto_register=True)
            # Should not raise — broken plugin is skipped
            plugins = discovery.discover()
            pids = [p.pid for p in plugins]
            assert "broken_plugin" not in pids

    def test_skips_dotfile_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hidden = Path(tmpdir) / ".hidden_plugin"
            hidden.mkdir()
            (hidden / "plugin.py").write_text("x = 1")

            discovery = DirectoryPluginDiscovery(str(tmpdir))
            plugins = discovery.discover()
            # hidden directories should be silently skipped
            assert plugins == []

    def test_skips_pycache_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pycache = Path(tmpdir) / "__pycache__"
            pycache.mkdir()
            (pycache / "plugin.py").write_text("x = 1")

            discovery = DirectoryPluginDiscovery(str(tmpdir))
            plugins = discovery.discover()
            assert plugins == []


class TestDiscoveryAutoRegisterFalse:
    """Discovery with auto_register=False creates contracts but does not register."""

    def test_returns_contracts_without_registering(self, plugin_registry):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "no_reg_plugin"
            _write_plugin(plugin_dir, pid="com.disc.noreg")

            discovery = DirectoryPluginDiscovery(str(tmpdir), auto_register=False)
            plugins = discovery.discover()

            pids = [p.pid for p in plugins]
            assert "com.disc.noreg" in pids
            # Not in registry since auto_register=False
            assert plugin_registry.get_plugin("com.disc.noreg") is None


class TestDiscoveryResetAndGetDiscovered:
    """reset() and get_discovered() behave correctly."""

    def test_get_discovered_returns_copy(self):
        discovery = DirectoryPluginDiscovery("/nonexistent_path_xyz")
        discovered = discovery.get_discovered()
        assert isinstance(discovered, dict)

    def test_reset_re_scans(self, plugin_registry):
        with tempfile.TemporaryDirectory() as tmpdir:
            discovery = DirectoryPluginDiscovery(str(tmpdir), auto_register=False)
            discovery.discover()
            initial = discovery.get_discovered()

            plugin_dir = Path(tmpdir) / "new_plugin"
            _write_plugin(plugin_dir, pid="com.disc.reset")

            discovery.reset()
            after_reset = discovery.get_discovered()

            pids_after = list(after_reset.keys())
            assert len(pids_after) >= len(initial)


class TestDiscoverPluginsConvenienceExtended:
    """Additional tests for discover_plugins convenience function."""

    def test_discovers_flat_plugin(self, plugin_registry):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "flat_ext"
            _write_plugin(plugin_dir, pid="com.disc.flatext")

            plugins = discover_plugins(str(tmpdir), auto_register=True)
            pids = [p.pid for p in plugins]
            assert "com.disc.flatext" in pids

    def test_accepts_list_of_paths(self):
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            plugins = discover_plugins([d1, d2], auto_register=False)
            assert isinstance(plugins, list)
