#!/usr/bin/env python3
"""Test script for the simplified configuration system."""

import json
import tempfile
import os
from pathlib import Path
from config import (
    RouterConfig,
    StateFile,
    ProjectInfo,
    RouterConfiguration,
    ServiceState,
    RouterState,
    RunStatus,
)


def test_config_creation():
    """Test that the simplified config can be created and used."""
    print("🧪 Testing simplified configuration system...")

    # Create a StateFile
    state = StateFile(
        project=ProjectInfo(name="test_router", version="1.0.0"),
        configuration=RouterConfiguration(enable_chat=True, enable_search=True),
        services={
            "ollama": ServiceState(
                status=RunStatus.RUNNING, url="http://localhost:11434"
            ),
            "local_rag": ServiceState(
                status=RunStatus.RUNNING, url="http://localhost:9000"
            ),
        },
        router=RouterState(status=RunStatus.RUNNING),
    )

    # Create RouterConfig from StateFile
    config = RouterConfig(state)

    print(f"✅ Created config:")
    print(f"   Project: {config.project_name}")
    print(f"   Chat enabled: {config.enable_chat}")
    print(f"   Search enabled: {config.enable_search}")
    print(f"   Service URLs: {config.service_urls}")

    # Test service URL access
    ollama_url = config.get_service_url("ollama")
    rag_url = config.get_service_url("local_rag")

    assert config.project_name == "test_router"
    assert config.enable_chat == True
    assert config.enable_search == True
    assert ollama_url == "http://localhost:11434"
    assert rag_url == "http://localhost:9000"
    assert "ollama" in config.service_urls
    assert "local_rag" in config.service_urls

    print("✅ All tests passed! Simplified configuration system is working correctly.")
    return True


def test_state_file_methods():
    """Test StateFile methods work correctly."""
    print("🧪 Testing StateFile methods...")

    # Create a StateFile
    state = StateFile(
        project=ProjectInfo(name="test_router", version="1.0.0"),
        configuration=RouterConfiguration(enable_chat=True, enable_search=True),
        services={},
        router=RouterState(status=RunStatus.STOPPED),
    )

    # Test updating service state
    state.update_service_state(
        "ollama", status=RunStatus.RUNNING, url="http://localhost:11434"
    )

    # Test updating router state
    state.update_router_state(status=RunStatus.RUNNING)

    # Verify updates
    assert state.services["ollama"].status == RunStatus.RUNNING
    assert state.services["ollama"].url == "http://localhost:11434"
    assert state.router.status == RunStatus.RUNNING

    print("✅ StateFile methods work correctly!")
    return True


def main():
    """Run the tests."""
    print("🚀 Testing simplified configuration system...\n")

    try:
        test_config_creation()
        print()
        test_state_file_methods()
        print("\n🎉 All tests passed!")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
