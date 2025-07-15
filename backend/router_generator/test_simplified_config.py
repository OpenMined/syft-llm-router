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
)


def test_config_loading():
    """Test that the shared config can be imported and used."""
    print("🧪 Testing simplified configuration system...")

    # Test basic config creation
    config = RouterConfig(
        project_name="test_router",
        enable_chat=True,
        enable_search=True,
        service_urls={
            "ollama": "http://localhost:11434",
            "local_rag": "http://localhost:9000",
        },
    )

    print(f"✅ Created config:")
    print(f"   Project: {config.project_name}")
    print(f"   Chat enabled: {config.enable_chat}")
    print(f"   Search enabled: {config.enable_search}")
    print(f"   Service URLs: {config.service_urls}")

    # Test service URL access
    ollama_url = config.get_service_url("ollama")
    rag_url = config.get_service_url("local_rag")

    assert ollama_url == "http://localhost:11434"
    assert rag_url == "http://localhost:9000"

    print("✅ All tests passed! Simplified configuration system is working correctly.")
    return True


def main():
    """Run the test."""
    print("🚀 Testing simplified configuration system...\n")

    try:
        test_config_loading()
        print("\n🎉 All tests passed!")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
