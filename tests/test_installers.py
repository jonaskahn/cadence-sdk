"""Tests for dependency installation utilities."""

from unittest.mock import MagicMock, patch

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

    def test_check_returns_missing_for_nonexistent_package(self):
        """check_plugin_dependencies returns missing for uninstalled package."""
        from cadence_sdk.utils.installers import check_plugin_dependencies

        satisfied, missing = check_plugin_dependencies(
            ["_nonexistent_xyz_789"],
            "test_plugin",
        )
        assert satisfied is False
        assert len(missing) == 1


class TestInstallDependenciesWithMocks:
    def test_success_returns_true(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Successfully installed"
        with patch(
            "cadence_sdk.utils.installers.subprocess.run", return_value=mock_result
        ):
            success, msg = install_dependencies(["some-package==1.0.0"])
        assert success is True

    def test_failure_returns_false_with_stderr(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "ERROR: No matching distribution"
        mock_result.stdout = ""
        with patch(
            "cadence_sdk.utils.installers.subprocess.run", return_value=mock_result
        ):
            success, msg = install_dependencies(["nonexistent-pkg-xyz==99.0"])
        assert success is False
        assert len(msg) > 0

    def test_failure_with_no_stderr_returns_fallback_message(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = ""
        mock_result.stdout = "some stdout info"
        with patch(
            "cadence_sdk.utils.installers.subprocess.run", return_value=mock_result
        ):
            success, msg = install_dependencies(["pkg==1.0"])
        assert success is False
        assert len(msg) > 0

    def test_timeout_returns_false(self):
        import subprocess

        with patch(
            "cadence_sdk.utils.installers.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="pip", timeout=300),
        ):
            success, msg = install_dependencies(["some-pkg"])
        assert success is False
        assert "timed out" in msg.lower() or "timeout" in msg.lower()

    def test_unexpected_exception_returns_false(self):
        with patch(
            "cadence_sdk.utils.installers.subprocess.run",
            side_effect=OSError("pip not found"),
        ):
            success, msg = install_dependencies(["some-pkg"])
        assert success is False
        assert "pip not found" in msg

    def test_upgrade_flag_included_in_command(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        with patch(
            "cadence_sdk.utils.installers.subprocess.run", return_value=mock_result
        ) as mock_run:
            install_dependencies(["pkg==1.0"], upgrade=True)
        args = mock_run.call_args[0][0]
        assert "--upgrade" in args

    def test_quiet_flag_included_by_default(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        with patch(
            "cadence_sdk.utils.installers.subprocess.run", return_value=mock_result
        ) as mock_run:
            install_dependencies(["pkg==1.0"])
        args = mock_run.call_args[0][0]
        assert "--quiet" in args


class TestInstallPluginDependenciesWithMocks:
    def test_satisfied_deps_return_true(self):
        satisfied, missing = install_plugin_dependencies(["json"], "test_plugin")
        assert satisfied is True
        assert missing == []

    def test_auto_install_true_attempts_install_for_missing(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        with patch(
            "cadence_sdk.utils.installers.subprocess.run", return_value=mock_result
        ):
            with patch(
                "cadence_sdk.utils.installers.check_dependency_installed",
                side_effect=[False, True],
            ):
                satisfied, missing = install_plugin_dependencies(
                    ["_fake_pkg==1.0"], "test_plugin"
                )
        assert satisfied is True
        assert missing == []

    def test_still_missing_after_install(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        with patch(
            "cadence_sdk.utils.installers.subprocess.run", return_value=mock_result
        ):
            with patch(
                "cadence_sdk.utils.installers.check_dependency_installed",
                return_value=False,
            ):
                satisfied, missing = install_plugin_dependencies(
                    ["_fake_pkg==1.0"], "test_plugin"
                )
        assert satisfied is False
        assert len(missing) > 0

    def test_install_failure_returns_false(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "install failed"
        mock_result.stdout = ""
        with patch(
            "cadence_sdk.utils.installers.subprocess.run", return_value=mock_result
        ):
            with patch(
                "cadence_sdk.utils.installers.check_dependency_installed",
                return_value=False,
            ):
                satisfied, missing = install_plugin_dependencies(
                    ["_fake_pkg==1.0"], "test_plugin"
                )
        assert satisfied is False
        assert len(missing) > 0


class TestCheckPluginDependencies:
    def test_empty_dependencies_returns_satisfied(self):
        from cadence_sdk.utils.installers import check_plugin_dependencies

        satisfied, missing = check_plugin_dependencies([], "test_plugin")
        assert satisfied is True
        assert missing == []

    def test_returns_missing_for_nonexistent_package(self):
        from cadence_sdk.utils.installers import check_plugin_dependencies

        satisfied, missing = check_plugin_dependencies(
            ["_nonexistent_xyz_789"], "test_plugin"
        )
        assert satisfied is False
        assert len(missing) == 1

    def test_returns_satisfied_when_all_installed(self):
        from cadence_sdk.utils.installers import check_plugin_dependencies

        satisfied, missing = check_plugin_dependencies(["json"], "test_plugin")
        assert satisfied is True
        assert missing == []
