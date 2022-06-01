# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline.client import Client

from ftrack_connect_pipeline_qt.ui.utility.widget import dialog


class QtSaveClientWidget(Client, QtWidgets.QWidget):
    '''Web widget viewer client base - a dialog for rendering web content within
    framework'''

    def __init__(self, event_manager, unused_asset_list_model):
        Client.__init__(self, event_manager)

        if not self.host_connections:
            self.discover_hosts()

    # Host

    def on_hosts_discovered(self, host_connections):
        '''(Override)'''
        if len(host_connections) > 0:
            # Use the first available host connection
            self.change_host(host_connections[0])

    # Use

    def show(self):
        self.logger.info('Attempting to save DCC work file locally..')
        if self.context_id is None:
            dialog.ModalDialog(
                None,
                title='Save',
                message='No host selector or no context present, please set!',
            )
            return
        work_path, message = self.dcc_utils.save(
            self.context_id, self._event_manager.session
        )
        if not message is None:
            self.logger.info(message)
