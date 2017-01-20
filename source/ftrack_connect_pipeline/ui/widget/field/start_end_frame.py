# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import sys

from ftrack_connect_pipeline.ui.widget.field.base import BaseField

from QtExt import QtWidgets


class StartEndFrameField(BaseField):
    '''Start and end frame fields.'''

    def __init__(self, start_frame, end_frame):
        '''Instantiate start and end frame field.'''
        super(StartEndFrameField, self).__init__()
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.start_frame = QtWidgets.QDoubleSpinBox()
        self.start_frame.setValue(start_frame)
        self.start_frame.setMaximum(sys.maxint)
        self.start_frame.setDecimals(0)
        self.start_frame.valueChanged.connect(self.notify_changed)

        self.end_frame = QtWidgets.QDoubleSpinBox()
        self.end_frame.setValue(end_frame)
        self.end_frame.setMaximum(sys.maxint)
        self.end_frame.setDecimals(0)
        self.end_frame.valueChanged.connect(self.notify_changed)

        self.layout().addWidget(QtWidgets.QLabel('Frame Range'))
        self.layout().addWidget(self.start_frame)
        self.layout().addWidget(self.end_frame)

    def notify_changed(self, *args, **kwargs):
        '''Notify the world about the changes.'''
        self.value_changed.emit(self.value())

    def value(self):
        '''Return value.'''
        return {
            'start_frame': int(self.start_frame.value()),
            'end_frame': int(self.end_frame.value())
        }
