"""Tests for dependency installation utilities."""

from cadence_sdk.utils.installers import (
    DEFAULT_INSTALL_TIMEOUT_SECONDS,
    check_dependency_installed,
    extract_package_name,
    get_installed_version,
    install_dependencies,
    install_plugin_dependencies,
)


class TestExtractPackageName:
    """Tests for extract_package_name."""

    def test_extracts_name_from_simple_spec(self):
        """extract_package_name extracts name from requests>=2.28."""
        assert extract_package_name("requests>=2.28") == "requests"

    def test_extracts_name_from_equals_spec(self):
        """extract_package_name extracts name from package==1.0."""
        assert extract_package_name("package==1.0") == "package"

    def test_extracts_name_from_less_than_spec(self):
        """extract_package_name extracts name from package<2.0."""
        assert extract_package_name("package<2.0") == "package"

    def test_extracts_name_from_no_version(self):
        """extract_package_name returns name when no version specifier."""
        assert extract_package_name("numpy") == "numpy"

    def test_strips_whitespace(self):
        """extract_package_name strips leading/trailing whitespace."""
        assert extract_package_name("  pkg  ") == "pkg"


class TestCheckDependencyInstalled:
    """Tests for check_dependency_installed."""

    def test_returns_true_for_installed_package(self):
        """check_dependency_installed returns True for stdlib."""
        assert check_dependency_installed("json") is True

    def test_returns_false_for_nonexistent_package(self):
        """check_dependency_installed returns False for nonexistent package."""
        assert check_dependency_installed("_nonexistent_package_xyz_123") is False


class TestGetInstalledVersion:
    """Tests for get_installed_version."""

    def test_returns_version_for_installed_package(self):
        """get_installed_version returns version string for installed package."""
        version = get_installed_version("pydantic")
        assert isinstance(version, str)
        assert len(version) > 0

    def test_returns_empty_for_nonexistent_package(self):
        """get_installed_version returns empty string for nonexistent package."""
        version = get_installed_version("_nonexistent_package_xyz_456")
        assert version == ""


class TestInstallDependencies:
    """Tests for install_dependencies."""

    def test_empty_packages_returns_success(self):
        """install_dependencies returns success for empty list."""
        success, msg = install_dependencies([])
        assert success is True
        assert "No packages" in msg

    def test_install_dependencies_timeout_constant_defined(self):
        """DEFAULT_INSTALL_TIMEOUT_SECONDS is defined."""
        assert DEFAULT_INSTALL_TIMEOUT_SECONDS == 300


class TestInstallPluginDependencies:
    """Tests for install_plugin_dependencies."""

    def test_empty_dependencies_returns_success(self):
        """install_plugin_dependencies returns success for empty deps."""
        satisfied, missing = install_plugin_dependencies([], "test_plugin")
        assert satisfied is True
        assert missing == []

    def test_returns_missing_when_auto_install_false(self):
        """install_plugin_dependencies returns missing when auto_install=False."""
        satisfied, missing = install_plugin_dependencies(
            ["_nonexistent_xyz_789"],
            "test_plugin",
            auto_install=False,
        )
        assert satisfied is False
        assert len(missing) == 1
