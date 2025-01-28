# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import click
import os
import platform
import subprocess
from pathlib import Path
from ftrack.library.utility.configuration import yaml_reader
from ftrack.library.utility.click import prompt
from ftrack.library.utility.uv import environment
from ftrack.library.configuration.configuration import Configuration
from ftrack.library.launch.launch import launch_application


@click.group()
def launcher():
    """
    Launcher CLI tool
    """
    pass


@launcher.command()
@click.argument("resolved_configuration_file")
@click.argument("identifier")
def start(resolved_configuration_file, identifier):
    """
    Launch a specified application using a configuration file and identifier.

    :param resolved_configuration_file: Path to the resolved configuration file.
    :param identifier: Identifier for the launcher to start.
    :raises click.Abort: If no launcher is found or the launcher configuration is invalid.
    :raises FileNotFoundError: If the Python version directory cannot be determined.
    """

    yaml_content = yaml_reader.parse_configuration(resolved_configuration_file)

    try:
        if not yaml_content["launcher"]:
            click.echo("No launchers found.")
            raise click.Abort()
    except KeyError:
        click.echo("launcher key is missing")
        raise click.Abort()

    launch_configuration = yaml_reader.recursive_find_in_nested_dictionary(
        yaml_content, {"identifier": identifier}
    )
    if not launch_configuration:
        click.echo("Could not found a matching launcher config.")
        raise click.Abort()

    venv_base_path = yaml_content["path"].get("venv-installation", "/tmp/venvs")
    venv_path = os.path.join(venv_base_path, identifier)

    # Find the Python version directory (e.g., python3.11)
    lib_path = Path(venv_path) / "lib"
    python_version_dir = next(lib_path.glob("python*"), None)
    if not python_version_dir:
        raise FileNotFoundError(
            f"Cannot determine Python version in virtual environment: {venv_path}"
        )
    site_packages = f"{python_version_dir}/site-packages"

    # env = os.environ.copy() # No need for now if just pythonpath is needed
    # Minimal environment with only PYTHONPATH
    env = {"PYTHONPATH": site_packages}

    executable = launch_configuration[0][1]["executable"]

    system = platform.system()

    kwargs = {}
    kwargs["env"] = env
    if system == "Windows":
        kwargs.update(
            creationflags=subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP
        )
    elif system == "Darwin":
        kwargs.update(start_new_session=True)
    elif system == "Linux":
        kwargs.update(start_new_session=True)
    else:
        raise OSError(f"Unsupported platform: {system}")

    launch_application(executable, **kwargs)


@launcher.command()
@click.argument("resolved_configuration_file", type=str)
def list_available_launchers(resolved_configuration_file):
    """
    List all available launchers defined in the configuration file.

    :param resolved_configuration_file: Path to the resolved configuration file.
    :raises click.Abort: If no launcher is found or the launcher key is missing in the configuration file.
    """
    yaml_content = yaml_reader.parse_configuration(resolved_configuration_file)

    try:
        if not yaml_content["launcher"]:
            click.echo("No launchers found.")
            raise click.Abort()
    except KeyError:
        click.echo("launcher key is missing")
        raise click.Abort()

    # 1. Determine current platform
    current_platform = platform.system().lower()

    # 2. Loop through launchers
    launchers = yaml_content.get("launcher", {})
    for launcher_key, launcher_data in launchers.items():
        application_name = launcher_data.get("application-name")
        if not application_name:
            # If there's no application-name, skip or handle differently
            continue

        # 3. Look for sub-entries under launcher_data["platform"][current_platform]
        platform_entries = launcher_data.get("platform", {}).get(current_platform, [])
        if not platform_entries:
            # Skip if no entries for this OS
            continue

        # 4. Print data in the desired format
        click.echo(f"{application_name}:")
        click.echo(f"  {launcher_key}")
        for entry in platform_entries:
            identifier = entry.get("identifier")
            if identifier:
                click.echo(f"    {identifier}")


@launcher.command()
@click.option(
    "--conflict_resolution_file",
    type=str,
    required=False,
    help="Pre-defined conflict resolution file",
)
@click.option(
    "--resolution_folder",
    type=str,
    required=False,
    help="Override the resolution folder provided in the config file",
)
def discover_configurations(conflict_resolution_file, resolution_folder):
    """
    Discover and resolve configurations based on provided parameters.

    :param conflict_resolution_file: Path to the pre-defined conflict resolution file.
    :param resolution_folder: Folder to override the configuration folder in the config file.
    :raises click.Abort: If no resolution folder is provided or if the folder cannot be created.
    """

    configuration = Configuration()
    configuration.load_from_entrypoint("connect.configuration")
    if conflict_resolution_file:
        configuration.compose(conflict_resolution_file=conflict_resolution_file)
    else:
        configuration.compose()
    configuration.resolve()
    if not resolution_folder:
        resolution_folder = configuration.resolved.get("path", {}).get(
            "configuration-installation"
        )
    else:
        click.echo(
            f"Overriding resolution folder from config file with provided {resolution_folder}"
        )
    if not resolution_folder:
        click.echo(
            "WARNING: No resolution folder provided. Skipping resolution dump. This will not allow you to launch the application as needs a resolved configuration file."
        )
        raise click.Abort()
    if not os.path.exists(resolution_folder):
        click.echo(
            f"Configuration folder doesn't exists, creating configuration folder: {resolution_folder}"
        )
        os.makedirs(resolution_folder, exist_ok=True)
    configuration.dump(resolution_folder)
    click.echo(f"Resolved configurations are saved at: {resolution_folder}")
    # TODO: maybe show each of the resolved files.


@launcher.command()
@click.argument("resolved_configuration_file", type=str)
@click.option(
    "--launcher_name", type=str, required=False, help="Name of the launcher to use"
)
@click.option(
    "--python_version", type=float, required=False, help="Python version to use"
)
@click.option(
    "--application_version", type=str, required=False, help="Application version to use"
)
@click.option(
    "--application_variant", type=str, required=False, help="Application variant to use"
)
@click.option(
    "--force_refresh",
    type=bool,
    default=False,
    help="Force refresh the virtual environment",
)
def make_launch_environment(
    resolved_configuration_file,
    launcher_name,
    python_version,
    application_version,
    application_variant,
    force_refresh,
):
    """
    Create a virtual environment for a specified launcher configuration.

    :param resolved_configuration_file: Path to the resolved configuration file.
    :param launcher_name: Name of the launcher to use.
    :param python_version: Python version to use.
    :param application_version: Application version to use.
    :param application_variant: Application variant to use.
    :param force_refresh: Whether to force refresh the virtual environment.
    :raises click.Abort: If no matching launcher or platform configuration is found.
    """

    # Load the resolved configuration file with yaml library
    yaml_content = yaml_reader.parse_configuration(resolved_configuration_file)

    try:
        if not yaml_content["launcher"]:
            click.echo("No launchers found.")
            raise click.Abort()
    except KeyError:
        click.echo("launcher key is missing")
        raise click.Abort()

    launcher_name = prompt.prompt_for_choice(
        list(yaml_content["launcher"].keys()),
        launcher_name,
        "launcher",
        allow_custom=False,
    )
    launcher_configuration = yaml_content["launcher"][launcher_name]

    # Determine platform (windows, linux, etc.)
    platform_config = launcher_configuration.get("platform", {}).get(
        platform.system().lower()
    )
    if not platform_config:
        click.echo(f"No platform configuration for '{platform.system().lower()}'.")
        raise click.Abort()

    # Step 1: Prompt for application_version if not provided
    all_versions = sorted(set(item["version"] for item in platform_config))
    application_version = prompt.prompt_for_choice(
        all_versions, application_version, "application version", allow_custom=False
    )

    # Step 2: Prompt for application_variant if not provided or invalid
    # Filter the platform_config to only items with the chosen version
    version_config = [
        item for item in platform_config if item["version"] == application_version
    ]
    all_variants = sorted(set(item["variant"] for item in version_config))
    application_variant = prompt.prompt_for_choice(
        all_variants, application_variant, "application variant", allow_custom=False
    )

    # Step 3: Prompt for python_version if not provided or invalid
    # Filter again for the selected version + variant
    version_variant_config = [
        item for item in version_config if item["variant"] == application_variant
    ]
    all_python_versions = sorted(
        set(item["python-version"] for item in version_variant_config)
    )
    python_version = prompt.prompt_for_choice(
        all_python_versions, python_version, "python version", allow_custom=False
    )

    # Finally, pick the matching config
    environment_config = None
    for item in version_variant_config:
        if item["python-version"] == python_version:
            environment_config = item
            break

    if not environment_config:
        click.echo("Could not find a matching launcher config.")
        raise click.Abort()

    click.echo(f"Selected environment config: {environment_config}")

    # Create the virtual environment
    env_name = environment_config["identifier"]
    # TODO: make sure not to use the maya python provider to create the
    #  environment always use the python version instead of
    #  the python executable key
    # python_executable = environment_config["python"]
    python_packages = environment_config.get("python-packages", [])

    # Location of venv
    venv_base_path = yaml_content["path"].get("venv-installation", "/tmp/venvs")
    venv_path = os.path.join(venv_base_path, env_name)
    click.echo(f"Creating virtual environment at {venv_path}...")

    environment.create_virtual_environment_on_path(
        venv_base_path, env_name, python_version, force_refresh
    )

    if python_packages:
        click.echo(f"Installing packages on virtual environment at {venv_path}...")
        environment.install_packages_on_virtual_environment(venv_path, python_packages)
    else:
        click.echo("No Python packages to install.")

    click.echo(f"Virtual environment {venv_path} created successfully.")
