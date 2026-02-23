"""Dependency installation utilities.

This module provides utilities for installing plugin dependencies
using pip.
"""

import logging
import re
import subprocess
import sys
from typing import List, Tuple

logger = logging.getLogger(__name__)

DEFAULT_INSTALL_TIMEOUT_SECONDS = 300
_PACKAGE_SPEC_SEPARATORS = re.compile(r"[><=!~\s\[;]")


def install_dependencies(
    packages: List[str], upgrade: bool = False, quiet: bool = True
) -> Tuple[bool, str]:
    """Install Python packages using pip.

    Args:
        packages: List of package specifications (e.g., ["requests>=2.28", "numpy"])
        upgrade: If True, upgrade packages if already installed
        quiet: If True, suppress pip output

    Returns:
        Tuple of (success, output/error_message)

    Example:
        success, msg = install_dependencies(["requests>=2.28", "numpy"])
        if not success:
            print(f"Installation failed: {msg}")
    """
    if not packages:
        return True, "No packages to install"

    cmd = [sys.executable, "-m", "pip", "install"]

    if upgrade:
        cmd.append("--upgrade")

    if quiet:
        cmd.append("--quiet")

    cmd.extend(packages)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=DEFAULT_INSTALL_TIMEOUT_SECONDS,
        )

        if result.returncode == 0:
            return True, result.stdout or "Installation successful"
        else:
            return False, result.stderr or "Installation failed"

    except subprocess.TimeoutExpired:
        return False, (
            f"Installation timed out after "
            f"{DEFAULT_INSTALL_TIMEOUT_SECONDS} seconds"
        )
    except Exception as e:
        return False, f"Installation error: {str(e)}"


def check_dependency_installed(package_name: str) -> bool:
    """Check if a package is installed.

    Args:
        package_name: Name of the package to check

    Returns:
        True if package is installed and importable

    Example:
        if check_dependency_installed("requests"):
            import requests
            # use requests
        else:
            print("Please install requests")
    """
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


def get_installed_version(package_name: str) -> str:
    """Get installed version of a package.

    Args:
        package_name: Package name

    Returns:
        Version string, or empty string if not installed

    Example:
        version = get_installed_version("requests")
        print(f"requests version: {version}")
    """
    try:
        import importlib.metadata

        return importlib.metadata.version(package_name)
    except Exception:
        return ""


def extract_package_name(dependency_spec: str) -> str:
    """Extract package name from dependency specification.

    Args:
        dependency_spec: Dependency string (e.g., "requests>=2.28")

    Returns:
        Package name without version specifiers
    """
    return _PACKAGE_SPEC_SEPARATORS.split(dependency_spec, maxsplit=1)[0].strip()


def install_plugin_dependencies(
    dependencies: List[str], plugin_name: str, auto_install: bool = True
) -> Tuple[bool, List[str]]:
    """Install dependencies for a plugin.

    Args:
        dependencies: List of package requirements
        plugin_name: Name of the plugin (for logging)
        auto_install: If True, automatically install; if False, just check

    Returns:
        Tuple of (all_satisfied, missing_packages)

    Example:
        satisfied, missing = install_plugin_dependencies(
            ["requests>=2.28", "numpy"],
            "my_plugin",
            auto_install=True
        )

        if not satisfied:
            print(f"Missing dependencies: {missing}")
    """
    if not dependencies:
        return True, []

    missing = []

    for dep in dependencies:
        pkg_name = extract_package_name(dep)
        if not check_dependency_installed(pkg_name):
            missing.append(dep)

    if not missing:
        return True, []

    if not auto_install:
        return False, missing

    logger.info(f"Installing dependencies for {plugin_name}: {missing}")
    success, msg = install_dependencies(missing)

    if success:
        still_missing = []
        for dep in missing:
            pkg_name = extract_package_name(dep)
            if not check_dependency_installed(pkg_name):
                still_missing.append(dep)

        return (True, []) if not still_missing else (False, still_missing)
    else:
        return False, missing
