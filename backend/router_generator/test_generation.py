#!/usr/bin/env python3
"""Comprehensive tests for router generation."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List

import pytest

from generate import SimplifiedProjectGenerator, ProjectConfig
from syft_core.config import SyftClientConfig


class TestRouterGeneration:
    """Test router generation for both default and custom types."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def generator(self):
        """Create a generator instance."""
        return SimplifiedProjectGenerator()

    @pytest.fixture
    def _syftbox_config(self, temp_dir):
        """Create a SyftClientConfig instance."""
        return SyftClientConfig(
            data_dir=Path(temp_dir),
            server_url="http://test-server:8001",
            client_url="http://test-client:8002",
            email="test@test.com",
            path=Path(temp_dir) / "syftbox_config.json",
        )

    def test_default_router_generation(self, temp_dir, generator, _syftbox_config):
        """Test default router generation."""
        config = ProjectConfig(
            project_name="test_default_router",
            router_type="default",
            enable_chat=True,
            enable_search=True,
            syftbox_config=_syftbox_config,
        )

        output_dir = os.path.join(temp_dir, "test_default")
        generator.generate_project(config, output_dir)

        # Verify all required files exist
        required_files = [
            "router.py",
            "server.py",
            "base_services.py",
            "schema.py",
            "chat_service.py",
            "search_service.py",
            "config.py",
            "pyproject.toml",
            ".env.example",
            "README.md",
            "run.sh",
            "setup.sh",
            "validate.py",
        ]

        for file_name in required_files:
            file_path = os.path.join(output_dir, file_name)
            assert os.path.exists(file_path), f"Required file {file_name} not found"

        # Verify default chat service contains Ollama implementation
        chat_service_path = os.path.join(output_dir, "chat_service.py")
        with open(chat_service_path, "r") as f:
            content = f.read()
            assert "OllamaChatService" in content
            assert "ollama" in content.lower()
            assert "OLLAMA_BASE_URL" in content

        # Verify default search service contains ChromaDB implementation
        search_service_path = os.path.join(output_dir, "search_service.py")
        with open(search_service_path, "r") as f:
            content = f.read()
            assert "LocalSearchService" in content

        # Verify pyproject.toml contains optional dependencies
        pyproject_path = os.path.join(output_dir, "pyproject.toml")
        with open(pyproject_path, "r") as f:
            content = f.read()
            assert "aiohttp" in content
            assert "[project.optional-dependencies]" in content

    def test_custom_router_generation(self, temp_dir, generator, _syftbox_config):
        """Test custom router generation."""
        config = ProjectConfig(
            project_name="test_custom_router",
            router_type="custom",
            enable_chat=True,
            enable_search=True,
            syftbox_config=_syftbox_config,
        )

        output_dir = os.path.join(temp_dir, "test_custom")
        generator.generate_project(config, output_dir)

        # Verify all required files exist
        required_files = [
            "router.py",
            "server.py",
            "base_services.py",
            "schema.py",
            "chat_service.py",
            "search_service.py",
            "config.py",
            ".env.example",
            "README.md",
            "run.sh",
            "setup.sh",
            "validate.py",
        ]

        for file_name in required_files:
            file_path = os.path.join(output_dir, file_name)
            assert os.path.exists(file_path), f"Required file {file_name} not found"

        # Verify custom chat service contains template with TODOs
        chat_service_path = os.path.join(output_dir, "chat_service.py")
        with open(chat_service_path, "r") as f:
            content = f.read()
            assert "CustomChatService" in content
            assert "TODO:" in content
            assert "NotImplementedError" in content
            assert "ollama" not in content.lower()

        # Verify custom search service contains template with TODOs
        search_service_path = os.path.join(output_dir, "search_service.py")
        with open(search_service_path, "r") as f:
            content = f.read()
            assert "CustomSearchService" in content
            assert "TODO:" in content
            assert "NotImplementedError" in content

        # Verify .env.example contains custom configuration template
        env_path = os.path.join(output_dir, ".env.example")
        with open(env_path, "r") as f:
            content = f.read()
            assert "CUSTOM_CHAT_API_KEY" in content
            assert "CUSTOM_SEARCH_API_KEY" in content
            assert "OLLAMA_BASE_URL" not in content

        # Verify README.md contains custom content
        readme_path = os.path.join(output_dir, "README.md")
        with open(readme_path, "r") as f:
            content = f.read()
            assert "custom" in content.lower()
            assert "Implement your own" in content

    def test_chat_only_router(self, temp_dir, generator, _syftbox_config):
        """Test router generation with only chat enabled."""
        config = ProjectConfig(
            project_name="test_chat_only",
            router_type="default",
            enable_chat=True,
            enable_search=False,
            syftbox_config=_syftbox_config,
        )

        output_dir = os.path.join(temp_dir, "test_chat_only")
        generator.generate_project(config, output_dir)

        # Verify chat service exists
        chat_service_path = os.path.join(output_dir, "chat_service.py")
        assert os.path.exists(chat_service_path)

        # Verify search service exists (but may not be used)
        search_service_path = os.path.join(output_dir, "search_service.py")
        assert os.path.exists(search_service_path)

        # Verify .env.example reflects chat-only configuration
        env_path = os.path.join(output_dir, ".env.example")
        with open(env_path, "r") as f:
            content = f.read()
            assert "ENABLE_CHAT=true" in content
            assert "ENABLE_SEARCH=false" in content

    def test_search_only_router(self, temp_dir, generator, _syftbox_config):
        """Test router generation with only search enabled."""
        config = ProjectConfig(
            project_name="test_search_only",
            router_type="default",
            enable_chat=False,
            enable_search=True,
            syftbox_config=_syftbox_config,
        )

        output_dir = os.path.join(temp_dir, "test_search_only")
        generator.generate_project(config, output_dir)

        # Verify both services exist (templates are always copied)
        chat_service_path = os.path.join(output_dir, "chat_service.py")
        assert os.path.exists(chat_service_path)

        search_service_path = os.path.join(output_dir, "search_service.py")
        assert os.path.exists(search_service_path)

        # Verify .env.example reflects search-only configuration
        env_path = os.path.join(output_dir, ".env.example")
        with open(env_path, "r") as f:
            content = f.read()
            assert "ENABLE_CHAT=false" in content
            assert "ENABLE_SEARCH=true" in content

    def test_router_factory_pattern(self, temp_dir, generator, _syftbox_config):
        """Test that generated router.py contains factory pattern."""
        config = ProjectConfig(
            project_name="test_factory",
            router_type="default",
            enable_chat=True,
            enable_search=True,
            syftbox_config=_syftbox_config,
        )

        output_dir = os.path.join(temp_dir, "test_factory")
        generator.generate_project(config, output_dir)

        # Verify router.py contains factory pattern
        router_path = os.path.join(output_dir, "router.py")
        with open(router_path, "r") as f:
            content = f.read()
            assert "RouterFactory" in content
            assert "create_chat_service" in content
            assert "create_search_service" in content
            assert "ImportError" in content  # Error handling for missing services

    def test_template_directory_structure(self, generator):
        """Test that template directories exist and contain required files."""
        # Check common directory
        common_dir = generator.common_dir
        assert common_dir.exists(), "Common directory not found"

        common_files = ["base_services.py", "schema.py", "server.py"]
        for file_name in common_files:
            file_path = common_dir / file_name
            assert file_path.exists(), f"Common file {file_name} not found"

        # Check templates directory
        templates_dir = generator.templates_dir
        assert templates_dir.exists(), "Templates directory not found"

        # Check default template
        default_dir = templates_dir / "default"
        assert default_dir.exists(), "Default template directory not found"

        default_files = ["chat_service.py", "search_service.py", "config.py"]
        for file_name in default_files:
            file_path = default_dir / file_name
            assert file_path.exists(), f"Default template file {file_name} not found"

        # Check custom template
        custom_dir = templates_dir / "custom"
        assert custom_dir.exists(), "Custom template directory not found"

        custom_files = ["chat_service.py", "search_service.py", "config.py"]
        for file_name in custom_files:
            file_path = custom_dir / file_name
            assert file_path.exists(), f"Custom template file {file_name} not found"

    def test_generated_files_executable(self, temp_dir, generator, _syftbox_config):
        """Test that generated shell scripts are executable."""
        config = ProjectConfig(
            project_name="test_executable",
            router_type="default",
            enable_chat=True,
            enable_search=True,
            syftbox_config=_syftbox_config,
        )

        output_dir = os.path.join(temp_dir, "test_executable")
        generator.generate_project(config, output_dir)

        # Check that shell scripts are executable
        shell_scripts = ["run.sh", "setup.sh"]
        for script_name in shell_scripts:
            script_path = os.path.join(output_dir, script_name)
            assert os.path.exists(script_path), f"Script {script_name} not found"
            assert os.access(
                script_path, os.X_OK
            ), f"Script {script_name} not executable"

    def test_project_config_validation(self, _syftbox_config):
        """Test ProjectConfig validation."""
        # Valid config
        config = ProjectConfig(
            project_name="test_project",
            router_type="default",
            enable_chat=True,
            enable_search=True,
            syftbox_config=_syftbox_config,
        )
        assert config.project_name == "test_project"
        assert config.router_type == "default"
        assert config.enable_chat is True
        assert config.enable_search is True

        # Test default values
        config = ProjectConfig(
            project_name="test_project",
            router_type="custom",
            syftbox_config=_syftbox_config,
        )
        assert config.enable_chat is True  # default
        assert config.enable_search is True  # default

    def test_enable_flags_behavior(self, temp_dir, generator, _syftbox_config):
        """Test the behavior of enable-chat and enable-search flags."""

        # Test 1: Both flags enabled (default behavior)
        config1 = ProjectConfig(
            project_name="test_both_enabled",
            router_type="default",
            enable_chat=True,
            enable_search=True,
            syftbox_config=_syftbox_config,
        )

        output_dir1 = os.path.join(temp_dir, "test_both_enabled")
        generator.generate_project(config1, output_dir1)

        # Verify .env.example has both enabled
        env_path1 = os.path.join(output_dir1, ".env.example")
        with open(env_path1, "r") as f:
            content1 = f.read()
            assert "ENABLE_CHAT=true" in content1
            assert "ENABLE_SEARCH=true" in content1

        # Verify both service files exist (always copied)
        assert os.path.exists(os.path.join(output_dir1, "chat_service.py"))
        assert os.path.exists(os.path.join(output_dir1, "search_service.py"))

        # Test 2: Only chat enabled
        config2 = ProjectConfig(
            project_name="test_chat_only",
            router_type="default",
            enable_chat=True,
            enable_search=False,
            syftbox_config=_syftbox_config,
        )

        output_dir2 = os.path.join(temp_dir, "test_chat_only")
        generator.generate_project(config2, output_dir2)

        # Verify .env.example has chat enabled, search disabled
        env_path2 = os.path.join(output_dir2, ".env.example")
        with open(env_path2, "r") as f:
            content2 = f.read()
            assert "ENABLE_CHAT=true" in content2
            assert "ENABLE_SEARCH=false" in content2

        # Verify both service files still exist (always copied)
        assert os.path.exists(os.path.join(output_dir2, "chat_service.py"))
        assert os.path.exists(os.path.join(output_dir2, "search_service.py"))

        # Test 3: Only search enabled
        config3 = ProjectConfig(
            project_name="test_search_only",
            router_type="default",
            enable_chat=False,
            enable_search=True,
            syftbox_config=_syftbox_config,
        )

        output_dir3 = os.path.join(temp_dir, "test_search_only")
        generator.generate_project(config3, output_dir3)

        # Verify .env.example has search enabled, chat disabled
        env_path3 = os.path.join(output_dir3, ".env.example")
        with open(env_path3, "r") as f:
            content3 = f.read()
            assert "ENABLE_CHAT=false" in content3
            assert "ENABLE_SEARCH=true" in content3

        # Verify both service files still exist (always copied)
        assert os.path.exists(os.path.join(output_dir3, "chat_service.py"))
        assert os.path.exists(os.path.join(output_dir3, "search_service.py"))

        # Test 4: Both disabled
        config4 = ProjectConfig(
            project_name="test_both_disabled",
            router_type="default",
            enable_chat=False,
            enable_search=False,
            syftbox_config=_syftbox_config,
        )

        output_dir4 = os.path.join(temp_dir, "test_both_disabled")
        generator.generate_project(config4, output_dir4)

        # Verify .env.example has both disabled
        env_path4 = os.path.join(output_dir4, ".env.example")
        with open(env_path4, "r") as f:
            content4 = f.read()
            assert "ENABLE_CHAT=false" in content4
            assert "ENABLE_SEARCH=false" in content4

        # Verify both service files still exist (always copied)
        assert os.path.exists(os.path.join(output_dir4, "chat_service.py"))
        assert os.path.exists(os.path.join(output_dir4, "search_service.py"))

    def test_router_runtime_behavior(self, temp_dir, generator, _syftbox_config):
        """Test that the generated router.py correctly handles enable flags at runtime."""
        config = ProjectConfig(
            project_name="test_runtime_behavior",
            router_type="default",
            enable_chat=True,
            enable_search=False,
            syftbox_config=_syftbox_config,
        )

        output_dir = os.path.join(temp_dir, "test_runtime_behavior")
        generator.generate_project(config, output_dir)

        # Verify router.py contains conditional service initialization
        router_path = os.path.join(output_dir, "router.py")
        with open(router_path, "r") as f:
            content = f.read()
            assert "if self.config.enable_chat:" in content
            assert "if self.config.enable_search:" in content
            assert "self.chat_service = RouterFactory.create_chat_service()" in content
            assert (
                "self.search_service = RouterFactory.create_search_service()" in content
            )
            assert (
                "NotImplementedError" in content
            )  # Error handling for disabled services

    def test_cli_flag_behavior(self, temp_dir, _syftbox_config):
        """Test CLI flag behavior and limitations."""
        # This test demonstrates the current CLI limitations
        # The flags are now --disable-chat and --disable-search, both default to enabled

        import subprocess
        import os

        current_dir = os.getcwd()

        _syftbox_config.save()

        # Test with no flags (both enabled)
        result = subprocess.run(
            [
                "/usr/bin/python3",
                os.path.join(current_dir, "generate.py"),
                "--project-name",
                "test_cli_both",
                "--router-type",
                "default",
                "--output-dir",
                temp_dir,
                "--syftbox-config",
                str(_syftbox_config.path),
            ],
            capture_output=True,
            text=True,
            cwd=current_dir,
        )
        assert result.returncode == 0, f"CLI test failed: {result.stderr}"
        assert "💬 Chat: ✅" in result.stdout
        assert "🔍 Search: ✅" in result.stdout

        _syftbox_config.path.unlink()

        # Test with --disable-chat (only search enabled)
        result = subprocess.run(
            [
                "/usr/bin/python3",
                os.path.join(current_dir, "generate.py"),
                "--project-name",
                "test_cli_search",
                "--router-type",
                "default",
                "--disable-chat",
                "--output-dir",
                temp_dir,
            ],
            capture_output=True,
            text=True,
            cwd=current_dir,
        )
        assert result.returncode == 0, f"CLI test failed: {result.stderr}"
        assert "💬 Chat: ❌" in result.stdout
        assert "🔍 Search: ✅" in result.stdout

        # Test with --disable-search (only chat enabled)
        result = subprocess.run(
            [
                "/usr/bin/python3",
                os.path.join(current_dir, "generate.py"),
                "--project-name",
                "test_cli_chat",
                "--router-type",
                "default",
                "--disable-search",
                "--output-dir",
                temp_dir,
            ],
            capture_output=True,
            text=True,
            cwd=current_dir,
        )
        assert result.returncode == 0, f"CLI test failed: {result.stderr}"
        assert "💬 Chat: ✅" in result.stdout
        assert "🔍 Search: ❌" in result.stdout

        # Test with both disabled
        result = subprocess.run(
            [
                "/usr/bin/python3",
                os.path.join(current_dir, "generate.py"),
                "--project-name",
                "test_cli_none",
                "--router-type",
                "default",
                "--disable-chat",
                "--disable-search",
                "--output-dir",
                temp_dir,
            ],
            capture_output=True,
            text=True,
            cwd=current_dir,
        )
        assert result.returncode == 0, f"CLI test failed: {result.stderr}"
        assert "💬 Chat: ❌" in result.stdout
        assert "🔍 Search: ❌" in result.stdout

    def test_custom_router_enable_flags(self, temp_dir, generator, _syftbox_config):
        """Test enable flags with custom router type."""
        config = ProjectConfig(
            project_name="test_custom_enable",
            router_type="custom",
            enable_chat=False,
            enable_search=True,
            syftbox_config=_syftbox_config,
        )

        output_dir = os.path.join(temp_dir, "test_custom_enable")
        generator.generate_project(config, output_dir)

        # Verify .env.example has correct custom configuration
        env_path = os.path.join(output_dir, ".env.example")
        with open(env_path, "r") as f:
            content = f.read()
            assert "ENABLE_CHAT=false" in content
            assert "ENABLE_SEARCH=true" in content
            assert "CUSTOM_CHAT_API_KEY" in content
            assert "CUSTOM_SEARCH_API_KEY" in content

        # Verify both service files exist (always copied)
        assert os.path.exists(os.path.join(output_dir, "chat_service.py"))
        assert os.path.exists(os.path.join(output_dir, "search_service.py"))

        # Verify custom service files contain TODO placeholders
        chat_service_path = os.path.join(output_dir, "chat_service.py")
        with open(chat_service_path, "r") as f:
            content = f.read()
            assert "CustomChatService" in content
            assert "TODO:" in content

    def test_requirements_based_on_enable_flags(
        self, temp_dir, generator, _syftbox_config
    ):
        """Test that pyproject.toml includes optional dependencies and requirements.txt has base deps only."""
        # Test default router with both services
        config1 = ProjectConfig(
            project_name="test_requirements_both",
            router_type="default",
            enable_chat=True,
            enable_search=True,
            syftbox_config=_syftbox_config,
        )

        output_dir1 = os.path.join(temp_dir, "test_requirements_both")
        generator.generate_project(config1, output_dir1)

        # Check pyproject.toml exists and has optional dependencies
        pyproject_path1 = os.path.join(output_dir1, "pyproject.toml")
        assert os.path.exists(pyproject_path1), "pyproject.toml not found"

        with open(pyproject_path1, "r") as f:
            pyproject_content1 = f.read()
            assert "[project.optional-dependencies]" in pyproject_content1
            assert "chat = [" in pyproject_content1
            assert "search = [" in pyproject_content1
            assert "all = [" in pyproject_content1
            assert "aiohttp" in pyproject_content1
            assert "httpx" in pyproject_content1

        # Test default router with only chat enabled
        config2 = ProjectConfig(
            project_name="test_requirements_chat_only",
            router_type="default",
            enable_chat=True,
            enable_search=False,
            syftbox_config=_syftbox_config,
        )

        output_dir2 = os.path.join(temp_dir, "test_requirements_chat_only")
        generator.generate_project(config2, output_dir2)

        # Check setup.sh installs chat extras
        setup_path2 = os.path.join(output_dir2, "setup.sh")
        with open(setup_path2, "r") as f:
            setup_content2 = f.read()
            assert "pip install -e .[chat]" in setup_content2
            assert "with extras: chat" in setup_content2

        # Test default router with neither service enabled
        config3 = ProjectConfig(
            project_name="test_requirements_none",
            router_type="default",
            enable_chat=False,
            enable_search=False,
            syftbox_config=_syftbox_config,
        )

        output_dir3 = os.path.join(temp_dir, "test_requirements_none")
        generator.generate_project(config3, output_dir3)

        # Check setup.sh installs base only
        setup_path3 = os.path.join(output_dir3, "setup.sh")
        with open(setup_path3, "r") as f:
            setup_content3 = f.read()
            assert "pip install -e ." in setup_content3
            assert "(base dependencies only)" in setup_content3

    def test_setup_script_conditional_behavior(
        self, temp_dir, generator, _syftbox_config
    ):
        """Test that setup.sh and run.sh conditionally include service setup based on enable flags."""

        # Test with both services enabled
        config1 = ProjectConfig(
            project_name="test_setup_both",
            router_type="default",
            enable_chat=True,
            enable_search=True,
            syftbox_config=_syftbox_config,
        )

        output_dir1 = os.path.join(temp_dir, "test_setup_both")
        generator.generate_project(config1, output_dir1)

        # Check setup.sh
        setup_path1 = os.path.join(output_dir1, "setup.sh")
        with open(setup_path1, "r") as f:
            setup_content1 = f.read()
            assert "ollama" in setup_content1.lower()

        # Check run.sh
        run_path1 = os.path.join(output_dir1, "run.sh")
        with open(run_path1, "r") as f:
            run_content1 = f.read()
            assert "ollama" in run_content1.lower()

        # Test with only chat enabled
        config2 = ProjectConfig(
            project_name="test_setup_chat_only",
            router_type="default",
            enable_chat=True,
            enable_search=False,
            syftbox_config=_syftbox_config,
        )

        output_dir2 = os.path.join(temp_dir, "test_setup_chat_only")
        generator.generate_project(config2, output_dir2)

        # Check setup.sh
        setup_path2 = os.path.join(output_dir2, "setup.sh")
        with open(setup_path2, "r") as f:
            setup_content2 = f.read()
            assert "ollama" in setup_content2.lower()

        # Check run.sh
        run_path2 = os.path.join(output_dir2, "run.sh")
        with open(run_path2, "r") as f:
            run_content2 = f.read()
            assert "ollama" in run_content2.lower()

        # Test with only search enabled
        config3 = ProjectConfig(
            project_name="test_setup_search_only",
            router_type="default",
            enable_chat=False,
            enable_search=True,
            syftbox_config=_syftbox_config,
        )

        output_dir3 = os.path.join(temp_dir, "test_setup_search_only")
        generator.generate_project(config3, output_dir3)

        # Check setup.sh
        setup_path3 = os.path.join(output_dir3, "setup.sh")
        with open(setup_path3, "r") as f:
            setup_content3 = f.read()
            assert "ollama" not in setup_content3.lower()

        # Test with neither service enabled
        config4 = ProjectConfig(
            project_name="test_setup_none",
            router_type="default",
            enable_chat=False,
            enable_search=False,
            syftbox_config=_syftbox_config,
        )

        output_dir4 = os.path.join(temp_dir, "test_setup_none")
        generator.generate_project(config4, output_dir4)

        # Check setup.sh
        setup_path4 = os.path.join(output_dir4, "setup.sh")
        with open(setup_path4, "r") as f:
            setup_content4 = f.read()
            assert "ollama" not in setup_content4.lower()
            assert "No services enabled" in setup_content4

    def test_run_script_uses_optional_dependencies(
        self, temp_dir, generator, _syftbox_config
    ):
        """Test that run.sh uses pip install with optional dependencies."""
        # Test with both services enabled
        config1 = ProjectConfig(
            project_name="test_run_both",
            router_type="default",
            enable_chat=True,
            enable_search=True,
            syftbox_config=_syftbox_config,
        )

        output_dir1 = os.path.join(temp_dir, "test_run_both")
        generator.generate_project(config1, output_dir1)

        run_path1 = os.path.join(output_dir1, "run.sh")
        with open(run_path1, "r") as f:
            run_content1 = f.read()
            assert "pip install -e .[chat,search]" in run_content1

        # Test with only chat enabled
        config2 = ProjectConfig(
            project_name="test_run_chat",
            router_type="default",
            enable_chat=True,
            enable_search=False,
            syftbox_config=_syftbox_config,
        )

        output_dir2 = os.path.join(temp_dir, "test_run_chat")
        generator.generate_project(config2, output_dir2)

        run_path2 = os.path.join(output_dir2, "run.sh")
        with open(run_path2, "r") as f:
            run_content2 = f.read()
            assert "pip install -e .[chat]" in run_content2

        # Test with no services enabled
        config3 = ProjectConfig(
            project_name="test_run_none",
            router_type="default",
            enable_chat=False,
            enable_search=False,
            syftbox_config=_syftbox_config,
        )

        output_dir3 = os.path.join(temp_dir, "test_run_none")
        generator.generate_project(config3, output_dir3)

        run_path3 = os.path.join(output_dir3, "run.sh")
        with open(run_path3, "r") as f:
            run_content3 = f.read()
            assert "pip install -e ." in run_content3
            assert "[chat" not in run_content3
            assert "[search" not in run_content3

    def test_custom_router_uses_pyproject(self, temp_dir, generator, _syftbox_config):
        """Test that custom router also uses pyproject.toml approach."""
        config = ProjectConfig(
            project_name="test_custom_pyproject",
            router_type="custom",
            enable_chat=False,
            enable_search=False,
            syftbox_config=_syftbox_config,
        )

        output_dir = os.path.join(temp_dir, "test_custom_pyproject")
        generator.generate_project(config, output_dir)

        # Check pyproject.toml exists
        pyproject_path = os.path.join(output_dir, "pyproject.toml")
        assert os.path.exists(
            pyproject_path
        ), "pyproject.toml not found in custom router"

        # Check setup.sh uses pip install -e .
        setup_path = os.path.join(output_dir, "setup.sh")
        with open(setup_path, "r") as f:
            setup_content = f.read()
            assert "pip install -e ." in setup_content
            assert "pyproject.toml" in setup_content

        # Check run.sh uses pip install -e .
        run_path = os.path.join(output_dir, "run.sh")
        with open(run_path, "r") as f:
            run_content = f.read()
            assert "pip install -e ." in run_content


def test_integration_full_workflow():
    """Integration test: generate, setup, and validate a complete workflow."""
    # This test would require more setup (Ollama, etc.)
    # For now, just test that generation works without errors
    generator = SimplifiedProjectGenerator()

    with tempfile.TemporaryDirectory() as temp_dir:
        config = ProjectConfig(
            project_name="integration_test",
            router_type="default",
            enable_chat=True,
            enable_search=True,
            syftbox_config=SyftClientConfig(
                data_dir=Path(temp_dir),
                server_url="http://test-server:8001",
                client_url="http://test-client:8002",
                email="test@test.com",
                path=Path(temp_dir) / "syftbox_config.json",
            ),
        )

        output_dir = os.path.join(temp_dir, "integration_test")
        generator.generate_project(config, output_dir)

        # Verify the project was generated successfully
        assert os.path.exists(output_dir)
        assert os.path.exists(os.path.join(output_dir, "router.py"))
        assert os.path.exists(os.path.join(output_dir, "server.py"))


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
