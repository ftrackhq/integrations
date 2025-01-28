# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import click
from importlib.metadata import entry_points
# from importlib_metadata import entry_points  # for python <3.8 Requires `importlib_metadata` package


from .command.install import install
from .command.uv import uv


@click.group()
def cli():
    """
    Connect CLI tool
    """
    pass


# Register the install and uv commands
cli.add_command(install)
cli.add_command(uv)


# Load plugins dynamically using entry points
def load_plugins():
    """
    Load plugins dynamically from the installed packages using entry points.
    """
    for entry_point in entry_points(group="connect.plugins"):
        try:
            command = entry_point.load()
            cli.add_command(command, name=entry_point.name)
        except Exception as e:
            click.echo(f"Failed to load plugin {entry_point.name}: {e}", err=True)


# Call load_plugins to ensure new commands are added
load_plugins()
