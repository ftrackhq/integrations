# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
from typing import Optional, TYPE_CHECKING
from .utility.session import create_api_session

if TYPE_CHECKING:
    from ftrack.library.authenticate.helper.credential import (
        CredentialProviderFactory,
        CredentialProvider,
    )
    from ftrack_api import Session


logging.basicConfig(level=logging.INFO)


class SessionProvider:
    """
    High-level session provider that uses external utilities and handles credential lookup.
    """

    def __init__(
        self, credential_provider_factory: "CredentialProviderFactory"
    ) -> None:
        """
        Initialize the session provider with a credential provider.

        :param credential_provider_factory: Credential provider factory instance.
        """
        self._credential_provider_instance: "CredentialProvider" = (
            credential_provider_factory.create_credential_provider()
        )
        self._session: Optional["Session"] = None

    @property
    def credential_provider_instance(self) -> "CredentialProvider":
        return self._credential_provider_instance

    @property
    def session(self) -> Optional["Session"]:
        """Lazily initialize and return the API session."""
        if not self._session:
            self._session = self.load_session()
        return self._session

    def load_session(
        self, auto_connect_event_hub: bool = True
    ) -> Optional["Session"]:
        """
        Load a session using stored credentials.

        :param auto_connect_event_hub: Whether to automatically connect to the event hub.
        :return: An API session or None if credentials are missing or invalid.
        """
        try:
            # Retrieve credential securely using the external library
            credential: Optional[
                dict
            ] = self.credential_provider_instance.get_credential()
            if credential:
                server_url: str = credential["server_url"]
                api_key: str = credential["api_key"]
                api_user: str = credential["api_user"]
                return create_api_session(
                    server_url, api_key, api_user, auto_connect_event_hub
                )
            else:
                logging.warning(
                    "No credentials found. Please authenticate first."
                )
                return None
        except KeyError as e:
            logging.error(f"Malformed credential data: Missing {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
        return None
