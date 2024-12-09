# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import keyring

# Configure logging
logging.basicConfig(level=logging.INFO)


def set_credential(identifier, server_url, api_user, api_key):
    """
    Save credential securely using keyring.

    :param identifier: Unique identifier for the credential (e.g., tool name).
    :param server_url: Server URL.
    :param api_user: User's name.
    :param api_key: API key for authentication.
    """
    try:
        keyring.set_password(identifier, "server_url", server_url)
        keyring.set_password(identifier, "api_user", api_user)
        keyring.set_password(identifier, "api_key", api_key)
        logging.info(f"Credential saved securely for tool: {identifier}.")
    except Exception as e:
        logging.error(f"Failed to save credential: {e}")


def get_credential(identifier):
    """
    Retrieve credential securely from keyring.

    :param identifier: Unique identifier for the credential (e.g., tool name).
    :return: Dictionary containing server_url, api_user and api_key, or None if not found.
    """
    try:
        server_url = keyring.get_password(identifier, "server_url")
        api_user = keyring.get_password(identifier, "api_user")
        api_key = keyring.get_password(identifier, "api_key")
        if server_url and api_user and api_key:
            return {"server_url": server_url, "api_user": api_user, "api_key": api_key}
        else:
            logging.warning(f"No credential found for tool: {identifier}.")
            return None
    except Exception as e:
        logging.error(f"Failed to retrieve credential: {e}")
        return None
