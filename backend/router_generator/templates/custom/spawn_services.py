#!/usr/bin/env python3
"""
Custom Service Spawner for Syft LLM Router
Template for implementing custom chat and search service spawning.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
from config import ProjectInfo, RouterConfiguration, RouterState, RunStatus, StateFile

# Configure verbose logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("spawn_services.log"),
    ],
)
logger = logging.getLogger(__name__)


class CustomServiceManager:
    """Manages custom service spawning, monitoring, and state tracking."""

    def __init__(self, project_name: str, config_path: str):
        self.project_name = project_name
        self.config_path = Path(config_path)
        self.state_file = Path("state.json")
        self.env_file = Path(".env")

        # Load environment variables
        load_dotenv(self.env_file)

        # Service configuration from .env
        self.enable_chat = os.getenv("ENABLE_CHAT", "true").lower() == "true"
        self.enable_search = os.getenv("ENABLE_SEARCH", "true").lower() == "true"

        # TODO: Add your custom service configuration from .env
        # Example:
        # self.custom_chat_api_key = os.getenv("CUSTOM_CHAT_API_KEY")
        # self.custom_search_api_key = os.getenv("CUSTOM_SEARCH_API_KEY")

        # URLs will be discovered dynamically when services are spawned
        self.custom_chat_url = None
        self.custom_search_url = None

        # Initialize state
        self.state = self._load_state()

        logger.info(f"Custom Service Manager initialized for {project_name}")
        logger.info(f"Chat enabled: {self.enable_chat}")
        logger.info(f"Search enabled: {self.enable_search}")

    def _load_state(self) -> Dict[str, Any]:
        """Load service state from state.json."""
        if self.state_file.exists():
            try:
                return StateFile.load(self.state_file)
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")

        # Initialize default state with new unified structure
        project_info = ProjectInfo(name=self.project_name, version="1.0.0")
        router_configuration = RouterConfiguration(
            enable_chat=self.enable_chat,
            enable_search=self.enable_search,
        )
        state = StateFile(
            project=project_info,
            configuration=router_configuration,
            services={},
        )

        state.save(self.state_file)

        # Initialize service states based on enabled services
        if self.enable_chat:
            state.update_service_state(
                "chat",
                status=RunStatus.STOPPED,
                url=None,
                port=None,
                pid=None,
                started_at=None,
                error=None,
            )

        if self.enable_search:
            state.update_service_state(
                "search",
                status=RunStatus.STOPPED,
                url=None,
                port=None,
                pid=None,
                started_at=None,
                error=None,
            )

        return state

    def spawn_custom_chat(self) -> bool:
        """
        TODO: Implement your custom chat service spawning logic.

        This method should:
        1. Set up your chat service (e.g., API client, local service, etc.)
        2. Verify the service is working
        3. Update service state on success/failure
        4. Return True if successful, False otherwise

        Example implementation:
        """
        logger.info("🔧 Setting up custom chat service...")

        try:
            # TODO: Add your custom chat service setup logic here
            # Example:
            # 1. Initialize your chat service client
            # 2. Test connection to your chat service
            # 3. Verify authentication/credentials
            # 4. Check if required models are available

            # Placeholder implementation
            logger.warning("⚠️  Custom chat service spawning not implemented")
            logger.info(
                "💡 Please implement spawn_custom_chat() method in spawn_services.py"
            )

            # For now, mark as failed so router doesn't start
            self.state.update_service_state(
                "chat", status=RunStatus.FAILED, error="Not implemented"
            )
            return False

        except Exception as e:
            logger.error(f"❌ Custom chat service setup failed: {e}")
            self.state.update_service_state(
                "chat", status=RunStatus.FAILED, error=str(e)
            )
            return False

    def spawn_custom_search(self) -> bool:
        """
        TODO: Implement your custom search service spawning logic.

        This method should:
        1. Set up your search service (e.g., vector database, RAG service, etc.)
        2. Verify the service is working
        3. Update service state on success/failure
        4. Return True if successful, False otherwise

        Example implementation:
        """
        logger.info("🔍 Setting up custom search service...")

        try:
            # TODO: Add your custom search service setup logic here
            # Example:
            # 1. Initialize your vector database connection
            # 2. Set up embeddings model
            # 3. Load/verify document index
            # 4. Test search functionality

            # Placeholder implementation
            logger.warning("⚠️  Custom search service spawning not implemented")
            logger.info(
                "💡 Please implement spawn_custom_search() method in spawn_services.py"
            )

            # For now, mark as failed so router doesn't start
            self.state.update_service_state(
                "search", status=RunStatus.FAILED, error="Not implemented"
            )
            return False

        except Exception as e:
            logger.error(f"❌ Custom search service setup failed: {e}")
            self.state.update_service_state(
                "search", status=RunStatus.FAILED, error=str(e)
            )
            return False

    def health_check_custom_chat(self) -> bool:
        """
        TODO: Implement health check for your custom chat service.

        This method should:
        1. Verify your chat service is still responding
        2. Check if it can process requests
        3. Return True if healthy, False otherwise
        """
        # TODO: Implement comprehensive health check
        logger.debug("🔍 Performing custom chat health check...")
        return True

    def health_check_custom_search(self) -> bool:
        """
        TODO: Implement health check for your custom search service.

        This method should:
        1. Verify your search service is still responding
        2. Check if it can process search queries
        3. Return True if healthy, False otherwise
        """
        # TODO: Implement comprehensive health check
        logger.debug("🔍 Performing custom search health check...")
        return True

    def spawn_services(self) -> bool:
        """Spawn all enabled services in dependency order."""
        logger.info("🚀 Starting custom service spawning process...")

        # Determine service dependencies
        services_to_spawn = []
        if self.enable_chat:
            services_to_spawn.append(("custom_chat", self.spawn_custom_chat))
        if self.enable_search:
            services_to_spawn.append(("custom_search", self.spawn_custom_search))

        if not services_to_spawn:
            logger.info("ℹ️  No services enabled - skipping service spawning")
            return True

        # Spawn services in order
        for service_name, spawn_func in services_to_spawn:
            logger.info(f"🔄 Spawning {service_name}...")

            if not spawn_func():
                logger.error(f"❌ Failed to spawn {service_name}")
                self.state.update_router_state(status=RunStatus.STOPPED)
                return False

            logger.info(f"✅ {service_name} spawned successfully")

        # Perform health checks
        logger.info("🔍 Performing health checks...")
        health_checks = []

        if self.enable_chat:
            health_checks.append(("custom_chat", self.health_check_custom_chat))
        if self.enable_search:
            health_checks.append(("custom_search", self.health_check_custom_search))

        for service_name, health_check_func in health_checks:
            if not health_check_func():
                logger.error(f"❌ Health check failed for {service_name}")
                self.state.update_router_state(status=RunStatus.STOPPED)
                return False

        logger.info("✅ All custom services spawned and healthy")

        # Save discovered URLs to state and update .env
        self._save_service_urls()

        return True

    def cleanup_services(self) -> None:
        """Cleanup services on shutdown."""
        logger.info("🧹 Cleaning up custom services...")

        # TODO: Add your custom cleanup logic here
        # Example:
        # - Close database connections
        # - Stop background processes
        # - Clean up temporary files

        # Update router state
        self.state.update_router_state(status=RunStatus.STOPPED)

        # Update service states
        for service_name in self.state.services.keys():
            self.state.update_service_state(service_name, status=RunStatus.STOPPED)

        logger.info("✅ Custom service cleanup completed")

    def _save_service_urls(self) -> None:
        """Save discovered service URLs to state and update .env file."""
        logger.info("💾 Saving discovered service URLs...")

        # TODO: Update state with discovered URLs
        # Example:
        # if self.custom_chat_url:
        #     self.state.update_service_state("chat", url=self.custom_chat_url)
        #
        # if self.custom_search_url:
        #     self.state.update_service_state("search", url=self.custom_search_url)

        logger.info(
            "💡 Please implement _save_service_urls() method for your custom services"
        )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Spawn custom services for Syft LLM Router"
    )
    parser.add_argument("--project-name", required=True, help="Name of the project")
    parser.add_argument("--config-path", required=True, help="Path to syftbox config")
    parser.add_argument(
        "--cleanup", action="store_true", help="Cleanup services and exit"
    )

    args = parser.parse_args()

    try:
        manager = CustomServiceManager(args.project_name, args.config_path)

        if args.cleanup:
            manager.cleanup_services()
            return 0

        # Spawn services
        if manager.spawn_services():
            logger.info("🎉 All custom services ready - router can start")
            return 0
        else:
            logger.error("💥 Custom service spawning failed - router should not start")
            return 1

    except Exception as e:
        logger.error(f"💥 Custom service spawning error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
