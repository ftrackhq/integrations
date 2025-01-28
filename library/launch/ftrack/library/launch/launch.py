# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import subprocess


def launch_application(
    executable: str,
    **popen_options: dict,
):
    """Logic to launch the specified app."""
    subprocess.Popen([executable], **popen_options)
    print(f"Launching application: {executable}")
