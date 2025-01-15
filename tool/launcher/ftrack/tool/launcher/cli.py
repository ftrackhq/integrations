# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import click
import subprocess

# import Configuration
import os
import logging
import yaml
import platform
import shutil


@click.group()
def launcher():
    """
    Launcher CLI tool
    """
    pass


@launcher.command()
@click.argument("app_name")
@click.argument("configuration")
def start(
    app_name,
    configuration,
):  # app_version, app_variant, configuration_file, config_name, refresh_configuration=False):
    """Launch the specified app."""
    pass
    # launchers = Configuration.get_resolved_configuration(
    #     configuration_file=configuration_file,
    #     config_name=config_name,
    #     python=python_version,
    #     app_version=app_version,
    #     app_variant=app_variant,
    # )
    # launch_application(app_name)


@click.argument("conflict_resolution_file", default="~/conflict_resolution.yaml")
@click.argument("resolution_folder", default="~/resolved")
@launcher.command()
def discover_configurations(conflict_resolution_file, resolution_folder):
    pass
    # configuration = Configuration()
    # configuration.load_from_entrypoint("launcher.configuration")
    # if conflict_resolution_file:
    #     configuration.compose(conflict_resolution_file=conflict_resolution_file)
    # else:
    #     configuration.compose()
    # configuration.resolve()
    # configuration.dump(resolution_folder)
    # click.echo(f"Resolved configurations are saved at: {resolution_folder}")


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
    """Create a virtual environment for the selected configuration."""
    # TODO:
    #   1. Load the resolved configuration yaml file
    #   2. isolate the launcher configuration based on the configuration name, python version and app version
    #   3. Create a virtual environment with the specified python version if doesn't exists or if force_refresh is True

    # Load the resolved configuration file with yaml library
    with open(resolved_configuration_file, "r") as yaml_file:
        try:
            yaml_content = yaml.safe_load(yaml_file)
        except yaml.YAMLError as exc:
            # Log an error if the yaml file is invalid.
            logging.error(
                logging.error(
                    f"Invalid .yaml file\nFile: {resolved_configuration_file}\nError: {exc}"
                )
            )
            raise click.Abort()

    try:
        launcher_configuration = yaml_content["launcher"].get(launcher_name)
    except KeyError:
        click.echo("launcher key is missing")
        raise click.Abort()

    if not launcher_configuration:
        if not yaml_content["launcher"]:
            click.echo("No launchers found.")
            raise click.Abort()
        click.echo("Available launchers:")
        for idx, ver in enumerate(list(yaml_content["launcher"].keys()), start=1):
            click.echo(f"{idx}. {ver}")
        choice = click.prompt(
            "Enter the id of the launcher you want to use",
            type=click.IntRange(1, len(yaml_content["launcher"])),
        )
        launcher_name = list(yaml_content["launcher"].keys())[choice - 1]
        launcher_configuration = yaml_content["launcher"][launcher_name]

    # Determine platform (windows, linux, etc.)
    platform_config = launcher_configuration.get("platform", {}).get(
        platform.system().lower()
    )
    if not platform_config:
        click.echo(f"No platform configuration for '{platform.system().lower()}'.")
        raise click.Abort()

    # Step 1: Prompt for application_version if not provided (or 0)
    all_versions = sorted(set(item["version"] for item in platform_config))
    if not application_version or application_version not in all_versions:
        click.echo("Available versions:")
        for idx, ver in enumerate(all_versions, start=1):
            click.echo(f"{idx}. {ver}")

        choice = click.prompt(
            "Enter the number of the version you want to use",
            type=click.IntRange(1, len(all_versions)),
        )
        application_version = all_versions[choice - 1]

    # Step 2: Prompt for application_variant if not provided or invalid
    # Filter the platform_config to only items with the chosen version
    version_config = [
        item for item in platform_config if item["version"] == application_version
    ]
    all_variants = sorted(set(item["variant"] for item in version_config))

    # If user didn't provide variant or it's invalid, prompt
    if not application_variant or application_variant not in all_variants:
        click.echo("Available variants:")
        for idx, var in enumerate(all_variants, start=1):
            click.echo(f"{idx}. {var}")

        choice = click.prompt(
            "Enter the number of the variant you want to use",
            type=click.IntRange(1, len(all_variants)),
        )
        application_variant = all_variants[choice - 1]

    # Step 3: Prompt for python_version if not provided or invalid
    # Filter again for the selected version + variant
    version_variant_config = [
        item for item in version_config if item["variant"] == application_variant
    ]
    all_python_versions = sorted(
        set(item["python-version"] for item in version_variant_config)
    )

    if not python_version or python_version not in all_python_versions:
        click.echo("Available Python versions:")
        for idx, py_ver in enumerate(all_python_versions, start=1):
            click.echo(f"{idx}. {py_ver}")

        choice = click.prompt(
            "Enter the number of the Python version you want to use",
            type=click.IntRange(1, len(all_python_versions)),
        )
        python_version = all_python_versions[choice - 1]

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
    # python_executable = environment_config["python"]
    python_packages = environment_config.get("python-packages", [])

    # Location of venv
    venv_base_path = yaml_content["path"].get("venv-installation", "/tmp/venvs")
    venv_path = os.path.join(venv_base_path, env_name)
    click.echo(f"Creating virtual environment at {venv_path}...")

    if not os.path.exists(venv_base_path):
        os.makedirs(venv_base_path, exist_ok=True)

    # Check existence
    if os.path.exists(venv_path):
        if force_refresh:
            # Remove the existing venv
            click.echo(f"Removing existing environment at {venv_path}...")
            shutil.rmtree(venv_path)
        else:
            # Skip creation if not forced
            click.echo(
                f"Environment '{env_name}' already exists at {venv_path}, skipping creation."
            )
            return

    # 1. Create environment with uv
    # TODO: make sure not to use the maya python provider to create the environment so using the python version instead of the python executable key
    subprocess.run(
        [
            "uv",
            "venv",
            f"--python={python_version}",
            f"--directory={venv_base_path}",
            env_name,
        ],
        check=True,
    )

    # 2. Install any packages
    if platform.system().lower().startswith("win"):
        bin_folder = "Scripts"
    else:
        # Linux, macOS, etc.
        bin_folder = "bin"

    python_in_venv = os.path.join(venv_path, bin_folder, "python")
    if python_packages:
        for pkg in python_packages:
            name = pkg["name"]
            version = pkg.get("version")
            package_str = f"{name}=={version}" if version else name
            subprocess.run(
                [
                    "uv",
                    "pip",
                    "install",
                    f"{package_str}",
                    f"--python={python_in_venv}",
                ],
                check=True,
            )
    else:
        click.echo("No Python packages to install.")

    click.echo(f"Virtual environment {venv_path} created successfully.")
