"""Framework-agnostic state definitions for Cadence SDK.

This module provides the minimal state contract shared across all
orchestration framework implementations.
"""

from typing import List, Optional

from typing_extensions import TypedDict

from .sdk_messages import AnyMessage


class UvState(TypedDict, total=False):
    """Universal state structure for Cadence orchestrators.

    This TypedDict defines the minimal shared contract between the service
    layer and any orchestration framework adapter. Framework-specific fields
    (routing history, agent hops, error state, etc.) belong in each
    framework's own state type, not here.

    Attributes:
        messages: List of conversation messages
        thread_id: Conversation thread identifier
        user_intent: Concise summary of what the user is trying to accomplish,
            extracted by the router node and propagated to downstream nodes.
    """

    messages: List[AnyMessage]
    thread_id: Optional[str]
    user_intent: Optional[str]
