# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import hiero
from FnAssetAPI.ui.toolkit import QtGui


class Fps(QtGui.QComboBox):
    '''Extract fps from hiero and expose them.'''
    def __init__(self, parent=None):
        super(Fps, self).__init__(parent=parent)
        for fps in hiero.core.defaultFrameRates():
            if fps.is_integer():
                self.addItem(str(int(fps)))
            else:
                self.addItem(str(fps))
