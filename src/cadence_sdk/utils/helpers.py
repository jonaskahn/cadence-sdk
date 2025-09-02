"""Helper utilities for Cadence plugins."""

import re
from typing import Any, Dict


def get_sdk_version() -> str:
    """Get the current SDK version."""
    return "1.0.5"


def check_compatibility(plugin_sdk_version: str, current_sdk_version: str = None) -> bool:
    """Check if a plugin's SDK version requirement is compatible with current SDK."""
    if current_sdk_version is None:
        current_sdk_version = get_sdk_version()

    try:
        return _check_version_constraint(plugin_sdk_version, current_sdk_version)
    except Exception:
        return False


def _check_version_constraint(constraint: str, version: str) -> bool:
    """Check if a version satisfies a constraint."""
    constraint = constraint.strip()

    if constraint == version:
        return True

    if constraint.startswith(">="):
        required_version = constraint[2:].strip()
        return _compare_versions(version, required_version) >= 0

    if constraint.startswith(">"):
        required_version = constraint[1:].strip()
        return _compare_versions(version, required_version) > 0

    if constraint.startswith("<="):
        required_version = constraint[2:].strip()
        return _compare_versions(version, required_version) <= 0

    if constraint.startswith("<"):
        required_version = constraint[1:].strip()
        return _compare_versions(version, required_version) < 0

    if constraint.startswith("~"):
        required_version = constraint[1:].strip()
        return _is_compatible_release(version, required_version)

    return constraint == version


def _compare_versions(version1: str, version2: str) -> int:
    """Compare two version strings."""

    def normalize_version(version_string):
        """Convert version string to comparable tuple."""
        parts = re.split(r"[-.]", version_string)
        normalized = []
        for part in parts:
            if part.isdigit():
                normalized.append(int(part))
            else:
                normalized.append(part)
        return normalized

    version1_parts = normalize_version(version1)
    version2_parts = normalize_version(version2)

    max_length = max(len(version1_parts), len(version2_parts))
    version1_parts += [0] * (max_length - len(version1_parts))
    version2_parts += [0] * (max_length - len(version2_parts))

    for part1, part2 in zip(version1_parts, version2_parts):
        if isinstance(part1, int) and isinstance(part2, int):
            if part1 < part2:
                return -1
            elif part1 > part2:
                return 1
        else:
            str1, str2 = str(part1), str(part2)
            if str1 < str2:
                return -1
            elif str1 > str2:
                return 1

    return 0


def _is_compatible_release(version: str, base_version: str) -> bool:
    """Check if version is a compatible release with base_version."""
    try:
        version_parts = [int(x) for x in version.split(".")]
        base_parts = [int(x) for x in base_version.split(".")]

        if len(version_parts) < 2 or len(base_parts) < 2:
            return False

        if version_parts[0] != base_parts[0] or version_parts[1] != base_parts[1]:
            return False

        if len(version_parts) >= 3 and len(base_parts) >= 3:
            return version_parts[2] >= base_parts[2]

        return True
    except (ValueError, IndexError):
        return False


def format_plugin_info(metadata: Dict[str, Any]) -> str:
    """Format plugin metadata for display."""
    name = metadata.get("name", "Unknown")
    version = metadata.get("version", "Unknown")
    description = metadata.get("description", "No description")
    capabilities = metadata.get("capabilities", [])

    info_lines = [
        f"Plugin: {name} v{version}",
        f"Description: {description}",
    ]

    if capabilities:
        info_lines.append(f"Capabilities: {', '.join(capabilities)}")

    return "\n".join(info_lines)
