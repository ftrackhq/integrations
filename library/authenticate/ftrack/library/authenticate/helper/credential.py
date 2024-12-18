# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import keyring
from abc import ABC, abstractmethod
from typing import Optional, Dict, Type

# Configure logging
logging.basicConfig(level=logging.INFO)


class CredentialInterface(ABC):
    """
    Abstract base class for credential.
    """

    @abstractmethod
    def __init__(self, credential_identifier: str) -> None:
        """
        Initialize the credential with a credential identifier.

        :param credential_identifier: Unique identifier for credentials.
        """
        pass

    @abstractmethod
    def credential_load(self) -> Optional[Dict[str, str]]:
        """
        Retrieve credentials.

        :return: Dictionary containing server_url, api_user, and api_key, or None if not found.
        """
        pass

    @abstractmethod
    def credential_store(
        self, server_url: str, api_user: str, api_key: str
    ) -> None:
        """
        Save credentials securely.

        :param server_url: Server URL.
        :param api_user: User's name.
        :param api_key: API key for authentication.
        """
        pass


class CredentialFactory:
    """Factory class for creating credential."""

    def __init__(
        self,
        credential_identifier: Optional[str] = None,
        variant: str = "keyring",
    ) -> None:
        self._credential_identifier: Optional[str] = None
        self._variant: str = variant
        self._available_variant: Dict[str, Type["CredentialInterface"]] = {
            'keyring': KeyringCredential
        }
        self.credential_identifier: Optional[str] = credential_identifier

    @property
    def credential_identifier(self) -> Optional[str]:
        return self._credential_identifier

    @credential_identifier.setter
    def credential_identifier(self, value: Optional[str]) -> None:
        if not isinstance(value, str) and value is not None:
            raise ValueError("Credential identifier must be a string or None.")
        self._credential_identifier = value

    @property
    def variant(self) -> str:
        return self._variant

    @variant.setter
    def variant(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("Variant must be a string.")
        self._variant = value

    @property
    def available_variant(self) -> Dict[str, Type["CredentialInterface"]]:
        return self._available_variant

    def make(self) -> "CredentialInterface":
        """
        Create and return a CredentialInterface-based credential.

        :return: Instance of a CredentialInterface.
        """
        if not self.credential_identifier:
            raise ValueError("Credential identifier is required.")
        return self.available_variant[self.variant](self.credential_identifier)


class KeyringCredential(CredentialInterface):
    """
    Credential that uses the system keyring to store and retrieve credentials.
    """

    def __init__(self, credential_identifier: str) -> None:
        self._credential_identifier: str = credential_identifier

    @property
    def credential_identifier(self) -> str:
        return self._credential_identifier

    def credential_load(self) -> Optional[Dict[str, str]]:
        """
        Retrieve credentials from the keyring.

        :return: Dictionary containing server_url, api_user, and api_key, or None if not found.
        """
        try:
            server_url = keyring.get_password(
                self.credential_identifier, "server_url"
            )
            api_user = keyring.get_password(
                self.credential_identifier, "api_user"
            )
            api_key = keyring.get_password(
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
            raise

    def credential_store(
        self, server_url: str, api_user: str, api_key: str
    ) -> None:
        """
        Save credentials securely using the system keyring.

        :param server_url: Server URL.
        :param api_user: User's name.
        :param api_key: API key for authentication.
        """
        try:
            keyring.set_password(
                self.credential_identifier, "server_url", server_url
            )
            keyring.set_password(
                self.credential_identifier, "api_user", api_user
            )
            keyring.set_password(
                self.credential_identifier, "api_key", api_key
            )
            logging.info(
                f"Credentials saved for identifier: {self.credential_identifier}."
            )
        except Exception as e:
            logging.error(f"Failed to save credential: {e}")
            raise
