# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from Qt import QtWidgets, QtCore, QtGui
from ftrack_connect_pipeline_qt import plugin
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget


class FileCollectorWidget(BaseOptionsWidget):
    '''Main class to represent a context widget on a publish process'''

    def __init__(
            self, parent=None, context=None, session=None, data=None, name=None,
            description=None, options=None
    ):
        '''initialise FileCollectorWidget with *parent*, *session*, *data*,
        *name*, *description*, *options*
        '''
        super(FileCollectorWidget, self).__init__(
            parent=parent, session=session, data=data, name=name,
            description=description, options=options
        )

    def build(self):
        '''build function widgets.'''
        super(FileCollectorWidget, self).build()

        current_path = self.options.get('path')

        widget_layout = QtWidgets.QHBoxLayout()
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.setAlignment(QtCore.Qt.AlignTop)

        label = QtWidgets.QLabel('path')
        self.line_edit = QtWidgets.QLineEdit(current_path)
        self.browser_button = QtWidgets.QPushButton("Browse")

        widget_layout.addWidget(label)
        widget_layout.addWidget(self.line_edit)
        widget_layout.addWidget(self.browser_button)
        self.layout().addLayout(widget_layout)

        self.file_selector = QtWidgets.QFileDialog()
        self.file_selector.setFileMode(QtWidgets.QFileDialog.ExistingFile)

    def post_build(self):
        '''hook events'''
        super(FileCollectorWidget, self).post_build()
        self.browser_button.clicked.connect(self._show_file_dialog)
        self.file_selector.fileSelected.connect(self._on_select_file)
        self.line_edit.textChanged.connect(self._on_path_changed)

    def _show_file_dialog(self):
        ''' Shows the file dialog'''
        self.file_selector.show()

    def _on_select_file(self, path):
        '''Updates the text with provided *path* when
        fileSelected of file_selector event is triggered'''
        self.line_edit.clear()
        self.line_edit.setText(path)

    def _on_path_changed(self, path):
        '''Updates the options dictionary with provided *path* when
        textChanged of line_edit event is triggered'''
        self.set_option_result(path, key='path')


class CollectorWidget(plugin.CollectorWidget):
    plugin_name = 'file_collector.widget'
    widget = FileCollectorWidget


def register(api_object, **kw):
    plugin = CollectorWidget(api_object)
    plugin.register()
