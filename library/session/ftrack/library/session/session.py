# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
from .utility.session import create_api_session

logging.basicConfig(level=logging.INFO)


class SessionProvider:
    """
    High-level session provider that uses external utilities and handles credential lookup.
    """

    def __init__(self, credential_provider):
        """
        Initialize the session provider with a credential provider.

        :param credential_provider: Credential provider instance.
        """
        self.credential_provider = credential_provider
        self._session = None

    @property
    def session(self):
        """Lazily initialize and return the API session."""
        if not self._session:
            self._session = self.load_session()
        return self._session

    def load_session(self, auto_connect_event_hub=True):
        """Load a session using stored credentials."""
        try:
            # Retrieve credential securely using the external library
            credential = self.credential_provider.get_credential()
            if credential:
                server_url = credential["server_url"]
                api_key = credential["api_key"]
                api_user = credential["api_user"]
                return create_api_session(
                    server_url, api_key, api_user, auto_connect_event_hub
                )
            else:
                logging.warning("No credentials found. Please authenticate first.")
                return None
        except KeyError as e:
            logging.error(f"Malformed credential data: Missing {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
        return None
