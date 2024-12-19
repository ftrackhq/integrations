# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
from typing import TYPE_CHECKING, Optional

from .utility.session import create_api_session

if TYPE_CHECKING:
    from ftrack.library.authenticate.helper.credential import (
        CredentialFactory,
        CredentialInterface,
    )
    from ftrack_api import Session


logging.basicConfig(level=logging.INFO)


class SessionProvider:
    """
    High-level session provider that uses external utilities and handles credential lookup.
    """

    def __init__(self, credential_factory: "CredentialFactory") -> None:
        """
        Initialize the session provider with a credential provider.

        :param credential_factory: Credential factory instance.
        """
        self._credential_instance: "CredentialInterface" = credential_factory.make()
        self._session: Optional["Session"] = None

    @property
    def credential_instance(self) -> "CredentialInterface":
        return self._credential_instance

    @property
    def session(self) -> Optional["Session"]:
        """Lazily initialize and return the API session."""
        if not self._session:
            self._session = self.new_session_from_stored_credentials()
        return self._session

    def new_session_from_stored_credentials(
        self, spawn_event_hub_thread: bool = True
    ) -> Optional["Session"]:
        """
        Load a session using stored credentials.

        :param spawn_event_hub_thread: Whether to automatically connect to the event hub.
        :return: An API session or None if credentials are missing or invalid.
        """
        try:
            # Retrieve credential securely using the external library
            credential: Optional[dict] = self.credential_instance.credential_load()
            if credential:
                server_url = credential["server_url"]
                api_key = credential["api_key"]
                api_user = credential["api_user"]
                return create_api_session(
                    server_url, api_key, api_user, spawn_event_hub_thread
                )
            else:
                logging.warning("No credentials found. Please authenticate first.")
                return None
        except KeyError as e:
            logging.error(f"Malformed credential data: Missing {e}")
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            raise
        return None
