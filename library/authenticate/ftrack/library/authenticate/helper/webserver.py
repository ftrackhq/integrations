# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import threading
import logging
from flask import Flask, request
from abc import ABC, abstractmethod
from typing import Optional
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

    def __init__(
        self,
        credential_provider: Optional[CredentialProvider] = None,
        server_url: Optional[str] = None,
    ) -> None:
        self._credential_provider: Optional[CredentialProvider] = None
        self._server_url: Optional[str] = None

        self.credential_provider: Optional[
            CredentialProvider
        ] = credential_provider
        self.server_url: Optional[str] = server_url

    @property
    def credential_provider(self) -> Optional[CredentialProvider]:
        return self._credential_provider

    @credential_provider.setter
    def credential_provider(self, value: Optional[CredentialProvider]) -> None:
        if value is not None and not isinstance(value, CredentialProvider):
            raise ValueError(
                "Credential provider must be an instance of CredentialProvider or None."
            )
        self._credential_provider = value

    @property
    def server_url(self) -> Optional[str]:
        return self._server_url

    @server_url.setter
    def server_url(self, value: Optional[str]) -> None:
        if not isinstance(value, str) and value is not None:
            raise ValueError("Server URL must be a string or None.")
        self._server_url = value

    def create_web_server(self, port: int = 5000) -> WebServer:
        if not self.credential_provider:
            raise ValueError("Credential provider is required.")
        if not self.server_url:
            raise ValueError("Server URL is required.")
        return FlaskWebServer(self.credential_provider, self.server_url, port)


class FlaskWebServer(WebServer):
    """Simple web server for handling authentication callbacks."""

    def __init__(
        self,
        credential_provider: CredentialProvider,
        server_url: str,
        port: int = 5000,
    ) -> None:
        self._app: Flask = Flask(__name__)
        self._server_url: str = server_url
        self._port: int = port
        self._credential_provider: CredentialProvider = credential_provider
        self._stop_flag: threading.Event = threading.Event()

        @self._app.route("/callback")
        def callback() -> str:
            """
            Handle authentication callback, save credential, and shut down the server.
            """
            try:
                api_user: Optional[str] = request.args.get("api_user")
                api_key: Optional[str] = request.args.get("api_key")
                if api_user and api_key:
                    self._credential_provider.set_credential(
                        self._server_url, api_user, api_key
                    )
                    logging.info("Credential received and saved.")
                    self._stop_flag.set()  # Signal to stop the server
                    return (
                        "Authentication successful! You can close this window."
                    )
                else:
                    logging.warning("Incomplete credential received.")
                    return "Missing api_user or api_key."
            except Exception as e:
                logging.error(f"Error during callback processing: {e}")
                return "An error occurred during authentication."

    def run_server(self) -> None:
        """Run Flask server and wait for stop flag."""
        threading.Thread(target=self._run, daemon=True).start()
        self._stop_flag.wait()  # Wait until the stop flag is set

    def _run(self) -> None:
        """Start the Flask server."""
        self._app.run(port=self._port, debug=False, use_reloader=False)
