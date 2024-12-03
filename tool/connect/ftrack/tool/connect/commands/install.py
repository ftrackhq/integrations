# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import click
import subprocess
import sys
import os


@click.command()
@click.argument("package")
@click.option(
    "-e", "--editable", is_flag=True, help="Install the package in editable mode"
)
def install(package, editable):
    """
    Install a package (from PyPI or a .whl file) into the active environment, which extends the CLI tool.
    """
    # Determine if the provided package is a .whl file or a PyPI package
    if os.path.isfile(package) and package.endswith(".whl"):
        # If it's a .whl file, ensure it's a valid file path
        package_path = os.path.abspath(package)
    elif os.path.isdir(package):
        # If it's a directory, treat it as a local package path
        package_path = os.path.abspath(package)
    else:
        # Otherwise, treat it as a PyPI package name
        package_path = package

    # TODO: Should we use uv to call pip in here?

    # Prepare the uv pip install command
    pip_command = ["uv", "pip", "install"]
    if editable and os.path.isdir(package):
        # Add the editable flag if requested and the package is a local directory
        pip_command.append("-e")
    pip_command.append(package_path)

    try:
        result = subprocess.run(
            pip_command, capture_output=True, text=True, env=os.environ
        )
        if result.returncode == 0:
            print(f"Package '{package}' installed successfully.")
        else:
            print(f"Failed to install '{package}': {result.stderr}")
    except Exception as e:
        print(f"An error occurred during installation: {e}")
