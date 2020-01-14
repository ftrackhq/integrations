# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from Qt import QtWidgets
from ftrack_connect_pipeline import client
from ftrack_connect_pipeline_qt.ui.widget import header


class QtHostConnection(client.HostConnection):

    def __init__(self, event_manager, host_data):
        super(QtHostConnection, self).__init__(event_manager, host_data)

class QtClient(client.Client, QtWidgets.QWidget):
    '''
    Base client widget class.
    '''

    def __init__(self, event_manager, ui, parent=None):
        '''Initialise widget with *ui* , *host* and *hostid*.'''
        QtWidgets.QWidget.__init__(self, parent=parent)
        client.Client.__init__(self, event_manager, ui)
        print "eoooooo"

    def on_ready(self, time_out=3):
        hosts = self.discover_hosts(time_out=time_out)
        print "hosts"
        self.pre_build()

    def pre_build(self):
        '''Prepare general layout.'''
        print "style --> {}".format(self.styleSheet())
        #self.setStyleSheet(self.styleSheet())
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.combo_hosts = QtWidgets.QComboBox()
        self.layout().addWidget(self.combo_hosts)
        self.combo_hosts.addItem('- Select host -')

        # if self.hostid:
        #     self.combo_hosts.setVisible(False)

        self.header = header.Header(self.session)
        self.layout().addWidget(self.header)
        self.combo = QtWidgets.QComboBox()
        self.layout().addWidget(self.combo)
        self.task_layout = QtWidgets.QVBoxLayout()
        self.layout().addLayout(self.task_layout)
        self.run_button = QtWidgets.QPushButton('Run')
        self.layout().addWidget(self.run_button)


