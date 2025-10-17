"""Helper utilities for Cadence plugins."""

import re
from typing import Any, Dict


def get_sdk_version() -> str:
    """Get the current SDK version."""
    return "1.3.3"


def _compare_versions(version1: str, version2: str) -> int:
    """Compare two version strings."""
    normalized_version1 = _normalize_version_string(version1)
    normalized_version2 = _normalize_version_string(version2)

    return _compare_normalized_versions(normalized_version1, normalized_version2)


def _normalize_version_string(version_string: str) -> list:
    """Convert version string to comparable list of mixed types."""
    parts = re.split(r"[-.]", version_string)
    normalized_parts = []
    for part in parts:
        if part.isdigit():
            normalized_parts.append(int(part))
        else:
            normalized_parts.append(part)
    return normalized_parts


def _compare_normalized_versions(version1_parts: list, version2_parts: list) -> int:
    """Compare two normalized version lists."""
    max_length = max(len(version1_parts), len(version2_parts))
    padded_version1 = _pad_version_parts(version1_parts, max_length)
    padded_version2 = _pad_version_parts(version2_parts, max_length)

    for part1, part2 in zip(padded_version1, padded_version2):
        if isinstance(part1, int) and isinstance(part2, int):
            if part1 < part2:
                return -1
            elif part1 > part2:
                return 1
        else:
            comparison_result = _compare_string_parts(str(part1), str(part2))
            if comparison_result != 0:
                return comparison_result

    return 0


def _pad_version_parts(version_parts: list, target_length: int) -> list:
    """Pad version parts with zeros to reach target length."""
    return version_parts + [0] * (target_length - len(version_parts))


def _compare_string_parts(part1: str, part2: str) -> int:
    """Compare two string parts lexicographically."""
    if part1 < part2:
        return -1
    elif part1 > part2:
        return 1
    return 0


def _is_compatible_release(version: str, base_version: str) -> bool:
    """Check if version is a compatible release with base_version."""
    try:
        version_components = _parse_version_components(version)
        base_components = _parse_version_components(base_version)

        if not _versions_have_minimum_components(version_components, base_components):
            return False

        return _versions_are_compatible(version_components, base_components)
    except (ValueError, IndexError):
        return False


def _parse_version_components(version: str) -> list:
    """Parse version string into integer components."""
    return [int(component) for component in version.split(".")]


def _versions_have_minimum_components(version_parts: list, base_parts: list) -> bool:
    """Check if both versions have at least 2 components."""
    return len(version_parts) >= 2 and len(base_parts) >= 2


def _versions_are_compatible(version_parts: list, base_parts: list) -> bool:
    """Check if version is compatible with base version."""
    if version_parts[0] != base_parts[0] or version_parts[1] != base_parts[1]:
        return False

    if len(version_parts) >= 3 and len(base_parts) >= 3:
        return version_parts[2] >= base_parts[2]

    return True


def _check_version_constraint(constraint: str, version: str) -> bool:
    """Check if a version satisfies a constraint."""
    constraint = constraint.strip()

    if constraint == version:
        return True

    constraint_type = _get_constraint_type(constraint)
    required_version = _extract_version_from_constraint(constraint)

    return _evaluate_version_constraint(constraint_type, version, required_version)


def _get_constraint_type(constraint: str) -> str:
    """Determine the type of version constraint."""
    if constraint.startswith(">="):
        return ">="
    elif constraint.startswith(">"):
        return ">"
    elif constraint.startswith("<="):
        return "<="
    elif constraint.startswith("<"):
        return "<"
    elif constraint.startswith("~"):
        return "~"
    else:
        return "="


def _extract_version_from_constraint(constraint: str) -> str:
    """Extract the version part from a constraint string."""
    constraint_type = _get_constraint_type(constraint)
    if constraint_type == "=":
        return constraint
    elif constraint_type == "~":
        return constraint[1:].strip()
    else:
        return constraint[len(constraint_type) :].strip()


def _evaluate_version_constraint(constraint_type: str, version: str, required_version: str) -> bool:
    """Evaluate a version constraint against a version."""
    if constraint_type == ">=":
        return _compare_versions(version, required_version) >= 0
    elif constraint_type == ">":
        return _compare_versions(version, required_version) > 0
    elif constraint_type == "<=":
        return _compare_versions(version, required_version) <= 0
    elif constraint_type == "<":
        return _compare_versions(version, required_version) < 0
    elif constraint_type == "~":
        return _is_compatible_release(version, required_version)
    else:
        return version == required_version


def check_compatibility(plugin_sdk_version: str, current_sdk_version: str = None) -> bool:
    """Check if a plugin's SDK version requirement is compatible with current SDK."""
    if current_sdk_version is None:
        current_sdk_version = get_sdk_version()

    try:
        return _check_version_constraint(plugin_sdk_version, current_sdk_version)
    except Exception:
        return False


def format_plugin_info(metadata: Dict[str, Any]) -> str:
    """Format plugin metadata for display."""
    plugin_name = metadata.get("name", "Unknown")
    plugin_version = metadata.get("version", "Unknown")
    plugin_description = metadata.get("description", "No description")
    plugin_capabilities = metadata.get("capabilities", [])

    formatted_lines = [
        f"Plugin: {plugin_name} v{plugin_version}",
        f"Description: {plugin_description}",
    ]

    if plugin_capabilities:
        formatted_lines.append(f"Capabilities: {', '.join(plugin_capabilities)}")

    return "\n".join(formatted_lines)
