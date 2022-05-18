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

        self.discover_hosts()

    def pre_build(self):
        self.entity_browser = EntityBrowser(
            None,
            self.session,
            title='CHOOSE TASK (WORKING CONTEXT)',
        )

    def on_hosts_discovered(self, host_connections):
        if len(host_connections) > 0:
            self.change_host(host_connections[0])

    def show(self):
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
            self.change_ftrack_context_id(self.entity_browser.entity)

    def change_ftrack_context_id(self, context_id):
        self.host_connection.context_id = context_id
