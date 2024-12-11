# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import webbrowser
import threading
from .helper.webserver import WebServer
from .util.identifier import generate_url_identifier

# Configure logging
logging.basicConfig(level=logging.INFO)


class Authenticate:
    """
    Handles authentication by opening a browser and running a local web server
    to capture credential via callback.
    """

    def __init__(self, server_url, credential_provider, redirect_port=5000):
        """
        Initialize the Authenticate instance.

        :param server_url: The base URL for the authentication request.
        :param credential_provider: The credential provider instance.
        :param redirect_port: The port on which the local web server will run.
        """
        self.server_url = server_url
        self.credential_provider = credential_provider
        self.redirect_port = redirect_port
        self.redirect_uri = f"http://localhost:{redirect_port}/callback"
        self.server_ready = threading.Event()

    def browser_authenticate(self):
        """
        Launch the authentication process:
        - Starts a local web server in a separate thread.
        - Opens the authentication URL in the default web browser.
        - Waits for the web server to handle the callback and capture credential.
        """
        try:
            # Create a web server instance
            self.webserver = WebServer(
                credential_provider=self.credential_provider,
                server_url=self.server_url,
                port=self.redirect_port,
            )

            # Start the web server in a separate thread
            server_thread = threading.Thread(target=self.run_server, daemon=True)
            server_thread.start()

            # Wait until the server is ready before proceeding
            self.server_ready.wait()

            # Format the authentication URL
            auth_url = f"{self.server_url}/user/api_credentials?identifier={generate_url_identifier('ftrack-connect')}&redirect_url={self.redirect_uri}"

            # Log the URL being opened
            logging.info(f"Opening browser for authentication: {auth_url}")

            # Open the authentication URL in the browser
            webbrowser.open_new_tab(auth_url)

            # Wait for the server to shut down after successful authentication
            server_thread.join()
        except Exception as e:
            logging.error(f"An error occurred during browser authentication: {e}")

    def run_server(self):
        """
        Start the web server and notify the main thread that it's ready.
        """
        self.server_ready.set()
        self.webserver.run_server()

    def credential_authenticate(self, server_url, api_user, api_key):
        """
        Save captured credential securely using the utility method.

        :param server_url: The server URL captured during authentication.
        :param api_user: The username captured during authentication.
        :param api_key: The API key captured during authentication.
        """
        self.credential_provider.set_credential(server_url, api_user, api_key)
