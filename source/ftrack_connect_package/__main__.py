# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import sys
import os

# Hooks use the ftrack event system. Set the FTRACK_EVENT_PLUGIN_PATH
# to pick up the default hooks if it has not already been set.
if getattr(sys, 'frozen', False):
    os.environ.setdefault(
        'FTRACK_EVENT_PLUGIN_PATH',
        os.path.abspath(
            os.path.join(
                os.path.dirname(sys.executable), 'resource', 'hook'
            )
        )
    )

import ftrack_connect.__main__


if __name__ == '__main__':
    arguments = sys.argv[1:]

    if sys.platform == "darwin" and getattr(sys, 'frozen', False):
        # Filter out PSN (process serial number) argument passed by OSX.
        arguments = [
            argument for argument in arguments
            if '-psn_0_' not in argument
        ]

    raise SystemExit(
        ftrack_connect.__main__.main(arguments=arguments)
    )
