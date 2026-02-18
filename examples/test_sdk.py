#!/usr/bin/env python3
"""Test script to verify Cadence SDK functionality."""

import asyncio
import sys
from pathlib import Path

# Add SDK to path
sdk_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(sdk_path))

# Add template plugin to path
template_path = Path(__file__).parent / "template_plugin"
sys.path.insert(0, str(template_path))


def test_imports():
    """Test that all SDK imports work."""
    print("Testing imports...")

    try:
        from cadence_sdk import (
            BaseAgent,
            BasePlugin,
            CacheConfig,
            PluginContext,
            PluginMetadata,
            PluginRegistry,
            RoutingHelpers,
            StateHelpers,
            UvAIMessage,
            UvHumanMessage,
            UvMessage,
            UvState,
            UvSystemMessage,
            UvTool,
            UvToolMessage,
            plugin_settings,
            register_plugin,
            uvtool,
            validate_plugin_structure,
            validate_plugin_structure_shallow,
        )

        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_plugin_structure():
    """Test plugin structure and metadata."""
    print("\nTesting plugin structure...")

    try:
        from plugin import TemplatePlugin

        # Get metadata
        metadata = TemplatePlugin.get_metadata()
        assert metadata.name == "Template Plugin"
        assert metadata.pid == "io.cadence.examples.template_plugin"
        assert metadata.version == "1.0.0"
        assert "greeting" in metadata.capabilities
        print(f"✓ Plugin metadata: {metadata.name} v{metadata.version}")

        # Create agent
        agent = TemplatePlugin.create_agent()
        assert agent is not None
        print(f"✓ Agent created: {type(agent).__name__}")

        # Get tools
        tools = agent.get_tools()
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "greet" in tool_names
        assert "search" in tool_names
        assert "async_fetch" in tool_names
        print(f"✓ Tools: {tool_names}")

        # Get system prompt
        prompt = agent.get_system_prompt()
        assert len(prompt) > 0
        print(f"✓ System prompt: {len(prompt)} characters")

        return True
    except Exception as e:
        print(f"✗ Plugin structure test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_tool_execution():
    """Test tool execution (sync and async)."""
    print("\nTesting tool execution...")

    try:
        from plugin import TemplatePlugin

        agent = TemplatePlugin.create_agent()

        # Initialize agent with config
        config = {"greeting": "Hi", "max_results": 5, "api_key": "test-key"}
        agent.initialize(config)
        print("✓ Agent initialized with config")

        tools = agent.get_tools()

        # Test greet tool (sync)
        greet_tool = next(t for t in tools if t.name == "greet")
        result = greet_tool(name="World")
        assert "Hi, World!" in result
        print(f"✓ Sync tool execution: {result}")

        # Test search tool (sync, cached)
        search_tool = next(t for t in tools if t.name == "search")
        result = search_tool(query="Python")
        assert "Python" in result
        print(f"✓ Cached tool execution: {result}")

        # Test async tool
        async def test_async():
            async_tool = next(t for t in tools if t.name == "async_fetch")
            result = await async_tool.ainvoke(url="https://example.com")
            assert "example.com" in result
            print(f"✓ Async tool execution: {result}")

        asyncio.run(test_async())

        return True
    except Exception as e:
        print(f"✗ Tool execution test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_registration():
    """Test plugin registration."""
    print("\nTesting plugin registration...")

    try:
        from plugin import TemplatePlugin

        from cadence_sdk import PluginRegistry, register_plugin

        # Clear registry
        PluginRegistry.instance().clear_all()

        # Register plugin (keyed by pid)
        contract = register_plugin(TemplatePlugin)
        assert contract.name == "Template Plugin"
        assert contract.pid == "io.cadence.examples.template_plugin"
        print(f"✓ Plugin registered: {contract}")

        # Verify registration (lookup by pid)
        retrieved = PluginRegistry.instance().get_plugin(
            "io.cadence.examples.template_plugin"
        )
        assert retrieved is not None
        assert retrieved.name == "Template Plugin"
        print(f"✓ Plugin retrieved from registry")

        # List plugins
        all_plugins = PluginRegistry.instance().list_registered_plugins()
        assert len(all_plugins) == 1
        print(f"✓ Registry contains {len(all_plugins)} plugin(s)")

        return True
    except Exception as e:
        print(f"✗ Registration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_validation():
    """Test plugin validation."""
    print("\nTesting plugin validation...")

    try:
        from plugin import TemplatePlugin

        from cadence_sdk import (
            validate_plugin_structure,
            validate_plugin_structure_shallow,
        )

        # Shallow validation
        is_valid, errors = validate_plugin_structure_shallow(TemplatePlugin)
        assert is_valid, f"Shallow validation failed: {errors}"
        print("✓ Shallow validation passed")

        # Deep validation
        is_valid, errors = validate_plugin_structure(TemplatePlugin)
        assert is_valid, f"Deep validation failed: {errors}"
        print("✓ Deep validation passed")

        return True
    except Exception as e:
        print(f"✗ Validation test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_messages():
    """Test message types."""
    print("\nTesting message types...")

    try:
        from cadence_sdk import (
            ToolCall,
            UvAIMessage,
            UvHumanMessage,
            UvSystemMessage,
            UvToolMessage,
        )

        # Human message
        human_msg = UvHumanMessage(content="Hello")
        assert human_msg.role == "human"
        assert human_msg.content == "Hello"
        print("✓ UvHumanMessage")

        # AI message with tool calls
        tool_call = ToolCall(name="search", args={"query": "test"})
        ai_msg = UvAIMessage(content="Let me search", tool_calls=[tool_call])
        assert ai_msg.role == "ai"
        assert len(ai_msg.tool_calls) == 1
        print("✓ UvAIMessage with tool calls")

        # System message
        sys_msg = UvSystemMessage(content="You are helpful")
        assert sys_msg.role == "system"
        print("✓ UvSystemMessage")

        # Tool message
        tool_msg = UvToolMessage(
            content="Result", tool_call_id="call_123", tool_name="search"
        )
        assert tool_msg.role == "tool"
        print("✓ UvToolMessage")

        # Serialization
        msg_dict = human_msg.to_dict()
        reconstructed = UvHumanMessage.from_dict(msg_dict)
        assert reconstructed.content == human_msg.content
        print("✓ Message serialization")

        return True
    except Exception as e:
        print(f"✗ Message test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_state():
    """Test state management."""
    print("\nTesting state management...")

    try:
        from cadence_sdk import (
            RoutingHelpers,
            StateHelpers,
            UvHumanMessage,
            UvState,
            create_initial_state,
        )

        # Create initial state
        state = create_initial_state(
            messages=[UvHumanMessage(content="Test")], thread_id="thread_123"
        )
        assert StateHelpers.safe_get_thread_id(state) == "thread_123"
        assert len(StateHelpers.safe_get_messages(state)) == 1
        print("✓ Initial state creation")

        # Increment hops
        state = StateHelpers.increment_agent_hops(state)
        assert StateHelpers.safe_get_agent_hops(state) == 1
        print("✓ Agent hops increment")

        # Routing history
        state = RoutingHelpers.add_to_routing_history(state, "agent1")
        state = RoutingHelpers.add_to_routing_history(state, "agent2")
        context = StateHelpers.get_plugin_context(state)
        assert len(context["routing_history"]) == 2
        print("✓ Routing history tracking")

        return True
    except Exception as e:
        print(f"✗ State test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Cadence SDK Test Suite")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Plugin Structure", test_plugin_structure),
        ("Tool Execution", test_tool_execution),
        ("Registration", test_registration),
        ("Validation", test_validation),
        ("Messages", test_messages),
        ("State", test_state),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
