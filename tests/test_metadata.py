"""Tests for PluginMetadata."""

import pytest
from cadence_sdk import PluginMetadata
from cadence_sdk.base.metadata import MAX_VERSION_PARTS, MIN_VERSION_PARTS


class TestPluginMetadataCreation:
    """Tests for PluginMetadata construction and validation."""

    def test_creates_metadata_with_required_fields(self):
        """PluginMetadata accepts required fields and applies defaults."""
        metadata = PluginMetadata(
            pid="com.example.test",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
        )
        assert metadata.pid == "com.example.test"
        assert metadata.name == "Test Plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == "A test plugin"
        assert metadata.capabilities == []
        assert metadata.dependencies == []
        assert metadata.agent_type == "specialized"
        assert metadata.sdk_version == ">=3.0.0,<4.0.0"
        assert metadata.stateless is True

    def test_creates_metadata_with_all_fields(self):
        """PluginMetadata accepts all optional fields."""
        metadata = PluginMetadata(
            pid="com.example.full",
            name="Full Plugin",
            version="2.1.3",
            description="Full metadata",
            capabilities=["search", "fetch"],
            dependencies=["requests>=2.28"],
            agent_type="general",
            sdk_version=">=3.0.0",
            stateless=False,
        )
        assert metadata.capabilities == ["search", "fetch"]
        assert metadata.dependencies == ["requests>=2.28"]
        assert metadata.agent_type == "general"
        assert metadata.stateless is False

    def test_rejects_empty_pid(self):
        """PluginMetadata raises ValueError when pid is empty."""
        with pytest.raises(ValueError, match="Plugin pid cannot be empty"):
            PluginMetadata(
                pid="",
                name="Test",
                version="1.0.0",
                description="Test",
            )

    def test_rejects_empty_name(self):
        """PluginMetadata raises ValueError when name is empty."""
        with pytest.raises(ValueError, match="Plugin name cannot be empty"):
            PluginMetadata(
                pid="com.test",
                name="",
                version="1.0.0",
                description="Test",
            )

    def test_rejects_empty_version(self):
        """PluginMetadata raises ValueError when version is empty."""
        with pytest.raises(ValueError, match="Plugin version cannot be empty"):
            PluginMetadata(
                pid="com.test",
                name="Test",
                version="",
                description="Test",
            )

    def test_rejects_empty_description(self):
        """PluginMetadata raises ValueError when description is empty."""
        with pytest.raises(ValueError, match="Plugin description cannot be empty"):
            PluginMetadata(
                pid="com.test",
                name="Test",
                version="1.0.0",
                description="",
            )

    def test_rejects_invalid_version_format_single_part(self):
        """PluginMetadata rejects version with only one part."""
        with pytest.raises(ValueError, match="Invalid version format"):
            PluginMetadata(
                pid="com.test",
                name="Test",
                version="1",
                description="Test",
            )

    def test_rejects_invalid_version_format_four_parts(self):
        """PluginMetadata rejects version with four parts."""
        with pytest.raises(ValueError, match="Invalid version format"):
            PluginMetadata(
                pid="com.test",
                name="Test",
                version="1.2.3.4",
                description="Test",
            )

    def test_accepts_two_part_version(self):
        """PluginMetadata accepts MAJOR.MINOR version format."""
        metadata = PluginMetadata(
            pid="com.test",
            name="Test",
            version="1.2",
            description="Test",
        )
        assert metadata.version == "1.2"

    def test_accepts_three_part_version(self):
        """PluginMetadata accepts MAJOR.MINOR.PATCH version format."""
        metadata = PluginMetadata(
            pid="com.test",
            name="Test",
            version="1.2.3",
            description="Test",
        )
        assert metadata.version == "1.2.3"


class TestPluginMetadataSerialization:
    """Tests for to_dict and from_dict."""

    def test_to_dict_returns_all_fields(self):
        """to_dict returns complete dictionary representation."""
        metadata = PluginMetadata(
            pid="com.example.serial",
            name="Serial",
            version="1.0.0",
            description="Serialization test",
            capabilities=["a"],
            dependencies=["b"],
        )
        data = metadata.to_dict()
        assert data["pid"] == "com.example.serial"
        assert data["name"] == "Serial"
        assert data["version"] == "1.0.0"
        assert data["description"] == "Serialization test"
        assert data["capabilities"] == ["a"]
        assert data["dependencies"] == ["b"]
        assert "agent_type" in data
        assert "sdk_version" in data
        assert "stateless" in data

    def test_from_dict_recreates_metadata(self):
        """from_dict creates equivalent PluginMetadata instance."""
        original = PluginMetadata(
            pid="com.example.roundtrip",
            name="Roundtrip",
            version="2.0.0",
            description="Roundtrip test",
            capabilities=["x"],
        )
        data = original.to_dict()
        restored = PluginMetadata.from_dict(data)
        assert restored.pid == original.pid
        assert restored.name == original.name
        assert restored.version == original.version
        assert restored.capabilities == original.capabilities


class TestVersionConstants:
    """Tests for version validation constants."""

    def test_version_constants_are_defined(self):
        """MIN_VERSION_PARTS and MAX_VERSION_PARTS are defined."""
        assert MIN_VERSION_PARTS == 2
        assert MAX_VERSION_PARTS == 3
