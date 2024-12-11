# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import click
from ftrack.library.authenticate.authenticate import Authenticate
from ftrack.library.authenticate.util.identifier import generate_credential_identifier
from ftrack.library.authenticate.helper.credential import CredentialProvider


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
    "--api-key", type=str, required=False, help="API key for credential authentication."
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
        # Generate default credential identifier if not provided
        if not credential_identifier:
            credential_identifier = generate_credential_identifier(
                server_url=server_url,
            )

        credential_provider = CredentialProvider(credential_identifier)
        auth = Authenticate(server_url, credential_provider)

        if method == "browser":
            auth.browser_authenticate()
        elif method == "credential":
            if not api_user or not api_key:
                raise click.BadParameter(
                    "Both --api-user and --api-key are required for credential authentication."
                )
            auth.credential_authenticate(server_url, api_user, api_key)
    except click.BadParameter as e:
        click.echo(f"Error: {e}", err=True)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)
