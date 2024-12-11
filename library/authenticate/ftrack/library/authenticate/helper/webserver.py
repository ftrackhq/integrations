# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import threading
import logging
from flask import Flask, request

# Configure logging
logging.basicConfig(level=logging.INFO)


class WebServer:
    """Simple web server for handling authentication callbacks."""

    def __init__(self, credential_provider, server_url, port=5000):
        self.app = Flask(__name__)
        self.server_url = server_url
        self.port = port
        self.credential_provider = credential_provider
        self.stop_flag = threading.Event()

        @self.app.route("/callback")
        def callback():
            """
            Handle authentication callback, save credential, and shut down the server.
            """
            try:
                api_user = request.args.get("api_user")
                api_key = request.args.get("api_key")
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

    def run_server(self):
        """Run Flask server and wait for stop flag."""
        threading.Thread(target=self._run, daemon=True).start()
        self.stop_flag.wait()  # Wait until the stop flag is set

    def _run(self):
        """Start the Flask server."""
        self.app.run(port=self.port, debug=False, use_reloader=False)
