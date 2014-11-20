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
    raise SystemExit(
        ftrack_connect.__main__.main(arguments=sys.argv[1:])
    )
