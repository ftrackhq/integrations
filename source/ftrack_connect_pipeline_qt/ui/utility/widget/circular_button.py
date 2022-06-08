# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.ui.utility.widget.icon import (
    MaterialIcon,
)


class CircularButton(QtWidgets.QPushButton):
    '''Widget representing a circular button with an outline'''

    def __init__(
        self, icon_name, color=None, diameter=32, variant=None, parent=None
    ):
        '''
        Initialize circular button

        :param icon_name: The material icon name
        :param color: The color, in html #RRGGBB format, or rgba(r,g,b,alpha)
        :param diameter: The circle diameter in pixels
        :param variant: The material icon variant to use (optional)
        :param parent: The parent dialog or frame
        '''
        super(CircularButton, self).__init__(parent)
        self.color = color

        self.setMaximumSize(QtCore.QSize(diameter, diameter))
        self.setMinimumSize(QtCore.QSize(diameter, diameter))

        if color is None:
            color = '#D3D3D3'
            border_color = 'rgba(255, 255, 255, 0.1)'
        else:
            border_color = color

        self.setIcon(MaterialIcon(icon_name, variant=variant, color=color))

        self.setStyleSheet(
            '''
            color: {};
            {}
            '''.format(
                color, self.get_border_style(border_color)
            )
        )

    def get_border_style(self, color):
        return '''
            border: 1px solid {};
            border-radius: 16px;
        '''.format(
            color
        )
