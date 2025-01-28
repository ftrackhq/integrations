# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import threading
import webbrowser
from typing import TYPE_CHECKING, Optional

from ftrack.library.utility.url.checker import ftrack_server_url_checker

from .util.identifier import generate_url_identifier

if TYPE_CHECKING:
    from .helper.credential import (
        CredentialFactory,
        CredentialInterface,
    )
    from .helper.webserver import WebServerFactory, WebServerInterface

# Configure logging
logging.basicConfig(level=logging.INFO)


class Authenticate:
    """
    Handles authentication by opening a browser and running a local web server
    to capture credential via callback.
    """

    def __init__(
        self,
        server_url: str,
        credential_factory: "CredentialFactory",
        web_server_factory: "WebServerFactory",
        redirect_port: int = 5000,
    ) -> None:
        """
        Initialize the Authenticate instance.

        :param server_url: The base URL for the authentication request.
        :param credential_factory: The credential provider factory instance.
        :param web_server_factory: The web server factory instance.
        :param redirect_port: The port on which the local web server will run.
        """
        try:
            self._server_url: str = ftrack_server_url_checker(server_url)
        except ValueError as e:
            logging.error(f"Invalid server URL: {e}")
            raise
        self._credential_instance: "CredentialInterface" = credential_factory.make()
        self._web_server_factory: "WebServerFactory" = web_server_factory
        self._web_server_instance: Optional["WebServerInterface"] = None
        self._redirect_port: int = redirect_port
        self._redirect_uri: str = f"http://localhost:{redirect_port}/callback"
        self._server_ready: threading.Event = threading.Event()

    @property
    def server_url(self):
        return self._server_url

    @property
    def credential_instance(self):
        return self._credential_instance

    @property
    def web_server_factory(self):
        return self._web_server_factory

    @property
    def web_server_instance(self):
        return self._web_server_instance

    @property
    def redirect_port(self):
        return self._redirect_port

    @property
    def redirect_uri(self):
        return self._redirect_uri

    def authenticate_browser(self) -> None:
        """
        Launch the authentication process:
        - Starts a local web server in a separate thread.
        - Opens the authentication URL in the default web browser.
        - Waits for the web server to handle the callback and capture credential.
        """
        try:
            # Create a web server instance
            self.web_server_factory.credential_instance = self.credential_instance
            self.web_server_factory.server_url = self.server_url
            self.web_server_factory.port = self.redirect_port
            self._web_server_instance = self.web_server_factory.make()

            # Start the web server in a separate thread
            server_thread: threading.Thread = threading.Thread(
                target=self.run_server, daemon=True
            )
            server_thread.start()

            # Wait until the server is ready before proceeding
            self._server_ready.wait()

            # Format the authentication URL
            auth_url: str = f"{self.server_url}/user/api_credentials?identifier={generate_url_identifier('ftrack-connect')}&redirect_url={self.redirect_uri}"

            # Log the URL being opened
            logging.info(f"Opening browser for authentication: {auth_url}")

            # Open the authentication URL in the browser
            webbrowser.open_new_tab(auth_url)

            # Wait for the server to shut down after successful authentication
            server_thread.join()
        except Exception as e:
            logging.error(f"An error occurred during browser authentication: {e}")
            raise

    def run_server(self) -> None:
        """
        Start the web server and notify the main thread that it's ready.
        """
        self._server_ready.set()
        self.web_server_instance.run_server()

    def authenticate_credential(
        self, server_url: str, api_user: str, api_key: str
    ) -> None:
        """
        Save captured credential securely using the utility method.

        :param server_url: The server URL captured during authentication.
        :param api_user: The username captured during authentication.
        :param api_key: The API key captured during authentication.
        """
        self.credential_instance.credential_store(server_url, api_user, api_key)
