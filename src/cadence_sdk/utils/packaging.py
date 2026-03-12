"""Plugin packaging utilities.

This module provides utilities for packaging plugins into zip archives
suitable for upload to the Cadence platform.
"""

import io
import json
import zipfile
from pathlib import Path
from typing import List, Optional, Union


def build_plugin_zip(
    plugin_dir: Union[str, Path],
    exclude_patterns: Optional[List[str]] = None,
) -> bytes:
    """Package a plugin directory into a zip archive with plugin_manifest.json.

    The zip archive will contain:
    - All files from the plugin directory (excluding __pycache__ and .pyc files)
    - A root-level plugin_manifest.json with pid and version from plugin metadata

    The plugin directory must contain a plugin.py file with a BasePlugin subclass
    that has a get_metadata() method returning pid and version.

    Args:
        plugin_dir: Path to the plugin directory containing plugin.py
        exclude_patterns: Additional glob patterns to exclude (e.g. ["*.log"])

    Returns:
        Raw zip archive bytes ready for upload

    Raises:
        FileNotFoundError: If plugin_dir does not exist
        ValueError: If plugin.py is not found or metadata cannot be read

    Example:
        zip_bytes = build_plugin_zip("/path/to/my_plugin")
        with open("my_plugin.zip", "wb") as f:
            f.write(zip_bytes)
    """
    plugin_dir = Path(plugin_dir)
    if not plugin_dir.exists():
        raise FileNotFoundError(f"Plugin directory not found: {plugin_dir}")

    plugin_file = plugin_dir / "plugin.py"
    if not plugin_file.exists():
        raise ValueError(f"plugin.py not found in {plugin_dir}")

    pid, version = _extract_metadata_from_plugin(plugin_dir, plugin_file)

    exclude_patterns = list(exclude_patterns or [])

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        manifest = {"pid": pid, "version": version}
        zf.writestr("plugin_manifest.json", json.dumps(manifest))

        for file_path in sorted(plugin_dir.rglob("*")):
            if not file_path.is_file():
                continue
            if _should_exclude(file_path, plugin_dir, exclude_patterns):
                continue
            arcname = file_path.relative_to(plugin_dir)
            zf.write(file_path, arcname)

    return buffer.getvalue()


def _should_exclude(file_path: Path, base_dir: Path, extra_patterns: List[str]) -> bool:
    """Return True if file_path should be excluded from the zip.

    Args:
        file_path: Absolute path to the file
        base_dir: Plugin base directory
        extra_patterns: Additional glob patterns to exclude

    Returns:
        True if the file should be excluded
    """
    rel = file_path.relative_to(base_dir)
    parts = rel.parts

    if any(part == "__pycache__" for part in parts):
        return True
    if file_path.suffix == ".pyc":
        return True

    for pattern in extra_patterns:
        if file_path.match(pattern):
            return True

    return False


def _extract_metadata_from_plugin(
    plugin_dir: Path, plugin_file: Path
) -> tuple[str, str]:
    """Import plugin.py and extract pid and version from metadata.

    Args:
        plugin_dir: Plugin package directory (added to sys.path)
        plugin_file: Path to plugin.py

    Returns:
        (pid, version) tuple

    Raises:
        ValueError: If the plugin class cannot be found or metadata is invalid
    """
    import importlib.util
    import sys

    module_name = f"_cadence_pkg_{plugin_dir.name.replace('.', '_').replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, plugin_file)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load plugin module from {plugin_file}")

    plugin_dir_str = str(plugin_dir)
    sys.path.insert(0, plugin_dir_str)
    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        plugin_class = _find_plugin_class(module)
        if plugin_class is None:
            raise ValueError(f"No BasePlugin subclass found in {plugin_file}")
        metadata = plugin_class.get_metadata()
        return metadata.pid, metadata.version
    finally:
        if plugin_dir_str in sys.path:
            sys.path.remove(plugin_dir_str)


def _find_plugin_class(module):
    from ._plugin_loader import find_plugin_class

    return find_plugin_class(module)
