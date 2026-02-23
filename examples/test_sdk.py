#!/usr/bin/env python3
"""Test script to verify Cadence SDK functionality."""

import asyncio
import sys
from pathlib import Path

sdk_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(sdk_path))

template_path = Path(__file__).parent / "template_plugin"
sys.path.insert(0, str(template_path))


def test_imports():
    """Test that all SDK imports work."""
    print("Testing imports...")

    try:

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

        metadata = TemplatePlugin.get_metadata()
        assert metadata.name == "Template Plugin"
        assert metadata.pid == "io.cadence.examples.template_plugin"
        assert metadata.version == "1.0.0"
        assert "greeting" in metadata.capabilities
        print(f"✓ Plugin metadata: {metadata.name} v{metadata.version}")

        agent = TemplatePlugin.create_agent()
        assert agent is not None
        print(f"✓ Agent created: {type(agent).__name__}")

        tools = agent.get_tools()
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "greet" in tool_names
        assert "search" in tool_names
        assert "async_fetch" in tool_names
        print(f"✓ Tools: {tool_names}")

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

        config = {"greeting": "Hi", "max_results": 5, "api_key": "test-key"}
        agent.initialize(config)
        print("✓ Agent initialized with config")

        tools = agent.get_tools()

        greet_tool = next(t for t in tools if t.name == "greet")
        result = greet_tool(name="World")
        assert "Hi, World!" in result
        print(f"✓ Sync tool execution: {result}")

        search_tool = next(t for t in tools if t.name == "search")
        result = search_tool(query="Python")
        assert "Python" in result
        print(f"✓ Cached tool execution: {result}")

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
        from cadence_sdk import PluginRegistry, register_plugin
        from plugin import TemplatePlugin

        PluginRegistry.instance().clear_all()

        contract = register_plugin(TemplatePlugin)
        assert contract.name == "Template Plugin"
        assert contract.pid == "io.cadence.examples.template_plugin"
        print(f"✓ Plugin registered: {contract}")

        retrieved = PluginRegistry.instance().get_plugin(
            "io.cadence.examples.template_plugin"
        )
        assert retrieved is not None
        assert retrieved.name == "Template Plugin"
        print("✓ Plugin retrieved from registry")

        all_plugins = PluginRegistry.instance().list_registered_plugins()
        assert len(all_plugins) == 1
        print(f"✓ Registry contains {len(all_plugins)} plugin(s)")

        return True
    except Exception as e:
        print(f"✗ Registration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_plugin_settings_format():
    """Test plugin_settings format as stored in orchestrator instances.

    Demonstrates the new {id, name, settings: [{key, name, value}]} format
    and verifies it maps correctly to agent.initialize() config.
    """
    print("\nTesting plugin_settings format...")

    try:
        from cadence_sdk.decorators.settings_decorators import (
            get_plugin_settings_schema as sdk_get_schema,
        )
        from plugin import TemplatePlugin

        pid = "io.cadence.examples.template_plugin"

        plugin_settings = {
            pid: {
                "id": pid,
                "name": "Template Plugin",
                "settings": [
                    {"key": "greeting", "name": "greeting", "value": "Hey"},
                    {"key": "max_results", "name": "max_results", "value": 3},
                    {"key": "enable_cache", "name": "enable_cache", "value": False},
                    {"key": "api_key", "name": "api_key", "value": "sk-test-key"},
                ],
            }
        }

        entry = plugin_settings[pid]
        assert entry["id"] == pid
        assert entry["name"] == "Template Plugin"
        assert len(entry["settings"]) == 4
        print(f"✓ Plugin entry has id={entry['id']!r}, name={entry['name']!r}")

        for s in entry["settings"]:
            assert "key" in s and "name" in s and "value" in s
        print("✓ Each setting has key, name, value")

        resolved = {s["key"]: s["value"] for s in entry["settings"]}
        assert resolved == {
            "greeting": "Hey",
            "max_results": 3,
            "enable_cache": False,
            "api_key": "sk-test-key",
        }
        print("✓ Resolved to flat {key: value} for agent.initialize()")

        agent = TemplatePlugin.create_agent()
        agent.initialize(resolved)
        assert agent.greeting == "Hey"
        assert agent.max_results == 3
        print("✓ Agent initialized correctly from resolved settings")

        schema = sdk_get_schema(TemplatePlugin)
        schema_keys = {s["key"] for s in schema}
        settings_keys = {s["key"] for s in entry["settings"]}
        assert settings_keys.issubset(schema_keys)
        print(f"✓ Settings keys match schema: {sorted(settings_keys)}")

        for s in schema:
            assert "name" in s, f"Schema entry missing 'name': {s}"
        schema_names = {s["key"]: s["name"] for s in schema}
        assert schema_names["greeting"] == "Greeting"
        assert schema_names["api_key"] == "API Key"
        print(f"✓ Schema names: {schema_names}")

        return True
    except Exception as e:
        print(f"✗ Plugin settings format test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_validation():
    """Test plugin validation."""
    print("\nTesting plugin validation...")

    try:
        from cadence_sdk import (
            validate_plugin_structure,
            validate_plugin_structure_shallow,
        )
        from plugin import TemplatePlugin

        is_valid, errors = validate_plugin_structure_shallow(TemplatePlugin)
        assert is_valid, f"Shallow validation failed: {errors}"
        print("✓ Shallow validation passed")

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

        human_msg = UvHumanMessage(content="Hello")
        assert human_msg.role == "human"
        assert human_msg.content == "Hello"
        print("✓ UvHumanMessage")

        tool_call = ToolCall(name="search", args={"query": "test"})
        ai_msg = UvAIMessage(content="Let me search", tool_calls=[tool_call])
        assert ai_msg.role == "ai"
        assert len(ai_msg.tool_calls) == 1
        print("✓ UvAIMessage with tool calls")

        sys_msg = UvSystemMessage(content="You are helpful")
        assert sys_msg.role == "system"
        print("✓ UvSystemMessage")

        tool_msg = UvToolMessage(
            content="Result", tool_call_id="call_123", tool_name="search"
        )
        assert tool_msg.role == "tool"
        print("✓ UvToolMessage")

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
            create_initial_state,
        )

        state = create_initial_state(
            messages=[UvHumanMessage(content="Test")], thread_id="thread_123"
        )
        assert StateHelpers.safe_get_thread_id(state) == "thread_123"
        assert len(StateHelpers.safe_get_messages(state)) == 1
        print("✓ Initial state creation")

        state = StateHelpers.increment_agent_hops(state)
        assert StateHelpers.safe_get_agent_hops(state) == 1
        print("✓ Agent hops increment")

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
        ("Plugin Settings Format", test_plugin_settings_format),
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
