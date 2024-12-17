# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import click
from ftrack.library.authenticate.util.identifier import (
    generate_vault_identifier,
)
from ftrack.library.authenticate.helper.credential import (
    CredentialFactory,
)

from ftrack.library.session.session import SessionProvider
from ftrack.library.utility.url.checker import ftrack_server_url_checker


@click.group()
def session():
    """
    Launcher CLI tool
    """
    pass


@session.command()
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
def start_event_hub(server_url, credential_identifier):
    """
    Start the event hub thread.

    :param server_url: Server URL.
    :param credential_identifier: Unique identifier for the credentials.
    """
    try:
        server_url = ftrack_server_url_checker(server_url)
        if not credential_identifier:
            credential_identifier = generate_vault_identifier(
                server_url=server_url
            )

        credential_factory_instance = CredentialFactory(credential_identifier)

        session_provider_instance = SessionProvider(
            credential_factory_instance
        )
        # TODO: we should probably not start the event hub in a new thread ere, but instead in a new process?. We have to review this.
        session = (
            session_provider_instance.new_session_from_stored_credentials(
                spread_event_hub_thread=True
            )
        )
        click.echo(f"Event hub thread started for session {session}")

    except click.BadParameter as e:
        click.echo(f"Error: {e}", err=True)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)
