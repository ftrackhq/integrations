# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import sys
import os
import argparse


if getattr(sys, 'frozen', False):
    # Hooks use the ftrack event system. Set the FTRACK_EVENT_PLUGIN_PATH
    # to pick up the default hooks if it has not already been set.
    os.environ.setdefault(
        'FTRACK_EVENT_PLUGIN_PATH',
        os.path.abspath(
            os.path.join(
                os.path.dirname(sys.executable), 'resource', 'hook'
            )
        )
    )

    # Set path to resource script folder if package is frozen.
    os.environ.setdefault(
        'FTRACK_RESOURCE_SCRIPT_PATH',
        os.path.abspath(
            os.path.join(
                os.path.dirname(sys.executable), 'resource', 'script'
            )
        )
    )

    # Set the path to certificate file in resource folder. This allows requests
    # module to read it outside frozen zip file.
    os.environ.setdefault(
        'REQUESTS_CA_BUNDLE',
        os.path.abspath(
            os.path.join(
                os.path.dirname(sys.executable), 'resource', 'cacert.pem'
            )
        )
    )

import ftrack_connect.__main__


def _validatePythonScript(path):
    '''Validate if *path* is a valid python script.'''
    return path and path.endswith('.py') and os.path.exists(path)


if __name__ == '__main__':
    arguments = sys.argv[1:]

    if sys.platform == "darwin" and getattr(sys, 'frozen', False):
        # Filter out PSN (process serial number) argument passed by OSX.
        arguments = [
            argument for argument in arguments
            if '-psn_0_' not in argument
        ]

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'script',
        help='Path to python script to execute.',
        default='',
        nargs='?'
    )

    parsedArguments, unknownArguments = parser.parse_known_args(arguments)

    # If first argument is an executable python script, execute the file.
    if (
        parsedArguments.script and
        _validatePythonScript(parsedArguments.script)
    ):
        execfile(parsedArguments.script)

        raise SystemExit()

    raise SystemExit(
        ftrack_connect.__main__.main(arguments=arguments)
    )
