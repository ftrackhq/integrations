# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import subprocess

import click


@click.command()
@click.argument("uv_command", nargs=-1)
def uv(uv_command):
    """
    Run uv commands from the internal dependency.
    """
    try:
        result = subprocess.run(["uv", *uv_command], capture_output=True, text=True)
        if result.returncode == 0:
            click.echo(result.stdout)
        else:
            click.echo(f"Failed to execute uv command: {result.stderr}", err=True)
    except FileNotFoundError:
        click.echo(
            "Error: 'uv' command not found. Ensure it is installed and available in PATH.",
            err=True,
        )
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)
