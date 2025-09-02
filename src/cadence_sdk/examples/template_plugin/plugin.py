"""Template plugin implementation."""

from cadence_sdk import BaseAgent, BasePlugin, PluginMetadata

from .agent import TemplateAgent


class TemplatePlugin(BasePlugin):
    """Template plugin demonstrating SDK usage."""

    @staticmethod
    def get_metadata() -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="template_plugin",
            version="1.0.5",
            description="Template plugin demonstrating Cadence SDK usage",
            capabilities=[
                "example_capability",
                "template_operation",
                "sdk_demonstration",
            ],
            llm_requirements={
                "provider": "openai",
                "model": "gpt-4o",
                "temperature": 0.1,
                "max_tokens": 1024,
            },
            agent_type="specialized",
            dependencies=["cadence_sdk>=1.0.1,<2.0.0"],
        )

    @staticmethod
    def create_agent() -> BaseAgent:
        """Create template agent instance."""
        return TemplateAgent(TemplatePlugin.get_metadata())

    @staticmethod
    def validate_dependencies() -> list[str]:
        """Validate plugin dependencies."""
        errors = []

        try:
            import cadence_sdk
        except ImportError:
            errors.append("cadence_sdk is required")

        import os

        if not os.getenv("TEMPLATE_API_KEY"):
            errors.append("TEMPLATE_API_KEY environment variable is required")

        return errors

    @staticmethod
    def get_config_schema() -> dict:
        """Return configuration schema."""
        return {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "API key for template service",
                },
                "timeout": {
                    "type": "integer",
                    "default": 30,
                    "description": "Request timeout in seconds",
                },
                "max_retries": {
                    "type": "integer",
                    "default": 3,
                    "description": "Maximum number of retries",
                },
            },
            "required": ["api_key"],
        }

    @staticmethod
    def health_check() -> dict:
        """Perform health check."""
        try:
            return {
                "healthy": True,
                "details": "Template plugin is operational",
                "checks": {
                    "dependencies": "OK",
                    "configuration": "OK",
                    "external_service": "OK",
                },
            }
        except Exception as e:
            return {
                "healthy": False,
                "details": f"Health check failed: {e}",
                "error": str(e),
            }
