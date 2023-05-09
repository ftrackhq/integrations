# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import logging

from Qt import QtWidgets

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.client import Client

from ftrack_connect_pipeline_qt.ui.utility.widget.entity_browser import (
    EntityBrowser,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    dialog,
)


class QtChangeContextClient(Client):
    def __init__(self, event_manager):
        super(QtChangeContextClient, self).__init__(event_manager)


class QtChangeContextClientWidget(QtChangeContextClient, QtWidgets.QWidget):
    '''Client for changing the current working context within the host/DCC'''

    def __init__(self, event_manager, parent=None):
        '''
        Initialize QtChangeContextClientWidget

        :param event_manager:  :class:`~ftrack_connect_pipeline.event.EventManager` instance
        :param parent: The parent dialog or frame
        '''
        QtWidgets.QWidget.__init__(self, parent=parent)
        QtChangeContextClient.__init__(self, event_manager)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.entity_browser = EntityBrowser(
            None,
            self.session,
            title='CHOOSE TASK (WORKING CONTEXT)',
        )

        self.discover_hosts()

    # Host

    def on_hosts_discovered(self, host_connections):
        '''(Override)'''
        if len(host_connections) > 0:
            self.change_host(host_connections[0])

    def on_host_changed(self, host_connection):
        '''(Override)'''
        pass

    # Context

    def on_context_changed(self, context_id):
        '''(Override) Context has been evaluated'''
        # TODO: Handle context changed while widget is active (remote mode)

    # User

    def show(self):
        '''Show the entity browser'''
        # Find my host
        if self.host_connection is None:
            # TODO: support multiple hosts
            dialog.ModalDialog(
                None,
                title='Change context',
                message='No host detected, cannot change context!',
            )
            return
        self.entity_browser.entity_id = self.context_id
        self.entity_browser.setMinimumWidth(600)
        if self.entity_browser.exec_():
            self.change_ftrack_context_id(self.entity_browser.entity['id'])
            return True
        else:
            return False

    def change_ftrack_context_id(self, context_id):
        '''A new context has been chosen, store it in host and tell other clients'''
        self.context_id = context_id
