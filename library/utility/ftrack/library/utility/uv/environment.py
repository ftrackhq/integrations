# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os
import logging
import shutil
import subprocess
import platform


def create_virtual_environment_on_path(
    venv_base_path: str, env_name: str, python_version: str, force_refresh: bool = False
) -> None:
    """
    Create a virtual environment at the specified path.

    :param venv_base_path: The base directory for the virtual environment.
    :param env_name: Name of the virtual environment.
    :param python_version: Python version to use for the environment.
    :param force_refresh: Whether to recreate the environment if it already exists.
    :return: None
    """
    venv_path = os.path.join(venv_base_path, env_name)

    if not os.path.exists(venv_base_path):
        logging.info(
            f"Creating directory base for virtual environment on path: {venv_base_path}"
        )
        os.makedirs(venv_base_path, exist_ok=True)
    # Check existence
    if os.path.exists(venv_path):
        if force_refresh:
            # Remove the existing venv
            logging.info(f"Removing existing environment at {venv_path}...")
            shutil.rmtree(venv_path)
        else:
            # Skip creation if not forced
            logging.info(
                f"Environment '{env_name}' already exists at {venv_path}, skipping creation."
            )
            return

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


def install_packages_on_virtual_environment(
    venv_path: str, python_packages: list[dict]
) -> None:
    """
    Install specified Python packages in the virtual environment.

    :param venv_path: Path to the virtual environment.
    :param python_packages: List of dictionaries with packages to install.
    :return: None
    """
    # Check platform bild folder
    print(python_packages)
    if platform.system().lower().startswith("win"):
        bin_folder = "Scripts"
    else:
        # Linux, macOS, etc.
        bin_folder = "bin"

    python_in_venv = os.path.join(venv_path, bin_folder, "python")

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
