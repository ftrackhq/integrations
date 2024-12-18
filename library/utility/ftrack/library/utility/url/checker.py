# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from urllib.parse import urlparse, urlunparse


def ftrack_server_url_checker(url: str) -> str:
    """
    Validates and constructs a proper Ftrack server URL, ensuring it uses HTTPS.

    :param url: The input server URL.
    :return: A validated and properly formatted Ftrack server URL with HTTPS.
    :raises ValueError: If the URL is invalid.
    """
    # Strip leading and trailing slashes and spaces
    url = url.strip("/ ")

    # If URL is empty after stripping
    if not url:
        raise ValueError(
            "You need to specify a valid server URL, "
            "for example https://server-name.ftrackapp.com"
        )

    # If 'http' is not in the URL, construct the URL
    if "http" not in url:
        if url.endswith("ftrackapp.com"):
            url = "https://" + url
        else:
            url = f"https://{url}.ftrackapp.com"

    # Parse the URL
    parsed_url = urlparse(url)
    if not parsed_url.netloc:
        raise ValueError(
            "The provided URL is not valid. Please ensure it is properly formatted."
        )

    # Enforce HTTPS scheme
    if parsed_url.scheme != "https":
        parsed_url = parsed_url._replace(scheme="https")
        url = urlunparse(parsed_url)

    # Ensure the URL ends with 'ftrackapp.com'
    if not parsed_url.netloc.endswith("ftrackapp.com"):
        raise ValueError(
            "The server URL must end with 'ftrackapp.com'. "
            "For example: https://server-name.ftrackapp.com"
        )

    return url
