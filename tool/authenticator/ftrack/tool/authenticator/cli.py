# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import click
from ftrack.library.authenticate.authenticate import Authenticate
from ftrack.library.authenticate.util.identifier import (
    generate_vault_identifier,
)
from ftrack.library.authenticate.helper.credential import (
    CredentialFactory,
)
from ftrack.library.authenticate.helper.webserver import WebServerFactory
from ftrack.library.utility.url.checker import ftrack_server_url_checker


@click.group()
def authenticator():
    """
    Launcher CLI tool
    """
    pass


@authenticator.command()
@click.argument(
    "method",
    type=click.Choice(["browser", "credential"], case_sensitive=False),
    default="browser",
)
@click.argument(
    "server-url",
    type=str,
    metavar="<SERVER_URL>",
)
@click.option(
    "--credential-identifier",
    type=str,
    default=None,
    help=(
        "Optional. Unique identifier for the credentials. If omitted, it defaults to "
        "a generated identifier in the format <user_name>@<server_url>."
    ),
)
@click.option(
    "--api-user",
    type=str,
    required=False,
    help="API username for credential authentication.",
)
@click.option(
    "--api-key",
    type=str,
    required=False,
    help="API key for credential authentication.",
)
def authenticate(method, server_url, credential_identifier, api_user, api_key):
    """
    Authenticate using the specified method.

    \b
    Available methods:
    - browser: Authenticate via a browser-based flow (default).
    - credential: Authenticate using API credentials (requires --api-user and --api-key).
    """
    try:
        server_url = ftrack_server_url_checker(server_url)
        # Generate default credential identifier if not provided
        if not credential_identifier:
            credential_identifier = generate_vault_identifier(
                server_url=server_url,
            )

        credential_factory_instance = CredentialFactory(credential_identifier)
        auth = Authenticate(
            server_url, credential_factory_instance, WebServerFactory()
        )

        if method == "browser":
            auth.authenticate_browser()
        elif method == "credential":
            if not api_user or not api_key:
                raise click.BadParameter(
                    "Both --api-user and --api-key are required for credential authentication."
                )
            auth.authenticate_credential(server_url, api_user, api_key)
    except click.BadParameter as e:
        click.echo(f"Error: {e}", err=True)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)