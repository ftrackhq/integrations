# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import keyring

# Configure logging
logging.basicConfig(level=logging.INFO)


class CredentialProvider:
    def __init__(self, credential_identifier):
        self.credential_identifier = credential_identifier

    def get_credential(self):
        """
        Retrieve credentials from keyring.

        :return: Dictionary containing server_url, api_user and api_key, or None if not found.
        """
        try:
            server_url = keyring.get_password(self.credential_identifier, "server_url")
            api_user = keyring.get_password(self.credential_identifier, "api_user")
            api_key = keyring.get_password(self.credential_identifier, "api_key")
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

    def set_credential(self, server_url, api_user, api_key):
        """
        Save credential securely using keyring.

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
