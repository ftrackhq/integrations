# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.ui.utility.widget.material_icon import (
    MaterialIconWidget,
)


class CircularButton(QtWidgets.QPushButton):
    def __init__(self, icon_name, color, diameter=32, parent=None):
        super(CircularButton, self).__init__(parent)

        self.setMaximumSize(QtCore.QSize(diameter, diameter))
        self.setMinimumSize(QtCore.QSize(diameter, diameter))

        self.setIcon(MaterialIconWidget(icon_name, color=color).icon)

        self.setStyleSheet(
            '''
            color: {};
            {}
            '''.format(
                color, self.get_border_style(color)
            )
        )

    def get_border_style(self, color):
        return '''
            border: 1px solid {};
            border-radius: 16px;
        '''.format(
            color
        )
