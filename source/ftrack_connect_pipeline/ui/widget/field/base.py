import abc

from PySide import QtGui, QtCore


class BaseField(QtGui.QWidget):
    '''Base widget to inherit from.'''

    #: Signal to emit on value change.
    value_changed = QtCore.Signal(object)

    @abc.abstractmethod
    def value():
        '''Return value.'''
