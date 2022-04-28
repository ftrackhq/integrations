# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtCore, QtWidgets

from PySide2 import (
    QtWebEngineWidgets,
)  # Qt.py does not provide QtWebEngineWidgets

from ftrack_connect_pipeline.utils import get_current_context_id
from ftrack_connect_pipeline_qt.ui.utility.widget import dialog, header
from ftrack_connect_pipeline_qt.ui import theme


class QtWebViewClientBase(dialog.Dialog):
    '''Web widget viewer base'''

    @property
    def session(self):
        '''
        Returns instance of :class:`ftrack_api.session.Session`
        '''
        return self._event_manager.session

    def __init__(self, event_manger, parent=None):
        self._event_manager = event_manger
        super(QtWebViewClientBase, self).__init__(parent=parent)

        self._context = None

        if self.getTheme():
            self.setTheme(self.getTheme())
            if self.getThemeBackgroundStyle():
                self.setProperty('background', self.getThemeBackgroundStyle())

        self.pre_build()
        self.build()

        self.resize(500, 600)

    def getTheme(self):
        '''Return the client theme, return None to disable themes. Can be overridden by child.'''
        return 'dark'

    def setTheme(self, selected_theme):
        theme.applyFont()
        theme.applyTheme(self, selected_theme, 'plastique')

    def getThemeBackgroundStyle(self):
        '''Return the theme background color style. Can be overridden by child.'''
        return 'ftrack'

    def pre_build(self):

        self._header = header.Header(self.session, parent=self.parent())
        self._web_engine_view = QtWebEngineWidgets.QWebEngineView(
            parent=self.parent()
        )

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def build(self):
        self.layout().addWidget(self._header)
        self.layout().addWidget(self._web_engine_view, 100)

    def set_context_id(self, context_id):
        self._context = self.session.query(
            'Task where id={}'.format(context_id)
        ).one()
        self._web_engine_view.load(self.get_url())

    def show(self):
        if self._context is None:
            self.set_context_id(get_current_context_id())
        super(QtWebViewClientBase, self).show()

    def get_url(self):
        raise NotImplementedError()


class QtInfoWebViewClient(QtWebViewClientBase):
    def __init__(self, event_manger, unused_asset_model, parent=None):
        super(QtInfoWebViewClient, self).__init__(event_manger, parent=parent)
        self.setWindowTitle('Task info')

    def get_url(self):
        return self.session.get_widget_url('info', entity=self._context)


class QtTasksWebViewClient(QtWebViewClientBase):
    def __init__(self, event_manger, unused_asset_model, parent=None):
        super(QtTasksWebViewClient, self).__init__(event_manger, parent=parent)
        self.setWindowTitle('My Tasks')

    def get_url(self):
        return self.session.get_widget_url('tasks', entity=self._context)
