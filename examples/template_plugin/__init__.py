"""Template plugin package."""

from .plugin import TemplatePlugin

__all__ = ["TemplatePlugin"]

from ...src.cadence_sdk import register_plugin

register_plugin(TemplatePlugin)
