# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtCore, QtWidgets

from PySide2 import (
    QtWebEngineWidgets,
)  # Qt.py does not provide QtWebEngineWidgets

from ftrack_connect_pipeline.client import Client
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    dialog,
    header,
    line,
    host_selector,
)

from ftrack_connect_pipeline_qt.utils import get_theme, set_theme


class QtWebViewClientWidget(Client, dialog.Dialog):
    '''Web widget viewer client base - a dialog for rendering web content within
    framework'''

    def __init__(self, event_manager, parent=None):
        '''
        Initialize QtWebViewClientWidget

        :param event_manager: :class:`~ftrack_connect_pipeline.event.EventManager` instance
        :param parent: The parent dialog or frame
        '''
        dialog.Dialog.__init__(self, parent=parent)
        Client.__init__(self, event_manager)

        self._context = None

        set_theme(self, get_theme())
        if self.get_theme_background_style():
            self.setProperty('background', self.get_theme_background_style())
        if self.get_theme_background_style():
            self.setProperty('background', self.get_theme_background_style())

        self.pre_build()
        self.build()
        self.post_build()

        self.discover_hosts()

        self.resize(500, 600)

    def get_theme_background_style(self):
        '''Return the theme background color style. Can be overridden by child.'''
        return 'ftrack'

    # Build

    def pre_build(self):
        self._header = header.Header(self.session, parent=self.parent())
        self.host_selector = host_selector.HostSelector(self)
        self._web_engine_view = QtWebEngineWidgets.QWebEngineView(
            parent=self.parent()
        )
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def build(self):
        self.layout().addWidget(self._header)
        self.layout().addWidget(self.host_selector)
        self.layout().addWidget(line.Line(style='solid', parent=self))
        self.layout().addWidget(self._web_engine_view, 100)

    def post_build(self):
        self.host_selector.hostChanged.connect(self.change_host)

    # Host

    def on_hosts_discovered(self, host_connections):
        '''(Override)'''
        self.host_selector.add_hosts(host_connections)

    # Context

    def on_context_changed(self, context_id):
        '''Context has been set in context selector'''
        self._context = self.session.query(
            'Task where id={}'.format(context_id)
        ).one()
        self._web_engine_view.load(self.get_url())

    def show(self):
        '''Show the dialog, sets the context to default and loads content if not done previously'''
        super(QtWebViewClientWidget, self).show()

    def get_url(self):
        '''Retreive the URL of content to view'''
        raise NotImplementedError()


class QtInfoWebViewClientWidget(QtWebViewClientWidget):
    '''Show the current context(task) info within a web client dialog'''

    def __init__(self, event_manger, parent=None):
        super(QtInfoWebViewClientWidget, self).__init__(
            event_manger, parent=parent
        )
        self.setWindowTitle('Task info')

    def get_url(self):
        return self.session.get_widget_url('info', entity=self._context)


class QtTasksWebViewClientWidget(QtWebViewClientWidget):
    '''Show assigned tasks with a web client dialog'''

    def __init__(self, event_manger, parent=None):
        super(QtTasksWebViewClientWidget, self).__init__(
            event_manger, parent=parent
        )
        self.setWindowTitle('My Tasks')

    def get_url(self):
        return self.session.get_widget_url('tasks')
