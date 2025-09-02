"""Plugin metadata and configuration types."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ModelConfig:
    """Configuration for LLM models used by plugins."""

    provider: str = "openai"
    model_name: str = "gpt-4o"
    temperature: float = 0.0
    max_tokens: int = 1024
    api_key: Optional[str] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normalize mutable defaults after initialization."""
        if self.additional_params is None:
            self.additional_params = {}


@dataclass
class PluginMetadata:
    """Comprehensive metadata for plugin bundles.

    Defines all the information the Cadence core system needs to know
    about a plugin without importing the plugin directly.
    """

    name: str
    version: str
    description: str
    agent_type: str = "specialized"

    capabilities: List[str] = field(default_factory=list)
    llm_requirements: Dict[str, Any] = field(default_factory=dict)

    dependencies: List[str] = field(default_factory=list)
    sdk_version: str = ">=1.0.1,<2.0.0"

    def __post_init__(self):
        """Validate metadata after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Plugin name cannot be empty")
        if not self.version or not self.version.strip():
            raise ValueError("Plugin version cannot be empty")
        if self.agent_type not in {"specialized", "general", "utility"}:
            raise ValueError(f"Invalid agent_type: {self.agent_type}")

    @property
    def is_specialized_agent(self) -> bool:
        """Check if this is a specialized agent."""
        return self.agent_type == "specialized"

    @property
    def is_general_agent(self) -> bool:
        """Check if this is a general agent."""
        return self.agent_type == "general"

    @property
    def is_utility_agent(self) -> bool:
        """Check if this is a utility agent."""
        return self.agent_type == "utility"

    def get_model_config(self) -> ModelConfig:
        """Convert LLM requirements to ModelConfig."""
        if not self.llm_requirements:
            return ModelConfig()

        return ModelConfig(
            provider=self.llm_requirements.get("provider", "openai"),
            model_name=self.llm_requirements.get("model", "gpt-4o"),
            temperature=self.llm_requirements.get("temperature", 0.0),
            max_tokens=self.llm_requirements.get("max_tokens", 1024),
            additional_params=self.llm_requirements.get("additional_params", {}),
        )
