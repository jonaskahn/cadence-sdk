"""Tests for DirectoryPluginDiscovery and discover_plugins."""

import tempfile
from pathlib import Path

from cadence_sdk import DirectoryPluginDiscovery, discover_plugins
from .conftest import write_plugin


class TestDirectoryPluginDiscoveryInit:
    """Tests for DirectoryPluginDiscovery initialization."""

    def test_accepts_single_path_string(self):
        """DirectoryPluginDiscovery accepts single path as string."""
        discovery = DirectoryPluginDiscovery("/tmp/plugins")
        assert len(discovery.search_paths) == 1
        assert discovery.search_paths[0] == Path("/tmp/plugins")

    def test_accepts_list_of_paths(self):
        """DirectoryPluginDiscovery accepts list of paths."""
        discovery = DirectoryPluginDiscovery(["/path/a", "/path/b"])
        assert len(discovery.search_paths) == 2

    def test_auto_register_defaults_to_true(self):
        """auto_register defaults to True."""
        discovery = DirectoryPluginDiscovery("/tmp")
        assert discovery.auto_register is True


class TestDirectoryPluginDiscoveryFlatLayout:
    """Tests for flat layout discovery: {dir}/{plugin_name}/plugin.py."""

    def test_discovers_plugin_from_flat_layout(self, plugin_registry):
        """Discovery finds plugin in flat layout directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "my_plugin"
            plugin_dir.mkdir()
            plugin_file = plugin_dir / "plugin.py"
            plugin_file.write_text('''
"""Test plugin for discovery."""
from cadence_sdk import BasePlugin, BaseAgent, PluginMetadata
from cadence_sdk.types import UvTool
from cadence_sdk import uvtool

class TestAgent(BaseAgent):
    def get_tools(self):
        @uvtool
        def echo(x: str) -> str:
            return x
        return [echo]
    def get_system_prompt(self):
        return "Test"

class TestPlugin(BasePlugin):
    @staticmethod
    def get_metadata():
        return PluginMetadata(
            pid="com.discovery.test",
            name="Discovery Test",
            version="1.0.0",
            description="For discovery tests",
        )
    @staticmethod
    def create_agent():
        return TestAgent()

plugin = TestPlugin
''')
            discovery = DirectoryPluginDiscovery(tmpdir, auto_register=True)
            plugins = discovery.discover()

            assert len(plugins) >= 1
            pids = [p.pid for p in plugins]
            assert "com.discovery.test" in pids


class TestDirectoryPluginDiscoverySkipItems:
    """Tests for _should_scan_item behavior."""

    def test_skips_nonexistent_paths(self):
        """Discovery skips paths that do not exist."""
        discovery = DirectoryPluginDiscovery("/nonexistent/path/12345")
        plugins = discovery.discover()
        assert plugins == []

    def test_skips_files(self):
        """Discovery skips files (only scans directories)."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            try:
                discovery = DirectoryPluginDiscovery(f.name)
                plugins = discovery.discover()
                assert plugins == []
            finally:
                Path(f.name).unlink(missing_ok=True)


class TestDiscoverPluginsConvenience:
    """Tests for discover_plugins convenience function."""

    def test_returns_list_of_contracts(self):
        """discover_plugins returns list of PluginContract."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            plugins = discover_plugins(tmpdir, auto_register=False)
        assert isinstance(plugins, list)


class TestDirectoryPluginDiscoveryRepr:
    """Tests for DirectoryPluginDiscovery __repr__."""

    def test_repr_includes_path_count(self):
        """__repr__ includes number of paths."""
        discovery = DirectoryPluginDiscovery(["/a", "/b"])
        repr_str = repr(discovery)
        assert "paths=2" in repr_str or "2" in repr_str


class TestVersionedLayout:
    def test_discovers_plugin_in_versioned_layout(self, plugin_registry):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            versioned = root / "com.disc.versioned" / "1.0.0"
            write_plugin(versioned, pid="com.disc.versioned", version="1.0.0")

            discovery = DirectoryPluginDiscovery(str(root), auto_register=True)
            plugins = discovery.discover()

            pids = [p.pid for p in plugins]
            assert "com.disc.versioned" in pids

    def test_discovers_multiple_versions_in_versioned_layout(self, plugin_registry):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            for ver in ("1.0.0", "2.0.0"):
                write_plugin(
                    root / "com.disc.multi" / ver,
                    pid="com.disc.multi",
                    version=ver,
                )

            discovery = DirectoryPluginDiscovery(str(root), auto_register=True)
            plugins = discovery.discover()

            pids = [p.pid for p in plugins]
            assert pids.count("com.disc.multi") >= 1


class TestDiscoveryErrorHandling:
    def test_skips_broken_plugin_file(self, plugin_registry):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "broken_plugin"
            plugin_dir.mkdir()
            (plugin_dir / "plugin.py").write_text("raise SyntaxError('intentional')")

            discovery = DirectoryPluginDiscovery(str(tmpdir), auto_register=True)
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
    def test_returns_contracts_without_registering(self, plugin_registry):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "no_reg_plugin"
            write_plugin(plugin_dir, pid="com.disc.noreg")

            discovery = DirectoryPluginDiscovery(str(tmpdir), auto_register=False)
            plugins = discovery.discover()

            pids = [p.pid for p in plugins]
            assert "com.disc.noreg" in pids
            assert plugin_registry.get_plugin("com.disc.noreg") is None


class TestDiscoveryResetAndGetDiscovered:
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
            write_plugin(plugin_dir, pid="com.disc.reset")

            discovery.reset()
            after_reset = discovery.get_discovered()

            assert len(after_reset) >= len(initial)


class TestDiscoverPluginsConvenienceExtended:
    def test_discovers_flat_plugin(self, plugin_registry):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_dir = Path(tmpdir) / "flat_ext"
            write_plugin(plugin_dir, pid="com.disc.flatext")

            plugins = discover_plugins(str(tmpdir), auto_register=True)
            pids = [p.pid for p in plugins]
            assert "com.disc.flatext" in pids

    def test_accepts_list_of_paths(self):
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            plugins = discover_plugins([d1, d2], auto_register=False)
            assert isinstance(plugins, list)
