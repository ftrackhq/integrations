# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import logging
import getpass
import socket
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)


def generate_url_identifier(tool_name: str) -> Optional[str]:
    """
    Generate a unique identifier.

    :param tool_name: Tool or application name.
    :return: A formatted identifier string.
    """
    try:
        user_name: str = getpass.getuser()
        host_name: str = socket.gethostname()
        identifier: str = f"{tool_name}-{user_name}@{host_name}"
        logging.info(f"Generated url identifier: {identifier}")
        return identifier
    except Exception as e:
        logging.error(f"Failed to generate url identifier: {e}")
        return None


def generate_vault_identifier(server_url: str) -> Optional[str]:
    """
    Generate a unique identifier.

    :param tool_name: Tool or application name.
    :return: A formatted identifier string.
    """
    try:
        user_name: str = getpass.getuser()
        identifier: str = f"{user_name}@{server_url}"
        logging.info(f"Generated credential identifier: {identifier}")
        return identifier
    except Exception as e:
        logging.error(f"Failed to generate credential identifier: {e}")
        return None
