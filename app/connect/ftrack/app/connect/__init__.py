# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import click
from cli import cli

# Check if virtual environment is activated
import os
import sys

if not os.getenv('VIRTUAL_ENV'):
    print(
        "Warning: No virtual environment is active. Please activate your venv before proceeding."
    )

if __name__ == "__main__":
    cli()
