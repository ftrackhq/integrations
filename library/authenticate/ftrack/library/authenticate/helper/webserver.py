# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import threading
import logging
from flask import Flask, request
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .credential import CredentialProvider

# Configure logging
logging.basicConfig(level=logging.INFO)


class WebServer(ABC):
    """
    Abstract base class for web servers.
    """

    @abstractmethod
    def run_server(self) -> None:
        """
        Start the web server and handle incoming requests.
        """
        pass


class WebServerFactory:
    """Factory class for creating WebServer instances."""

    @property
    def credential_provider(self) -> Optional["CredentialProvider"]:
        return self._credential_provider

    @credential_provider.setter
    def credential_provider(self, value: "CredentialProvider") -> None:
        self._credential_provider = value

    @property
    def server_url(self) -> Optional[str]:
        return self._server_url

    @server_url.setter
    def server_url(self, value: str) -> None:
        self._server_url = value

    def __init__(
        self,
        credential_provider: Optional["CredentialProvider"] = None,
        server_url: Optional[str] = None,
    ) -> None:
        self._credential_provider: Optional["CredentialProvider"] = credential_provider
        self._server_url: Optional[str] = server_url

    def create_web_server(self, port: int = 5000) -> WebServer:
        return FlaskWebServer(self.credential_provider, self.server_url, port)


class FlaskWebServer(WebServer):
    """Simple web server for handling authentication callbacks."""

    def __init__(
        self,
        credential_provider: "CredentialProvider",
        server_url: Optional[str],
        port: int = 5000,
    ) -> None:
        self.app: Flask = Flask(__name__)
        self.server_url: Optional[str] = server_url
        self.port: int = port
        self.credential_provider: "CredentialProvider" = credential_provider
        self.stop_flag: threading.Event = threading.Event()

        @self.app.route("/callback")
        def callback() -> str:
            """
            Handle authentication callback, save credential, and shut down the server.
            """
            try:
                api_user: Optional[str] = request.args.get("api_user")
                api_key: Optional[str] = request.args.get("api_key")
                if api_user and api_key:
                    self.credential_provider.set_credential(
                        self.server_url, api_user, api_key
                    )
                    logging.info("Credential received and saved.")
                    self.stop_flag.set()  # Signal to stop the server
                    return "Authentication successful! You can close this window."
                else:
                    logging.warning("Incomplete credential received.")
                    return "Missing api_user or api_key."
            except Exception as e:
                logging.error(f"Error during callback processing: {e}")
                return "An error occurred during authentication."

    def run_server(self) -> None:
        """Run Flask server and wait for stop flag."""
        threading.Thread(target=self._run, daemon=True).start()
        self.stop_flag.wait()  # Wait until the stop flag is set

    def _run(self) -> None:
        """Start the Flask server."""
        self.app.run(port=self.port, debug=False, use_reloader=False)
