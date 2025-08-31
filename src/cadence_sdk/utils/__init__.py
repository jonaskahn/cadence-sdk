"""Utility functions for Cadence plugins."""


def import_plugins_from_directories(*args, **kwargs):
    from .directory_discovery import import_plugins_from_directories as _f

    return _f(*args, **kwargs)


def reset_directory_discovery(*args, **kwargs):
    from .directory_discovery import reset_directory_discovery as _f

    return _f(*args, **kwargs)


def get_directory_discovery_summary(*args, **kwargs):
    from .directory_discovery import get_directory_discovery_summary as _f

    return _f(*args, **kwargs)


def list_loaded_directories(*args, **kwargs):
    from .directory_discovery import list_loaded_directories as _f

    return _f(*args, **kwargs)


def list_imported_directory_modules(*args, **kwargs):
    from .directory_discovery import list_imported_directory_modules as _f

    return _f(*args, **kwargs)


def import_plugins_from_environment(*args, **kwargs):
    from .environment_discovery import import_plugins_from_environment as _f

    return _f(*args, **kwargs)


def reset_environment_discovery(*args, **kwargs):
    from .environment_discovery import reset_environment_discovery as _f

    return _f(*args, **kwargs)


def get_environment_discovery_summary(*args, **kwargs):
    from .environment_discovery import get_environment_discovery_summary as _f

    return _f(*args, **kwargs)


def list_imported_environment_packages(*args, **kwargs):
    from .environment_discovery import list_imported_environment_packages as _f

    return _f(*args, **kwargs)


def list_installed_environment_packages(*args, **kwargs):
    from .environment_discovery import list_installed_environment_packages as _f

    return _f(*args, **kwargs)


def get_sdk_version(*args, **kwargs):
    from .helpers import get_sdk_version as _f

    return _f(*args, **kwargs)


def check_compatibility(*args, **kwargs):
    from .helpers import check_compatibility as _f

    return _f(*args, **kwargs)


def format_plugin_info(*args, **kwargs):
    from .helpers import format_plugin_info as _f

    return _f(*args, **kwargs)


def install_packages(*args, **kwargs):
    from .installers import install_packages as _f

    return _f(*args, **kwargs)


def validate_plugin_structure(*args, **kwargs):
    from .validation import validate_plugin_structure as _f

    return _f(*args, **kwargs)


def validate_tools(*args, **kwargs):
    from .validation import validate_tools as _f

    return _f(*args, **kwargs)


__all__ = [
    "validate_plugin_structure",
    "validate_tools",
    "get_sdk_version",
    "check_compatibility",
    "format_plugin_info",
    "import_plugins_from_environment",
    "import_plugins_from_directories",
    "reset_directory_discovery",
    "get_directory_discovery_summary",
    "list_loaded_directories",
    "list_imported_directory_modules",
    "get_environment_discovery_summary",
    "list_installed_environment_packages",
    "list_imported_environment_packages",
    "reset_environment_discovery",
    "install_packages",
]
