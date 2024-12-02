# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import click
import subprocess


@click.command()
@click.argument("uv_command", nargs=-1)
def uv(uv_command):
    """
    Run uv commands from the internal dependency.
    """
    try:
        result = subprocess.run(["uv", *uv_command], capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"Failed to execute uv command: {result.stderr}")
    except FileNotFoundError:
        print("uv is not installed. Install it as a dependency first.")
    except Exception as e:
        print(f"An error occurred while running the command: {e}")
