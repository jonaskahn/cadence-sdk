"""Internal utility for finding BasePlugin subclasses in imported modules."""

from typing import Any, Optional, Type


def is_plugin_class(attr: Any) -> bool:
    """Return True if attr is a concrete BasePlugin subclass."""
    from ..base import BasePlugin

    return (
        isinstance(attr, type)
        and issubclass(attr, BasePlugin)
        and attr is not BasePlugin
    )


def find_plugin_class(module) -> Optional[Type]:
    """Return the first BasePlugin subclass found in module, or None."""
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if is_plugin_class(attr):
            return attr
    return None
