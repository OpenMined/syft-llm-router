#!/usr/bin/env python3
"""
Default Service Spawner for Syft LLM Router
Handles spawning and monitoring of Ollama and Local RAG services.
"""

import argparse
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
import requests
from syft_core import Client
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


class RunStatus:
    """Represents the state of a service."""

    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass
class ServiceState:
    """Represents the state of a service."""

    status: RunStatus
    port: Optional[int] = None
    pid: Optional[int] = None
    started_at: Optional[str] = None
    error: Optional[str] = None
    url: Optional[str] = None


@dataclass
class RouterState:
    """Represents the state of the router."""

    status: RunStatus
    started_at: Optional[str] = None
    depends_on: List[str] = None


class ServiceManager:
    """Manages service spawning, monitoring, and state tracking."""

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

        # URLs will be discovered dynamically when services are spawned
        self.ollama_base_url = None
        self.rag_service_url = None

        # Initialize state
        self.state = self._load_state()

        logger.info(f"Service Manager initialized for {project_name}")
        logger.info(f"Chat enabled: {self.enable_chat}")
        logger.info(f"Search enabled: {self.enable_search}")

    def _load_state(self) -> Dict[str, Any]:
        """Load service state from state.json."""
        if self.state_file.exists():
            try:
                return StateFile.load(self.state_file)
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
        else:
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
            return state

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

    def spawn_ollama(self) -> bool:
        """Spawn and verify Ollama service."""
        logger.info("🔧 Setting up Ollama service...")

        try:
            # Check if Ollama is installed
            result = subprocess.run(
                ["ollama", "--version"], capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                logger.error("❌ Ollama not found. Please install Ollama first:")
                logger.error("   curl -fsSL https://ollama.ai/install.sh | sh")
                self.state.update_service_state(
                    "chat", status=RunStatus.FAILED, error="Ollama not installed"
                )
                return False

            logger.info(f"✅ Ollama found: {result.stdout.strip()}")

            # Check if required model is available
            result = subprocess.run(
                ["ollama", "list"], capture_output=True, text=True, timeout=10
            )

            if "tinyllama" not in result.stdout:
                logger.info("📥 Pulling tinyllama model...")
                pull_result = subprocess.run(
                    ["ollama", "pull", "tinyllama:latest"],
                    capture_output=True,
                    text=True,
                    timeout=600,  # 10 minutes timeout for model download
                )

                if pull_result.returncode != 0:
                    logger.error(f"❌ Failed to pull tinyllama: {pull_result.stderr}")
                    self.state.update_service_state(
                        "chat", status=RunStatus.FAILED, error="Model pull failed"
                    )
                    return False

                logger.info("✅ tinyllama model pulled successfully")

            # Discover Ollama URL and verify it's responding

            ollama_urls = ["http://localhost:11434", "http://127.0.0.1:11434"]

            for url in ollama_urls:
                try:
                    response = requests.get(f"{url}/api/tags", timeout=5)
                    if response.status_code == 200:
                        self.ollama_base_url = url
                        logger.info(f"✅ Ollama service discovered at {url}")
                        self.state.update_service_state(
                            "chat",
                            status=RunStatus.RUNNING,
                            started_at=datetime.now().isoformat(),
                        )
                        return True
                except Exception:
                    continue

            logger.error("❌ Ollama service not found on any expected URL")
            self.state.update_service_state(
                "chat", status=RunStatus.FAILED, error="Service not found"
            )
            return False

        except subprocess.TimeoutExpired:
            logger.error("❌ Ollama setup timed out")
            self.state.update_service_state(
                "chat", status=RunStatus.FAILED, error="Setup timeout"
            )
            return False
        except Exception as e:
            logger.error(f"❌ Ollama setup failed: {e}")
            self.state.update_service_state(
                "chat", status=RunStatus.FAILED, error=str(e)
            )
            return False

    def spawn_local_rag(self) -> bool:
        """Spawn and verify Local RAG service."""
        logger.info("🔍 Setting up Local RAG service...")

        try:
            # Check if syftbox is available
            result = subprocess.run(
                ["syftbox", "--version"], capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                logger.error("❌ syftbox not found. Please install syftbox first.")
                self.state.update_service_state(
                    "search", status="failed", error="syftbox not installed"
                )
                return False

            logger.info(f"✅ syftbox found: {result.stdout.strip()}")

            # Check if local-rag is already installed
            result = subprocess.run(
                ["syftbox", "app", "list", "-c", self.config_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if "local-rag" not in result.stdout:
                logger.info("📥 Installing local-rag...")
                install_result = subprocess.run(
                    [
                        "syftbox",
                        "app",
                        "install",
                        "https://github.com/OpenMined/local-rag",
                        "--config",
                        self.config_path,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minutes timeout for installation
                )

                if install_result.returncode != 0:
                    logger.error(
                        f"❌ Failed to install local-rag: {install_result.stderr}"
                    )
                    self.state.update_service_state(
                        "search",
                        status=RunStatus.FAILED,
                        error="Installation failed",
                    )
                    return False

                logger.info("✅ local-rag installed successfully")

            # Wait for local-rag to be ready and discover its URL
            logger.info("⏳ Waiting for local-rag to be ready...")

            # Check if app.pid and app.port are set
            client = Client.load(self.config_path)
            app_folder = (
                client.workspace.data_dir / "apps" / "com.github.openmined.local-rag"
            )
            app_pid = app_folder / "data" / "app.pid"
            app_port = app_folder / "data" / "app.port"

            max_wait_time = 300  # 5 minutes
            start_time = time.time()

            # Wait for app.port to be set and app.pid to be set
            while time.time() - start_time < max_wait_time:
                if app_port.exists() and app_pid.exists():
                    app_port = app_port.read_text().strip()
                    app_pid = app_pid.read_text().strip()
                    self.rag_service_url = f"http://localhost:{app_port}"
                    logger.info(
                        f"✅ Local RAG service discovered at {self.rag_service_url}"
                    )
                    self.state.update_service_state(
                        "search",
                        status=RunStatus.RUNNING,
                        started_at=datetime.now().isoformat(),
                        port=app_port,
                        pid=app_pid,
                    )
                    return True
                time.sleep(1)

            logger.error("❌ Local RAG service failed to start within timeout")
            self.state.update_service_state(
                "search", status=RunStatus.FAILED, error="Service startup timeout"
            )
            return False

        except Exception as e:
            logger.error(f"❌ Local RAG setup failed: {e}")
            self.state.update_service_state(
                "search", status=RunStatus.FAILED, error=str(e)
            )
            return False

    def health_check_ollama(self) -> bool:
        """Health check for Ollama service."""
        # TODO: Implement comprehensive health check
        logger.debug("🔍 Performing Ollama health check...")
        return True

    def health_check_local_rag(self) -> bool:
        """Health check for Local RAG service."""
        # TODO: Implement comprehensive health check
        logger.debug("🔍 Performing Local RAG health check...")
        return True

    def spawn_services(self) -> bool:
        """Spawn all enabled services in dependency order."""
        logger.info("🚀 Starting service spawning process...")

        # Determine service dependencies
        services_to_spawn = []
        if self.enable_chat:
            services_to_spawn.append(("chat", self.spawn_ollama))
        if self.enable_search:
            services_to_spawn.append(("search", self.spawn_local_rag))

        if not services_to_spawn:
            logger.info("ℹ️  No services enabled - skipping service spawning")
            return True

        # Spawn services in order
        for service_name, spawn_func in services_to_spawn:
            logger.info(f"🔄 Spawning {service_name}...")

            if not spawn_func():
                logger.error(f"❌ Failed to spawn {service_name}")
                self.state.update_router_state(status="stopped")
                return False

            logger.info(f"✅ {service_name} spawned successfully")

        # Perform health checks
        logger.info("🔍 Performing health checks...")
        health_checks = []

        if self.enable_chat:
            health_checks.append(("chat", self.health_check_ollama))
        if self.enable_search:
            health_checks.append(("search", self.health_check_local_rag))

        for service_name, health_check_func in health_checks:
            if not health_check_func():
                logger.error(f"❌ Health check failed for {service_name}")
                self.state.update_router_state(status=RunStatus.FAILED)
                return False

        logger.info("✅ All services spawned and healthy")

        # Save discovered URLs to state and update .env
        self._save_service_urls()

        return True

    def cleanup_services(self) -> None:
        """Cleanup services on shutdown."""
        logger.info("🧹 Cleaning up services...")

        # Update router state
        self.state.update_router_state(status=RunStatus.STOPPED)

        # Update service states
        for service_name in self.state.services.keys():
            self.state.update_service_state(service_name, status=RunStatus.STOPPED)

        logger.info("✅ Cleanup completed")

    def _save_service_urls(self) -> None:
        """Save discovered service URLs to state and update .env file."""
        logger.info("💾 Saving discovered service URLs...")

        # Update state with discovered URLs
        if self.ollama_base_url:
            self.state.update_service_state("chat", url=self.ollama_base_url)

        if self.rag_service_url:
            self.state.update_service_state("search", url=self.rag_service_url)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Spawn services for Syft LLM Router")
    parser.add_argument("--project-name", required=True, help="Name of the project")
    parser.add_argument("--config-path", required=True, help="Path to syftbox config")
    parser.add_argument(
        "--cleanup", action="store_true", help="Cleanup services and exit"
    )

    args = parser.parse_args()

    try:
        manager = ServiceManager(args.project_name, args.config_path)

        if args.cleanup:
            manager.cleanup_services()
            return 0

        # Spawn services
        if manager.spawn_services():
            logger.info("🎉 All services ready - router can start")
            return 0
        else:
            logger.error("💥 Service spawning failed - router should not start")
            return 1

    except Exception as e:
        logger.error(f"💥 Service spawning error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
