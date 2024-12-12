# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import keyring
from abc import ABC, abstractmethod
from typing import Optional, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)


class CredentialProvider(ABC):
    """
    Abstract base class for credential providers.
    """

    @abstractmethod
    def get_credential(self) -> Optional[Dict[str, str]]:
        """
        Retrieve credentials.

        :return: Dictionary containing server_url, api_user, and api_key, or None if not found.
        """
        pass

    @abstractmethod
    def set_credential(self, server_url: str, api_user: str, api_key: str) -> None:
        """
        Save credentials securely.

        :param server_url: Server URL.
        :param api_user: User's name.
        :param api_key: API key for authentication.
        """
        pass


class CredentialProviderFactory:
    """Factory class for creating credential provider."""

    @property
    def credential_identifier(self) -> Optional[str]:
        return self._credential_identifier

    @credential_identifier.setter
    def credential_identifier(self, value: str) -> None:
        self._credential_identifier = value

    def __init__(self, credential_identifier: Optional[str] = None) -> None:
        self._credential_identifier: Optional[str] = credential_identifier

    def create_credential_provider(self) -> CredentialProvider:
        """
        Create and return a keyring-based credential provider.

        :return: Instance of a CredentialProvider.
        """
        return KeyringCredentialProvider(self.credential_identifier)


class KeyringCredentialProvider(CredentialProvider):
    """
    Credential provider that uses the system keyring to store and retrieve credentials.
    """

    def __init__(self, credential_identifier: Optional[str]) -> None:
        self.credential_identifier: Optional[str] = credential_identifier

    def get_credential(self) -> Optional[Dict[str, str]]:
        """
        Retrieve credentials from the keyring.

        :return: Dictionary containing server_url, api_user, and api_key, or None if not found.
        """
        try:
            server_url: Optional[str] = keyring.get_password(
                self.credential_identifier, "server_url"
            )
            api_user: Optional[str] = keyring.get_password(
                self.credential_identifier, "api_user"
            )
            api_key: Optional[str] = keyring.get_password(
                self.credential_identifier, "api_key"
            )

            if server_url and api_user and api_key:
                return {
                    "server_url": server_url,
                    "api_user": api_user,
                    "api_key": api_key,
                }

            logging.warning(
                f"No credential found for identifier: {self.credential_identifier}."
            )
            return None
        except Exception as e:
            logging.error(f"Failed to retrieve credential: {e}")
            return None

    def set_credential(self, server_url: str, api_user: str, api_key: str) -> None:
        """
        Save credentials securely using the system keyring.

        :param server_url: Server URL.
        :param api_user: User's name.
        :param api_key: API key for authentication.
        """
        try:
            keyring.set_password(self.credential_identifier, "server_url", server_url)
            keyring.set_password(self.credential_identifier, "api_user", api_user)
            keyring.set_password(self.credential_identifier, "api_key", api_key)
            logging.info(
                f"Credentials saved for identifier: {self.credential_identifier}."
            )
        except Exception as e:
            logging.error(f"Failed to save credential: {e}")
