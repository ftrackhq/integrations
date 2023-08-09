# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import shiboken2

from Qt import QtWidgets, QtCore, QtGui

from ftrack_framework_core import constants as core_constants
from ftrack_framework_core.utils import str_version

import ftrack_framework_qt.ui.utility.widget.button
from ftrack_framework_qt.ui.factory.base import BaseUIWidgetObject
from ftrack_framework_qt.ui.utility.widget import overlay, scroll_area
from ftrack_framework_qt import utils
from ftrack_framework_qt.ui.utility.widget.icon import (
    MaterialIconWidget,
)
from ftrack_framework_qt.utils import set_property

class BatchProgressWidget(ProgressWidgetObject):
    '''Progress widget designed for batch processing multiple assets'''

    def __init__(
        self, name, fragment_data, status_view_mode=None, parent=None
    ):
        super(BatchProgressWidget, self).__init__(
            name,
            fragment_data,
            status_view_mode=status_view_mode,
            parent=parent,
        )

    def add_version(self, component):
        version_widget = QtWidgets.QLabel(
            '{} | {}'.format(
                str_version(component['version']).replace('/', ' | '),
                component['name'],
            )
        )
        version_widget.setObjectName('h2')
        self.content_widget.layout().addWidget(version_widget)

    def add_item(self, item):
        item_widget = QtWidgets.QLabel(item)
        item_widget.setObjectName('h2')
        self.content_widget.layout().addWidget(item_widget)
