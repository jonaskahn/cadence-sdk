"""Plugin metadata definitions.

This module defines the PluginMetadata dataclass that describes a plugin's
capabilities, dependencies, and requirements.

IMPORTANT: v3.0 architectural change - LLM configuration is NO LONGER
part of plugin metadata. The framework owns all LLM configuration.
"""

from dataclasses import dataclass, field
from typing import List

MIN_VERSION_PARTS = 2
MAX_VERSION_PARTS = 3


@dataclass
class PluginMetadata:
    """Metadata describing a Cadence plugin.

    This metadata is used for plugin discovery, validation, and registration.
    It describes what the plugin does and what it needs, but NOT how to
    configure LLMs (that's the framework's responsibility).

    Attributes:
        pid: Globally unique reverse-domain identifier (e.g.,
            "com.example.product_search"). Used as the registry key and
            referenced in orchestrator instance configuration. Immutable
            after registration.
        name: Human-readable display name (e.g., "Product Search"). Can be
            overridden per orchestrator instance in Tier 4 node_settings.
        version: Semantic version string (e.g., "1.2.3")
        description: Human-readable description of plugin capabilities.
            Can be overridden per orchestrator instance in Tier 4
            node_settings.
        capabilities: List of capability tags (e.g., ["search", "web_browsing"])
        dependencies: List of pip package dependencies (e.g., ["requests>=2.28"])
        agent_type: Agent type category (default "specialized")
        sdk_version: Compatible SDK version range (default ">=2.0.0,<4.0.0")
        stateless: Whether this plugin is stateless (default True)

    Example:
        metadata = PluginMetadata(
            pid="com.example.product_search",
            name="Product Search",
            version="1.0.0",
            description="Search products by name, category, or attributes",
            capabilities=["product_search", "product_recommendations"],
            dependencies=["requests>=2.28"],
            stateless=True
        )

    Note:
        - NO ModelConfig or llm_requirements in v3.0+
        - NO should_continue() — framework owns continue/stop decisions
        - Framework handles all LLM configuration via 4-tier settings
        - Plugins declare tools and logic, not models
        - pid uses reverse-domain convention (e.g., com.example.my_plugin)
          to guarantee global uniqueness across all tenants and system plugins
    """

    pid: str
    name: str
    version: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    agent_type: str = "specialized"
    sdk_version: str = ">=2.0.0,<3.0.0"
    stateless: bool = True

    def __post_init__(self):
        """Validate metadata after initialization."""
        self._validate_required_fields()
        self._validate_version_format()

    def _validate_required_fields(self) -> None:
        """Validate all required fields are non-empty."""
        if not self.pid:
            raise ValueError("Plugin pid cannot be empty")
        if not self.name:
            raise ValueError("Plugin name cannot be empty")
        if not self.version:
            raise ValueError("Plugin version cannot be empty")
        if not self.description:
            raise ValueError("Plugin description cannot be empty")

    def _validate_version_format(self) -> None:
        """Validate version follows semantic versioning format."""
        version_parts = self.version.split(".")
        is_valid_format = MIN_VERSION_PARTS <= len(version_parts) <= MAX_VERSION_PARTS

        if not is_valid_format:
            raise ValueError(
                f"Invalid version format: {self.version}. "
                "Expected format: MAJOR.MINOR or MAJOR.MINOR.PATCH"
            )

    def to_dict(self) -> dict:
        """Convert metadata to dictionary.

        Returns:
            Dictionary representation of metadata
        """
        return {
            "pid": self.pid,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "capabilities": self.capabilities,
            "dependencies": self.dependencies,
            "agent_type": self.agent_type,
            "sdk_version": self.sdk_version,
            "stateless": self.stateless,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PluginMetadata":
        """Create metadata from dictionary.

        Args:
            data: Dictionary containing metadata fields

        Returns:
            PluginMetadata instance
        """
        return cls(**data)
