# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from QtExt import QtWidgets, QtCore
from ftrack_connect_pipeline.client.widgets import BaseWidget


class SimpleWidget(BaseWidget):

    def build(self):
        super(SimpleWidget, self).build()

        for key, value in self.options.items():
            option_layout = QtWidgets.QHBoxLayout()
            option_layout.setContentsMargins(5, 1, 5, 1)
            option_layout.setAlignment(QtCore.Qt.AlignTop)

            label = QtWidgets.QLabel(key)

            value = QtWidgets.QLineEdit(str(value))
            self.add_widget(key, value)

            option_layout.addWidget(label)
            option_layout.addWidget(value)
            self.layout().addLayout(option_layout)

    def __init__(self, parent=None, session=None, data=None, name=None, description=None, options=None):
        super(SimpleWidget, self).__init__(parent=parent, session=session, data=data, name=name, description=description, options=options)




