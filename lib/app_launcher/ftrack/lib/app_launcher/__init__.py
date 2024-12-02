# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from .launcher import launch_application

# Import the CLI tool from the current module
from .cli import app_launcher

if __name__ == "__main__":
    app_launcher()
