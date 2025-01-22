# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os
import logging
import shutil
import subprocess
import platform


def create_virtual_environment_on_path(
    venv_base_path, env_name, python_version, force_refresh=False
):
    """Create a virtual environment on the specified path."""
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


def install_packages_on_virtual_environment(venv_path, python_packages):
    """Install packages on the specified virtual environment."""
    # Check platform bild folder
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
