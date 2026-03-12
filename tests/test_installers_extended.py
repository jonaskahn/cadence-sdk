"""Extended tests for installer utilities to increase coverage."""

from unittest.mock import MagicMock, patch


from cadence_sdk.utils.installers import (
    install_dependencies,
    install_plugin_dependencies,
)


class TestInstallDependenciesExtended:
    """Tests for install_dependencies with subprocess interaction."""

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
        # stderr is empty so falls back to "Installation failed"
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


class TestInstallPluginDependenciesExtended:
    """Tests for install_plugin_dependencies with auto_install=True."""

    def test_satisfied_deps_return_true_without_installing(self):
        # json is always available
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
                side_effect=[False, True],  # missing before install, present after
            ):
                satisfied, missing = install_plugin_dependencies(
                    ["_fake_pkg==1.0"], "test_plugin", auto_install=True
                )
        assert satisfied is True
        assert missing == []

    def test_auto_install_still_missing_after_install(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        with patch(
            "cadence_sdk.utils.installers.subprocess.run", return_value=mock_result
        ):
            with patch(
                "cadence_sdk.utils.installers.check_dependency_installed",
                return_value=False,  # still missing after install
            ):
                satisfied, missing = install_plugin_dependencies(
                    ["_fake_pkg==1.0"], "test_plugin", auto_install=True
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
                    ["_fake_pkg==1.0"], "test_plugin", auto_install=True
                )
        assert satisfied is False
        assert len(missing) > 0
