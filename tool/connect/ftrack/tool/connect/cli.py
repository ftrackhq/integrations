# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import click
import pkg_resources
from .commands.install import install
from .commands.uv import uv


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
    for entry_point in pkg_resources.iter_entry_points("connect.plugins"):
        try:
            command = entry_point.load()
            cli.add_command(command, name=entry_point.name)
        except Exception as e:
            print(f"Failed to load plugin '{entry_point.name}': {e}")


# Call load_plugins to ensure new commands are added
load_plugins()
