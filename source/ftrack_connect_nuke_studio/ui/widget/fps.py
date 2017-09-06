# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from QtExt import QtGui, QtCore, QtWidgets

import hiero


class Fps(QtWidgets.QComboBox):
    '''Extract fps from hiero and expose them.'''
    def __init__(self, parent=None, default_value=None):
        super(Fps, self).__init__(parent=parent)
        for fps in hiero.core.defaultFrameRates():
            if fps.is_integer():
                safe_fps = str(int(fps))
            else:
                safe_fps = str(fps)

            self.addItem(safe_fps)

        if default_value:
            index = self.findText(str(default_value))

            if index:
                self.setCurrentIndex(index)

