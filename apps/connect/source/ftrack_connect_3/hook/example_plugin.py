# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import ftrack_api
import logging

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

import ftrack_connect.ui.application

logger = logging.getLogger('ftrack_connect.plugin.actions')


class ExamplePlugin(ftrack_connect.ui.application.ConnectWidget):
    '''Base widget for ftrack connect actions plugin.'''

    icon = ':ftrack/image/default/ftrackLogoColor'

    def __init__(self, session, parent=None):
        '''Instantiate the actions widget.'''
        super(ExamplePlugin, self).__init__(session, parent=parent)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        text = QtWidgets.QLabel('This is a test plugin!')
        layout.addWidget(text)


def register(session, **kw):
    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        logger.debug(
            'Not subscribing plugin as passed argument {0!r} is not an '
            'ftrack_api.Session instance.'.format(session)
        )
        return

    # #  Uncomment to register plugin
    # plugin = ftrack_connect.ui.application.ConnectWidgetPlugin(ExamplePlugin)
    # plugin.register(session, priority=10)
