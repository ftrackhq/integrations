# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline.client import Client

from ftrack_connect_pipeline_qt.ui.utility.widget import dialog


class QtSaveClientWidget(Client, QtWidgets.QWidget):
    '''Client for saving the project/scene/script within DCC locally during work.

    This is sample code that exists here for reference and not used by the current
    version of the framework.
    '''

    def __init__(self, event_manager):
        Client.__init__(self, event_manager)

        self.discover_hosts()

    # Host

    def on_hosts_discovered(self, host_connections):
        '''(Override)'''
        if len(host_connections) > 0:
            # Use the first available host connection
            self.change_host(host_connections[0])

    def on_host_changed(self, host_connection):
        '''(Override)'''
        pass

    # Context

    def on_context_changed(self, context_id):
        '''(Override) Context has been evaluated'''

    # User

    def show(self):
        self.logger.info(
            'Attempting to incrementally save DCC work file locally..'
        )
        if self.context_id is None:
            dialog.ModalDialog(
                None,
                title='Save',
                message='No host selector or no context present, please set!',
            )
            return
        work_path, message = self.dcc_utils.save(
            self.context_id, self._event_manager.session, temp=False
        )
        if not message is None:
            self.logger.info(message)
