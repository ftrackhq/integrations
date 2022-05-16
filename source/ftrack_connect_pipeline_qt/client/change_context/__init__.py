# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import logging

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.client import Client

from ftrack_connect_pipeline_qt.ui.utility.widget.entity_browser import (
    EntityBrowser,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    dialog,
)


class QtChangeContextClient(Client):
    '''Client for changing the current working context.'''

    def __init__(self, event_manager, unused_asset_list_model):
        Client.__init__(self, event_manager)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._host_connection = None

        self.pre_build()
        self.post_build()

    def pre_build(self):
        self.entity_browser = EntityBrowser(
            None,
            self.session,
            title='CHOOSE TASK (WORKING CONTEXT)',
        )

    def post_build(self):
        self._host_connections = self.discover_hosts()
        if len(self._host_connections) == 1:
            self._host_connection = self._host_connections[0]

    def show(self):
        # Find my host
        if self._host_connection is None:
            if len(self._host_connections) == 0:
                dialog.ModalDialog(
                    None,
                    title='Change context',
                    message='No host detected, cannot change context!',
                )
                return
            # Need to choose host connection
            self._host_connections[0].launch_widget(core_constants.OPENER)
            return
        self.entity_browser.setMinimumWidth(600)
        if self.entity_browser.exec_():
            self.change_ftrack_context_id(self.entity_browser.entity)

    def change_ftrack_context_id(self, context):
        self._host_connection.change_ftrack_context_id(context)
