# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack


from ftrack_connect_pipeline.ui.widget.field.base import BaseField
from ftrack_connect_pipeline.ui.widget import thumbnail_drop_zone

from QtExt import QtWidgets


class ThumbnailField(BaseField):

    def __init__(self):
        '''Initialize widget'''
        super(ThumbnailField, self).__init__()
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.thumbnail = thumbnail_drop_zone.ThumbnailDropZone()
        self.layout().addWidget(self.thumbnail)
        self.thumbnail.updated.connect(self.notify_changed)

    def notify_changed(self, *args, **kwargs):
        '''Notify the world about the changes.'''
        self.value_changed.emit(self.value())

    def value(self):
        '''Return value.'''
        return self.thumbnail.getFilePath()
