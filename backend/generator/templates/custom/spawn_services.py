#!/usr/bin/env python3
"""
Custom Service Spawner for Syft LLM Router
Handles spawning and monitoring of custom chat and search services.
"""

import argparse
import logging
import sys
from config import RunStatus, load_config
from syft_core import Client

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
        client = Client.load(config_path)

        # metadata path
        metadata_path = (
            client.my_datasite / "public" / "routers" / project_name / "metadata.json"
        )

        # Load config
        self.config = load_config(
            syft_config_path=client.config.path,
            metadata_path=metadata_path,
        )

        self.enable_chat = self.config.enable_chat
        self.enable_search = self.config.enable_search

        # URLs will be discovered dynamically when services are spawned
        self.custom_chat_url = None
        self.custom_search_url = None

        # Update state
        self._initialize_state()

        logger.info(f"Custom Service Manager initialized for {project_name}")
        logger.info(f"Chat enabled: {self.enable_chat}")
        logger.info(f"Search enabled: {self.enable_search}")

    def _initialize_state(self) -> None:
        """Update state."""
        if self.enable_chat:
            self.config.state.update_service_state(
                "chat",
                status=RunStatus.STOPPED,
                url=None,
                port=None,
                pid=None,
                started_at=None,
                error=None,
            )
        if self.enable_search:
            self.config.state.update_service_state(
                "search",
                status=RunStatus.STOPPED,
                url=None,
                port=None,
                pid=None,
                started_at=None,
                error=None,
            )

    def spawn_custom_chat(self) -> bool:
        """Spawn and verify custom chat service."""
        logger.info("🔧 Setting up custom chat service...")
        try:
            # TODO: Add your custom chat service setup logic here
            # Example: Start a subprocess, check API health, etc.
            # If successful:
            # self.custom_chat_url = "http://localhost:12345"
            # self.config.state.update_service_state(
            #     "chat",
            #     status=RunStatus.RUNNING,
            #     started_at=datetime.now().isoformat(),
            #     url=self.custom_chat_url,
            # )
            # return True

            # Placeholder implementation
            logger.warning("⚠️  Custom chat service spawning not implemented")
            self.config.state.update_service_state(
                "chat", status=RunStatus.FAILED, error="Not implemented"
            )
            return False
        except Exception as e:
            logger.error(f"❌ Custom chat service setup failed: {e}")
            self.config.state.update_service_state(
                "chat", status=RunStatus.FAILED, error=str(e)
            )
            return False

    def spawn_custom_search(self) -> bool:
        """Spawn and verify custom search service."""
        logger.info("🔍 Setting up custom search service...")
        try:
            # TODO: Add your custom search service setup logic here
            # Example: Start a subprocess, check API health, etc.
            # If successful:
            # self.custom_search_url = "http://localhost:23456"
            # self.config.state.update_service_state(
            #     "search",
            #     status=RunStatus.RUNNING,
            #     started_at=datetime.now().isoformat(),
            #     url=self.custom_search_url,
            # )
            # return True

            # Placeholder implementation
            logger.warning("⚠️  Custom search service spawning not implemented")
            self.config.state.update_service_state(
                "search", status=RunStatus.FAILED, error="Not implemented"
            )
            return False
        except Exception as e:
            logger.error(f"❌ Custom search service setup failed: {e}")
            self.config.state.update_service_state(
                "search", status=RunStatus.FAILED, error=str(e)
            )
            return False

    def health_check_custom_chat(self) -> bool:
        """Health check for custom chat service."""
        # TODO: Implement comprehensive health check
        logger.debug("🔍 Performing custom chat health check...")
        return True

    def health_check_custom_search(self) -> bool:
        """Health check for custom search service."""
        # TODO: Implement comprehensive health check
        logger.debug("🔍 Performing custom search health check...")
        return True

    def spawn_services(self) -> bool:
        """Spawn all enabled services in dependency order."""
        logger.info("🚀 Starting custom service spawning process...")
        services_to_spawn = []
        if self.enable_chat:
            services_to_spawn.append(("chat", self.spawn_custom_chat))
        if self.enable_search:
            services_to_spawn.append(("search", self.spawn_custom_search))

        if not services_to_spawn:
            logger.info("ℹ️  No services enabled - skipping service spawning")
            return True

        for service_name, spawn_func in services_to_spawn:
            logger.info(f"🔄 Spawning {service_name}...")
            if not spawn_func():
                logger.error(f"❌ Failed to spawn {service_name}")
                self.config.state.update_router_state(status=RunStatus.STOPPED)
                return False
            logger.info(f"✅ {service_name} spawned successfully")

        # Perform health checks
        logger.info("🔍 Performing health checks...")
        health_checks = []
        if self.enable_chat:
            health_checks.append(("chat", self.health_check_custom_chat))
        if self.enable_search:
            health_checks.append(("search", self.health_check_custom_search))

        for service_name, health_check_func in health_checks:
            if not health_check_func():
                logger.error(f"❌ Health check failed for {service_name}")
                self.config.state.update_router_state(status=RunStatus.STOPPED)
                return False
        logger.info("✅ All custom services spawned and healthy")
        self._save_service_urls()
        return True

    def cleanup_services(self) -> None:
        """Cleanup services on shutdown."""
        logger.info("🧹 Cleaning up custom services...")
        self.config.state.update_router_state(status=RunStatus.STOPPED)
        for service_name in self.config.state.services.keys():
            self.config.state.update_service_state(
                service_name, status=RunStatus.STOPPED
            )
        logger.info("✅ Custom service cleanup completed")

    def _save_service_urls(self) -> None:
        """Save discovered service URLs to state and update .env file."""
        logger.info("💾 Saving discovered service URLs...")
        if self.custom_chat_url:
            self.config.state.update_service_state("chat", url=self.custom_chat_url)
        if self.custom_search_url:
            self.config.state.update_service_state("search", url=self.custom_search_url)


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
