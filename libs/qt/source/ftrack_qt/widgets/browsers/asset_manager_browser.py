# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_qt.widgets.accordion import AccordionBaseWidget


class AssetmManagerBrowser(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(AssetmManagerBrowser, self).__init__(parent=parent)

