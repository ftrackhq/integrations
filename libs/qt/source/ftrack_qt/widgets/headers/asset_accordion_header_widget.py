# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.widgets.headers import (
    AccordionHeaderWidget,
)
from ftrack_qt.widgets.info import AssetVersionStatusWidget
from ftrack_qt.widgets.info import ComponentAndVersionWidget


class AssetAccordionHeaderWidget(AccordionHeaderWidget):
    '''Extended header with asset info, for asset accordion'''

    @property
    def path_widget(self):
        return self._path_widget

    @property
    def asset_name_widget(self):
        return self._asset_name_widget

    @property
    def component_and_version_widget(self):
        return self._component_and_version_widget

    @property
    def status_widget(self):
        return self._status_widget

    def __init__(
        self,
        title=None,
        checkable=False,
        checked=True,
        show_checkbox=False,
        collapsable=True,
        collapsed=True,
        parent=None,
    ):
        self._path_widget = None
        self._asset_name_widget = None
        self._component_and_version_widget = None
        self._status_widget = None
        super(AssetAccordionHeaderWidget, self).__init__(
            title=title,
            checkable=checkable,
            checked=checked,
            show_checkbox=show_checkbox,
            collapsable=collapsable,
            collapsed=collapsed,
            parent=parent,
        )

    def build_content(self):
        result = QtWidgets.QWidget()

        '''Build asset widgets and add to the accordion header'''
        content_layout = QtWidgets.QHBoxLayout()
        result.setLayout(content_layout)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(5, 1, 0, 1)
        content_layout.setSpacing(0)

        widget = QtWidgets.QWidget()
        widget.setLayout(QtWidgets.QVBoxLayout())
        widget.layout().setContentsMargins(0, 0, 0, 0)
        widget.layout().setSpacing(2)

        # Add context path, relative to browser context
        self._path_widget = QtWidgets.QLabel()
        self._path_widget.setStyleSheet('font-size: 9px;')
        self._path_widget.setObjectName("gray-dark")

        widget.layout().addWidget(self._path_widget)

        lower_widget = QtWidgets.QWidget()
        lower_widget.setLayout(QtWidgets.QHBoxLayout())
        lower_widget.layout().setContentsMargins(0, 0, 0, 0)
        lower_widget.layout().setSpacing(0)

        self._asset_name_widget = QtWidgets.QLabel()
        self._asset_name_widget.setObjectName('h4')
        lower_widget.layout().addWidget(self._asset_name_widget)
        self._component_and_version_widget = ComponentAndVersionWidget(True)
        lower_widget.layout().addWidget(self._component_and_version_widget)

        delimiter_label = QtWidgets.QLabel(' - ')
        delimiter_label.setObjectName('gray')
        lower_widget.layout().addWidget(delimiter_label)

        self._status_widget = AssetVersionStatusWidget()
        lower_widget.layout().addWidget(self._status_widget)

        lower_widget.layout().addWidget(QtWidgets.QLabel(), 10)

        widget.layout().addWidget(lower_widget)

        content_layout.addWidget(widget)

        return result
