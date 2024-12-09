# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
from .util.credential import get_credential
from .util.session import create_api_session

# Configure logging
logging.basicConfig(level=logging.INFO)

# TODO: should we separate session and the event hub thread into another library?


class SessionProvider:
    @property
    def session(self):
        return self._session or self.load_session()

    def __init__(self, credential_identifier):
        self.credential_identifier = credential_identifier
        self._session = None

    def load_session(self):
        """Load session using stored credential."""
        try:
            # Retrieve credential securely
            credential = get_credential(self.credential_identifier)
            if credential:
                api_user = credential["api_user"]
                api_key = credential["api_key"]
                server_url = credential["server_url"]
                self._session = create_api_session(server_url, api_user, api_key)
                logging.info(f"Session loaded for user: {api_user}")
                return self._session
            else:
                logging.warning("No credential found. Please authenticate first.")
                return None
        except KeyError as e:
            logging.error(f"Malformed credential data: Missing {e}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None
