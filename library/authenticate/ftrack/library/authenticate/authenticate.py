# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import webbrowser
import threading
from typing import TYPE_CHECKING, Optional
from .util.identifier import generate_url_identifier
from ftrack.library.utility.url.checker import (
    url_checker,
    ftrack_server_url_checker,
)

if TYPE_CHECKING:
    from .helper.credential import (
        CredentialProviderFactory,
        CredentialProvider,
    )
    from .helper.webserver import WebServerFactory, WebServer

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
        credential_provider_factory: "CredentialProviderFactory",
        web_server_factory: "WebServerFactory",
        redirect_port: int = 5000,
    ) -> None:
        """
        Initialize the Authenticate instance.

        :param server_url: The base URL for the authentication request.
        :param credential_provider_factory: The credential provider factory instance.
        :param web_server_factory: The web server factory instance.
        :param redirect_port: The port on which the local web server will run.
        """
        try:
            self._server_url: str = url_checker(
                server_url, [ftrack_server_url_checker]
            )
        except ValueError as e:
            logging.error(f"Invalid server URL: {e}")
            raise
        self._credential_provider_instance: "CredentialProvider" = (
            credential_provider_factory.create_credential_provider()
        )
        self._web_server_factory: "WebServerFactory" = web_server_factory
        self._web_server_instance: Optional["WebServer"] = None
        self._redirect_port: int = redirect_port
        self._redirect_uri: str = f"http://localhost:{redirect_port}/callback"
        self._server_ready: threading.Event = threading.Event()

    @property
    def server_url(self):
        return self._server_url

    @property
    def credential_provider_instance(self):
        return self._credential_provider_instance

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

    def browser_authenticate(self) -> None:
        """
        Launch the authentication process:
        - Starts a local web server in a separate thread.
        - Opens the authentication URL in the default web browser.
        - Waits for the web server to handle the callback and capture credential.
        """
        try:
            # Create a web server instance
            self.web_server_factory.credential_provider = (
                self.credential_provider_instance
            )
            self.web_server_factory.server_url = self.server_url
            self._web_server_instance = (
                self.web_server_factory.create_web_server(
                    port=self.redirect_port,
                )
            )

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
            logging.error(
                f"An error occurred during browser authentication: {e}"
            )

    def run_server(self) -> None:
        """
        Start the web server and notify the main thread that it's ready.
        """
        self._server_ready.set()
        self.web_server_instance.run_server()

    def credential_authenticate(
        self, server_url: str, api_user: str, api_key: str
    ) -> None:
        """
        Save captured credential securely using the utility method.

        :param server_url: The server URL captured during authentication.
        :param api_user: The username captured during authentication.
        :param api_key: The API key captured during authentication.
        """
        self.credential_provider_instance.set_credential(
            server_url, api_user, api_key
        )
