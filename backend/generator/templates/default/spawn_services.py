#!/usr/bin/env python3
"""
Default Service Spawner for Syft LLM Router
Handles spawning and monitoring of Ollama and Local RAG services.
"""

import argparse
import logging
import shutil
import subprocess
import sys
import time
from datetime import datetime

import requests
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


class ServiceManager:
    """Manages service spawning, monitoring, and state tracking."""

    def __init__(self, project_name: str, config_path: str):
        client = Client.load(config_path)

        # metadata path
        metadata_path = (
            client.my_datasite / "public" / "routers" / project_name / "metadata.json"
        )

        # load config
        self.config = load_config(
            syft_config_path=client.config.path,
            metadata_path=metadata_path,
        )

        # Service configuration from .env
        self.enable_chat = self.config.enable_chat
        self.enable_search = self.config.enable_search

        # URLs will be discovered dynamically when services are spawned
        self.ollama_base_url = None
        self.rag_service_url = None

        # Update state
        self._initialize_state()

        logger.info(f"Service Manager initialized for {project_name}")
        logger.info(f"Chat enabled: {self.enable_chat}")
        logger.info(f"Search enabled: {self.enable_search}")

    def _initialize_state(self) -> None:
        """Update state."""

        # Initialize service states based on enabled services
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
                self.config.state.update_service_state(
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
                    self.config.state.update_service_state(
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
                        self.config.state.update_service_state(
                            "chat",
                            status=RunStatus.RUNNING,
                            started_at=datetime.now().isoformat(),
                        )
                        return True
                except Exception:
                    continue

            logger.error("❌ Ollama service not found on any expected URL")
            self.config.state.update_service_state(
                "chat", status=RunStatus.FAILED, error="Service not found"
            )
            return False

        except subprocess.TimeoutExpired:
            logger.error("❌ Ollama setup timed out")
            self.config.state.update_service_state(
                "chat", status=RunStatus.FAILED, error="Setup timeout"
            )
            return False
        except Exception as e:
            logger.error(f"❌ Ollama setup failed: {e}")
            self.config.state.update_service_state(
                "chat", status=RunStatus.FAILED, error=str(e)
            )
            return False

    def _install_app_on_syftbox(self, repo_url: str, app_name: str) -> bool:
        """Install an app on syftbox."""
        logger.info(f"🔍 Installing {repo_url} on syftbox...")

        using_syftbox_cli = True

        try:
            client = Client.load(self.config.syft_config.path)

            # Check if syftbox cli is available
            if shutil.which("syftbox") is None:
                logger.error("❌ syftbox cli not found. Defaulting to SyftUI Client.")
                using_syftbox_cli = False

                # Check if syftbox client is available
                response = requests.get(
                    f"{client.config.client_url}/v1/apps",
                    headers={"Authorization": f"Bearer {client.config.client_token}"},
                    timeout=10,
                )

                # If syftbox client is not available, return False
                if response.status_code != 200:
                    logger.error("❌ syftbox client not found")
                    self.config.state.update_service_state(
                        "search", status="failed", error="syftbox client not found"
                    )
                    return False

                logger.info("✅ syftbox client found")
            else:
                logger.info("✅ syftbox cli found")

            # If syftbox cli present, the use syftbox cli to check and install app
            if using_syftbox_cli:
                result = subprocess.run(
                    ["syftbox", "app", "list", "-c", self.config.syft_config.path],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if app_name in result.stdout:
                    logger.info(f"✅ {app_name} already installed")
                    return True

                # Install app using syftbox cli
                install_result = subprocess.run(
                    [
                        "syftbox",
                        "app",
                        "install",
                        repo_url,
                        "--config",
                        self.config.syft_config.path,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minutes timeout for installation
                )

                # If app is not installed, install it using syftbox cli
                if install_result.returncode != 0:
                    logger.error(
                        f"❌ Failed to install {repo_url}: {install_result.stderr}"
                    )
                    self.config.state.update_service_state(
                        "search", status="failed", error="Installation failed"
                    )
                    return False

            # If syftbox client is not available, use syftbox client to check and install app
            else:
                # List available apps
                response = requests.get(
                    f"{client.config.client_url}/v1/apps",
                    headers={"Authorization": f"Bearer {client.config.client_token}"},
                    timeout=10,
                )

                if response.status_code != 200:
                    logger.error(f"❌ Failed to list apps: {response.text}")
                    self.config.state.update_service_state(
                        "search", status="failed", error="Failed to list apps"
                    )
                    return False

                # Check if app is already installed
                apps_list = response.json().get("apps", [])
                for app in apps_list:
                    if app["name"] == app_name:
                        logger.info(f"✅ {app_name} already installed")
                        return True

                # Install app using syftbox client
                install_result = requests.post(
                    f"{client.config.client_url}/v1/apps/",
                    headers={"Authorization": f"Bearer {client.config.client_token}"},
                    json={
                        "repoURL": repo_url,
                        "branch": "main",
                        "force": False,
                    },
                    timeout=300,
                )

                if install_result.status_code != 200:
                    logger.error(
                        f"❌ Failed to install {repo_url}: {install_result.text}: {install_result.status_code}"
                    )
                    self.config.state.update_service_state(
                        "search", status="failed", error="Failed to install app"
                    )
                    return False

            logger.info(f"✅ {app_name} installed successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to install {repo_url}:{app_name}: {e}")
            self.config.state.update_service_state(
                "search", status="failed", error=f"Failed to install {repo_url}: {e}"
            )
            return False

    def spawn_local_rag(self) -> bool:
        """Spawn and verify Local RAG service."""
        logger.info("🔍 Setting up Local RAG service...")

        try:
            if not self._install_app_on_syftbox(
                "https://github.com/OpenMined/local-rag",
                "com.github.openmined.local-rag",
            ):
                logger.error("❌ Failed to install local-rag")
                return False
            else:
                logger.info("✅ local-rag installed successfully")

            # Set router context for local-rag
            client = Client.load(self.config.syft_config.path)
            app_folder = (
                client.workspace.data_dir / "apps" / "com.github.openmined.local-rag"
            )
            
            # Create router context file
            # router_context_file = app_folder / ".env.router"
            # router_context_file.write_text(f"CURRENT_ROUTER_ID={self.config.project.name}\n")
            # logger.info(f"✅ Set router context: {self.config.project.name}")

            # Wait for local-rag to be ready and discover its URL
            logger.info("⏳ Waiting for local-rag to be ready...")

            # Check if app.pid and app.port are set
            client = Client.load(self.config.syft_config.path)
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
                    self.config.state.update_service_state(
                        "search",
                        status=RunStatus.RUNNING,
                        started_at=datetime.now().isoformat(),
                        port=app_port,
                        pid=app_pid,
                    )
                    return True
                time.sleep(1)

            logger.error("❌ Local RAG service failed to start within timeout")
            self.config.state.update_service_state(
                "search", status=RunStatus.FAILED, error="Service startup timeout"
            )
            return False

        except Exception as e:
            logger.error(f"❌ Local RAG setup failed: {e}")
            self.config.state.update_service_state(
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
                self.config.state.update_router_state(status="stopped")
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
                self.config.state.update_router_state(status=RunStatus.FAILED)
                return False

        logger.info("✅ All services spawned and healthy")

        # Save discovered URLs to state and update .env
        self._save_service_urls()

        return True

    def cleanup_services(self) -> None:
        """Cleanup services on shutdown."""
        logger.info("🧹 Cleaning up services...")

        # Update router state
        self.config.state.update_router_state(status=RunStatus.STOPPED)

        # Update service states
        for service_name in self.config.state.services.keys():
            self.config.state.update_service_state(
                service_name, status=RunStatus.STOPPED
            )

        logger.info("✅ Cleanup completed")

    def _save_service_urls(self) -> None:
        """Save discovered service URLs to state and update .env file."""
        logger.info("💾 Saving discovered service URLs...")

        # Update state with discovered URLs
        if self.ollama_base_url:
            self.config.state.update_service_state("chat", url=self.ollama_base_url)

        if self.rag_service_url:
            self.config.state.update_service_state("search", url=self.rag_service_url)


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
