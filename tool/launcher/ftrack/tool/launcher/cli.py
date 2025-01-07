# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import click
from ftrack.library.launch import launch_application
import subprocess
import Configuration
import os


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


@launcher.command()
@click.argument()
def discover_configurations():
    configuration = Configuration()
    conf_object = configuration.load_from_entry_point("launcher.configuration")
    print(conf_object.get_launch_configuration())
    # Expected output:
    #  maya-lluis
    #  maya-default
    #  maya-animation
    #  blender-animation


@launcher.command()
@click.argument()
def resolve_configurations():
    configuration = Configuration()
    resolved_file = configuration.resolve()
    return resolved_file


@launcher.command()
@click.argument("resolved_file", default="my/resolved_config.yaml")
@click.argument("config_name", default="maya-lluis")
@click.argument("python_version", type=float, default=3.11)
@click.argument("app_version", type=int, default=2025)
@click.argument("force_refresh", type=bool, default=False)
def make_configuration(
    resolved_file, config_name, python_version, app_version, force_refresh
):
    launchers = Configuration.get_resolved_configuration(
        resolved_file,
        config_name=config_name,
        python=python_version,
        app_version=app_version,
    )

    selected_launcher = None
    if len(launchers) > 1:
        click.echo("Multiple configurations found. Please choose one to start:")

        # Display available launcher options
        for i, launcher in enumerate(launchers, 1):
            click.echo(f"{i}. {launcher}")

        # Prompt user to select a launcher
        choice = click.prompt(
            "Enter the number of the launcher you want to use",
            type=click.IntRange(1, len(launchers)),
        )
        selected_launcher = launchers[choice - 1]
    elif len(launchers) == 1:
        selected_launcher = launchers[0]
    else:
        click.echo("No configurations found.")
        raise click.Abort()

    click.echo(f"{selected_launcher} found. Starting...")

    # Create virtual environment if not exists
    venv_name = (
        selected_launcher.get("venv", {}).get(app_version, {}).get("name")
    )  # maya_animation_maya_2025_3.11
    venv_path = (
        selected_launcher.get("venv", {}).get(app_version, {}).get("path")
    )  # appdata/ftrack/connect/maya_animation_maya_2025_3.11
    python_version = (
        selected_launcher.get("venv", {}).get(app_version, {}).get("python_version")
    )  # 3.11 This might be a list in the future
    packages = (
        selected_launcher.get("venv", {}).get(app_version, {}).get("packages", [])
    )  # maya_animation_maya_2025_3.11

    # Get a list of existing environments using `uv venv list --json`
    if os.path.exists(venv_path):
        venv_exists = True

    if venv_exists and not force_refresh:
        click.echo(f"Virtual environment '{venv_name}' already exists.")
        # TODO: Validate the resolved config file inside the venv
    else:
        # Create the virtual environment
        click.echo(
            f"Creating virtual environment '{venv_name}' with Python {python_version}..."
        )
        subprocess.run(
            ["uv", "venv", f"--python={python_version}", venv_name], check=True
        )
        # activate venv

        # Install required packages
        if packages:
            for package in packages:
                click.echo(f"Installing package: {package}")
                subprocess.run(
                    ["uv", "pip", "install", f"{package}", f"--python={venv_name}"],
                    check=True,
                )

    click.echo(f"Virtual environment '{venv_name}' is ready!")
