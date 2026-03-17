"""Plugin contract wrapper for standardized interface."""

from typing import Optional, Type

from ..base import (
    BaseAgent,
    BasePlugin,
    BaseScopedAgent,
    BaseSpecializedAgent,
    PluginMetadata,
)


class PluginContract:
    """Wrapper providing standardized interface to plugin classes.

    The PluginContract wraps a plugin class and provides a consistent
    interface for the framework to interact with plugins, regardless
    of implementation details.

    This abstraction allows plugins to evolve independently while
    maintaining a stable contract with the framework.

    Attributes:
        plugin_class: The plugin class being wrapped
        metadata: Cached metadata from plugin
    """

    def __init__(self, plugin_class: Type[BasePlugin]):
        if not issubclass(plugin_class, BasePlugin):
            raise TypeError(f"{plugin_class.__name__} must inherit from BasePlugin")

        self.plugin_class = plugin_class
        self._metadata: Optional[PluginMetadata] = None
        self._agent_type_cache: Optional[tuple[bool, bool]] = None

    @property
    def metadata(self) -> PluginMetadata:
        if self._metadata is None:
            self._metadata = self.plugin_class.get_metadata()
        return self._metadata

    @property
    def pid(self) -> str:
        return self.metadata.pid

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def version(self) -> str:
        return self.metadata.version

    @property
    def description(self) -> str:
        return self.metadata.description

    @property
    def capabilities(self) -> list[str]:
        return self.metadata.capabilities

    def _get_agent_type_flags(self) -> tuple[bool, bool]:
        if self._agent_type_cache is None:
            agent = self.plugin_class.create_agent()
            self._agent_type_cache = (
                isinstance(agent, BaseSpecializedAgent),
                isinstance(agent, BaseScopedAgent),
            )
        return self._agent_type_cache

    @property
    def is_specialized(self) -> bool:
        return self._get_agent_type_flags()[0]

    @property
    def is_scoped(self) -> bool:
        return self._get_agent_type_flags()[1]

    @property
    def is_stateless(self) -> bool:
        return self.metadata.stateless

    def create_agent(self) -> BaseAgent:
        return self.plugin_class.create_agent()

    def validate_dependencies(self) -> list[str]:
        return self.plugin_class.validate_dependencies()

    def health_check(self) -> dict:
        return self.plugin_class.health_check()

    def __repr__(self) -> str:
        return f"PluginContract(pid='{self.pid}', version='{self.version}')"

    def __eq__(self, other) -> bool:
        if not isinstance(other, PluginContract):
            return False
        return self.pid == other.pid and self.version == other.version

    def __hash__(self) -> int:
        return hash((self.pid, self.version))
