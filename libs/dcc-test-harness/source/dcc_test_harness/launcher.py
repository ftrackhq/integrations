"""DCC process launcher.

Provides the abstract ``Launcher`` base class for starting a DCC
application with the test server injected. DCC-specific launchers
(e.g. MayaLauncher, NukeLauncher) should be implemented in the
integration project.
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class LaunchConfig:
    """Configuration for launching a DCC application."""

    server_port: int = 0
    """Port for the RPC server. 0 means OS picks a free port."""

    dcc_executable: Optional[str] = None
    """Path to the DCC binary. Auto-detected by the launcher if None."""

    extra_env: dict[str, str] = field(default_factory=dict)
    """Additional environment variables to set for the DCC."""

    startup_timeout: float = 60.0
    """Maximum seconds to wait for the DCC and server to be ready."""

    harness_package_path: Optional[str] = None
    """Path to the directory containing the dcc_test_harness package.
    Auto-detected if None (uses the parent of this package's location)."""


@dataclass
class DCCProcess:
    """A running DCC process with the test server active."""

    process: subprocess.Popen
    port: int
    host: str = "127.0.0.1"

    def is_alive(self) -> bool:
        """Check if the DCC process is still running."""
        return self.process.poll() is None

    def terminate(self, timeout: float = 10.0) -> None:
        """Kill the DCC process via SIGKILL.

        Never sends SIGTERM — it crashes Qt mid-paint on macOS.
        Clean shutdown should already have been requested via the
        server's ``quit_fn`` before this is called.
        """
        if not self.is_alive():
            return

        logger.warning(
            "DCC process still alive, sending SIGKILL (pid=%d)",
            self.process.pid,
        )
        self.process.kill()
        try:
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            logger.error(
                "DCC process did not exit after SIGKILL within %ss "
                "(pid=%d)",
                timeout,
                self.process.pid,
            )


class Launcher(ABC):
    """Base class for DCC launchers.

    Subclass to implement launching for a specific DCC application.
    The launcher is responsible for:

    1. Finding/configuring the DCC executable
    2. Setting up PYTHONPATH so the DCC can import dcc_test_harness
    3. Injecting the server startup command
    4. Waiting for the server to be ready
    5. Returning a DCCProcess with the connection info

    Example implementation for Maya::

        class MayaLauncher(Launcher):
            def launch(self, config):
                maya_exe = config.dcc_executable or self._find_maya()
                port_file = tempfile.mktemp(suffix=".port")
                env = self._build_env(config)
                startup = self._build_server_startup_code(
                    port_file, config.server_port,
                    quit_fn="lambda: maya.cmds.quit(force=True)",
                )
                process = subprocess.Popen(
                    [maya_exe, "-command", f'python("{startup}")'],
                    env=env,
                )
                port = self._wait_for_port_file(
                    port_file, config.startup_timeout, process
                )
                return DCCProcess(process=process, port=port)
    """

    @abstractmethod
    def launch(self, config: LaunchConfig) -> DCCProcess:
        """Start the DCC with the test server running.

        Returns when the server is ready to accept connections.
        """
        ...

    def _find_harness_package_path(self, config: LaunchConfig) -> str:
        """Resolve the path to the directory containing dcc_test_harness."""
        if config.harness_package_path:
            return config.harness_package_path
        return str(Path(__file__).parent.parent)

    def _build_env(self, config: LaunchConfig) -> dict[str, str]:
        """Build the environment dict with PYTHONPATH set."""
        env = os.environ.copy()
        env.update(config.extra_env)
        src_path = self._find_harness_package_path(config)
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            src_path + os.pathsep + existing if existing else src_path
        )
        return env

    def _build_server_startup_code(
        self,
        port_file: str,
        port: int,
        quit_fn: Optional[str] = None,
    ) -> str:
        """Generate the Python code the DCC runs at startup.

        Args:
            port_file: Path where the server writes its port.
            port: Port to bind (0 for auto).
            quit_fn: Optional Python expression for the quit callback,
                e.g. ``"lambda: maya.cmds.quit(force=True)"``.
                If None, the server won't quit the DCC on shutdown.
        """
        quit_arg = f", quit_fn={quit_fn}" if quit_fn else ""
        return (
            f"from dcc_test_harness.server import start; "
            f"start(port={port}, port_file={port_file!r}"
            f"{quit_arg})"
        )

    def _wait_for_port_file(
        self,
        port_file: str,
        timeout: float,
        process: subprocess.Popen,
    ) -> int:
        """Poll for the port file to appear and read the port number."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(
                    f"DCC process exited with code "
                    f"{process.returncode} before server started"
                )
            if os.path.exists(port_file):
                try:
                    with open(port_file) as f:
                        content = f.read().strip()
                    if content:
                        return int(content)
                except (ValueError, IOError):
                    pass
            time.sleep(0.5)

        raise TimeoutError(
            f"DCC test server did not start within {timeout}s. "
            f"Port file not found: {port_file}"
        )
