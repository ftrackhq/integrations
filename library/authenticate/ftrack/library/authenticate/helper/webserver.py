# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import threading
from abc import ABC, abstractmethod
from typing import Dict, Optional, Type

from flask import Flask, request

from .credential import CredentialInterface

# Configure logging
logging.basicConfig(level=logging.INFO)


class WebServerInterface(ABC):
    """
    Abstract base class for web servers.
    """

    @abstractmethod
    def __init__(
        self,
        credential_instance: "CredentialInterface",
        server_url: str,
        port: int = 5000,
    ) -> None:
        """
        Initialize the web server instance.

        :param credential_instance: Credential instance.
        :param server_url: Server URL.
        :param port: Port for the server.
        """
        pass

    @abstractmethod
    def run_server(self) -> None:
        """
        Start the web server and handle incoming requests.
        """
        pass


class WebServerFactory:
    """Factory class for creating WebServerInterface instances."""

    def __init__(
        self,
        credential_instance: Optional["CredentialInterface"] = None,
        server_url: Optional[str] = None,
        port: int = 5000,
        variant: str = "FlaskWebServer",
    ) -> None:
        self._credential_instance: Optional["CredentialInterface"] = None
        self._server_url: Optional[str] = None
        self._port: int = port
        self._variant: str = variant
        self._available_variant: Dict[str, Type["WebServerInterface"]] = {
            "FlaskWebServer": FlaskWebServer
        }

        self.credential_instance: Optional["CredentialInterface"] = credential_instance
        self.server_url: Optional[str] = server_url

    @property
    def credential_instance(self) -> Optional["CredentialInterface"]:
        return self._credential_instance

    @credential_instance.setter
    def credential_instance(self, value: Optional["CredentialInterface"]) -> None:
        if value is not None and not isinstance(value, CredentialInterface):
            raise ValueError(
                "Credential must be an instance of CredentialInterface or None."
            )
        self._credential_instance = value

    @property
    def server_url(self) -> Optional[str]:
        return self._server_url

    @server_url.setter
    def server_url(self, value: Optional[str]) -> None:
        if not isinstance(value, str) and value is not None:
            raise ValueError("Server URL must be a string or None.")
        self._server_url = value

    @property
    def port(self) -> int:
        return self._port

    @port.setter
    def port(self, value: int) -> None:
        if not isinstance(value, int):
            raise ValueError("Port must be an integer.")
        self._port = value

    @property
    def variant(self) -> str:
        return self._variant

    @variant.setter
    def variant(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("Variant must be a string.")
        self._variant = value

    @property
    def available_variant(self) -> Dict[str, Type["WebServerInterface"]]:
        return self._available_variant

    def make(self) -> "WebServerInterface":
        """
        Create and return a WebServerInterface-based web server instance.

        :return: Instance of a WebServerInterface.
        """
        if not self.credential_instance:
            raise ValueError("Credential instance is required.")
        if not self.server_url:
            raise ValueError("Server URL is required.")
        return self.available_variant[self.variant](
            self.credential_instance, self.server_url, self.port
        )


class FlaskWebServer(WebServerInterface):
    """Simple web server for handling authentication callbacks."""

    def __init__(
        self,
        credential_instance: "CredentialInterface",
        server_url: str,
        port: int = 5000,
    ) -> None:
        self._app: Flask = Flask(__name__)
        self._server_url: str = server_url
        self._port: int = port
        self._credential_instance: "CredentialInterface" = credential_instance
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
                    self._credential_instance.credential_store(
                        self._server_url, api_user, api_key
                    )
                    logging.info("Credential received and saved.")
                    self._stop_flag.set()  # Signal to stop the server
                    return "Authentication successful! You can close this window."
                else:
                    logging.warning("Incomplete credential received.")
                    return "Missing api_user or api_key."
            except Exception as e:
                logging.error(f"Error during callback processing: {e}")
                raise

    def run_server(self) -> None:
        """Run Flask server and wait for stop flag."""
        threading.Thread(target=self._run, daemon=True).start()
        self._stop_flag.wait()  # Wait until the stop flag is set

    def _run(self) -> None:
        """Start the Flask server."""
        self._app.run(port=self._port, debug=False, use_reloader=False)
