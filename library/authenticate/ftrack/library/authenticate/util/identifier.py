# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import logging
import getpass
import socket

# Configure logging
logging.basicConfig(level=logging.INFO)


def generic_identifier(user_name, host_name, tool_name):
    """
    Generate a generic identifier string.

    :param user_name: User's name.
    :param host_name: Host machine's name.
    :param tool_name: Tool or application name.
    :return: A formatted identifier string.
    """
    identifier = f"{tool_name}-{user_name}@{host_name}"
    logging.info(f"Generated identifier: {identifier}")
    return identifier


def connect_identifier():
    # TODO: Maybe as an optional argument we could add id so this way we allow to have 2 different connect open at the same time with different identifiers.
    """
    Generate an identifier for ftrack-connect.

    :return: A formatted identifier for ftrack-connect.
    """
    try:
        user_name = getpass.getuser()
        host_name = socket.gethostname()
        return generic_identifier(user_name, host_name, "ftrack-connect")
    except Exception as e:
        logging.error(f"Failed to generate connect identifier: {e}")
        return None
