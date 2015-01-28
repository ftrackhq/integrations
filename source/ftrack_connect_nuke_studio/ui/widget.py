# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import hiero
import ftrack
from FnAssetAPI.ui.toolkit import QtGui


class Resolution(hiero.ui.FormatChooser):
    '''Wrap hiero widget for promoted qtDesigner one.'''
    pass


class Fps(QtGui.QComboBox):
    '''Extract fps from hiero and expose them.'''
    def __init__(self, parent=None):
        super(Fps, self).__init__(parent=parent)
        for fps in hiero.core.defaultFrameRates():
            if fps.is_integer():
                self.addItem(str(int(fps)))
            else:
                self.addItem(str(fps))


class Workflow(QtGui.QComboBox):
    '''Expose availble workflows from ftrack's server.'''
    def __init__(self, parent=None):
        super(Workflow, self).__init__(parent=parent)
        self._schema = ftrack.getProjectSchemes()
        for schemata in self._schema:
            self.addItem(schemata.get('name'))
