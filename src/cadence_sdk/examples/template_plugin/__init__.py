"""Template plugin for Cadence multi-agent system.

This template demonstrates how to create a Cadence plugin using the SDK.
Auto-registers the plugin when imported.
"""

from cadence_sdk import register_plugin

from .plugin import TemplatePlugin

register_plugin(TemplatePlugin)
