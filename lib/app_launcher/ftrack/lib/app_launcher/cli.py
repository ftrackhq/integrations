# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import click
from .launcher import launch_application


@click.group()
def app_launcher():
    """
    App Launcher CLI tool
    """
    pass


@app_launcher.command()
@click.argument("app_name")
def launch(app_name):
    """Launch the specified app."""
    launch_application(app_name)
