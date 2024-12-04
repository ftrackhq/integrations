# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import click
from ftrack.library.launch import launch_application


@click.group()
def launcher():
    """
    Launcher CLI tool
    """
    pass


@launcher.command()
@click.argument("app_name")
def start(app_name):
    """Launch the specified app."""
    launch_application(app_name)
