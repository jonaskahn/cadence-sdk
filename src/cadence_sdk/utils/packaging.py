"""Plugin packaging utilities.

This module provides utilities for packaging plugins into zip archives
suitable for upload to the Cadence platform.
"""

import io
import zipfile
from pathlib import Path
from typing import List, Optional, Union


def build_plugin_zip(
    plugin_dir: Union[str, Path],
    exclude_patterns: Optional[List[str]] = None,
) -> bytes:
    """Package a plugin directory into a zip archive.

    The zip archive will contain all files from the plugin directory
    (excluding __pycache__ and .pyc files).

    The plugin directory must contain a plugin.py file with a BasePlugin subclass.

    Args:
        plugin_dir: Path to the plugin directory containing plugin.py
        exclude_patterns: Additional glob patterns to exclude (e.g. ["*.log"])

    Returns:
        Raw zip archive bytes ready for upload

    Raises:
        FileNotFoundError: If plugin_dir does not exist
        ValueError: If plugin.py is not found

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

    exclude_patterns = list(exclude_patterns or [])

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
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
