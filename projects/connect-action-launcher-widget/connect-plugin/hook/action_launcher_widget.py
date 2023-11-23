# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import sys
import logging

import ftrack_api
from ftrack_connect.qt import QtWidgets, QtCore, QtGui
import ftrack_connect.ui.application
from ftrack_connect.util import get_connect_plugin_version

logger = logging.getLogger(__name__)

cwd = os.path.dirname(__file__)
connect_plugin_path = os.path.abspath(os.path.join(cwd, '..'))

# Read version number from __version__.py
__version__ = get_connect_plugin_version(connect_plugin_path)

sources = os.path.abspath(os.path.join(connect_plugin_path, 'dependencies'))
sys.path.append(sources)


from ftrack_connect_action_launcher_widget.actions import Actions


class ActionLauncherWidget(ftrack_connect.ui.application.ConnectWidget):
    name = 'Launch'

    def __init__(self, session, parent=None):
        '''Instantiate the actions widget.'''
        super(ActionLauncherWidget, self).__init__(session, parent=parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.actionsView = Actions(self.session)
        layout.addWidget(self.actionsView)


def get_version_information(event):
    '''Return version information for ftrack connect plugin.'''
    return [dict(name='connect-action-launcher-widget', version=__version__)]


def register(session, **kw):
    '''Register plugin. Called when used as a plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        logger.debug(
            'Not subscribing plugin as passed argument {0!r} is not an '
            'ftrack_api.Session instance.'.format(session)
        )
        return

    #  Uncomment to register plugin
    plugin = ftrack_connect.ui.application.ConnectWidgetPlugin(
        ActionLauncherWidget
    )
    plugin.register(session, priority=20)

    # Enable plugin info in Connect about dialog
    session.event_hub.subscribe(
        'topic=ftrack.connect.plugin.debug-information',
        get_version_information,
        priority=20,
    )
