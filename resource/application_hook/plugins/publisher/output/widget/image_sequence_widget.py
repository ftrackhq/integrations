
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from functools import partial

from Qt import QtWidgets


from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget

import nuke


class SequenceWidget(BaseOptionsWidget):

    def __init__(
            self, parent=None, session=None, data=None, name=None,
            description=None, options=None, context=None
    ):

        super(SequenceWidget, self).__init__(
            parent=parent,
            session=session, data=data, name=name,
            description=description, options=options,
            context=context
        )

    def build(self):

        super(SequenceWidget, self).build()

        frames_option = {
            'start_frame': 1,
            'end_frame': 10,
        }
        self.file_formats = [
            'exr',
            'jpeg',
            'png',
            'pic',
            'targa',
            'tiff'
        ]
        self.default_file_format = self.options.get('file_format')

        self.option_group = QtWidgets.QGroupBox('Image sequence options')
        self.option_group.setToolTip(self.description)
        options_v_lay = QtWidgets.QVBoxLayout()
        self.option_group.setLayout(options_v_lay)

        img_h_lay = QtWidgets.QHBoxLayout()
        img_format_text = QtWidgets.QLabel("Image format")
        self.img_format_cb = QtWidgets.QComboBox()

        self.img_format_cb.addItems(self.file_formats)
        img_h_lay.addWidget(img_format_text)
        img_h_lay.addWidget(self.img_format_cb)

        range_v_lay = QtWidgets.QVBoxLayout()
        range_h_lay = QtWidgets.QHBoxLayout()
        range_text = QtWidgets.QLabel("Frame range")

        stf_text = QtWidgets.QLabel("From")
        self.stf_text_edit = QtWidgets.QLineEdit(
            str(frames_option['start_frame'])
        )

        enf_text = QtWidgets.QLabel("To")
        self.enf_text_edit = QtWidgets.QLineEdit(
            str(frames_option['end_frame'])
        )

        range_h_lay.addWidget(stf_text)
        range_h_lay.addWidget(self.stf_text_edit)
        range_h_lay.addWidget(enf_text)
        range_h_lay.addWidget(self.enf_text_edit)

        range_v_lay.addWidget(range_text)
        range_v_lay.addLayout(range_h_lay)

        options_v_lay.addLayout(img_h_lay)
        options_v_lay.addLayout(range_v_lay)
        self.layout().addWidget(self.option_group)

    def post_build(self):
        super(SequenceWidget, self).post_build()

        update_fn = partial(self.set_option_result, key='image_format')
        self.img_format_cb.editTextChanged.connect(update_fn)
        if self.default_file_format:
            index = self.img_format_cb.findText(self.default_file_format)
            if index:
                self.nodes_cb.setCurrentIndex(index)
        self.set_option_result(self.img_format_cb.currentText(), 'image_format')

        update_fn = partial(self.set_option_result, key='start_frame')
        self.stf_text_edit.textChanged.connect(update_fn)
        self.set_option_result(self.stf_text_edit.text(), 'start_frame')

        update_fn = partial(self.set_option_result, key='end_frame')
        self.enf_text_edit.textChanged.connect(update_fn)
        self.set_option_result(self.enf_text_edit.text(), 'end_frame')


class ImageSequencePluginWidget(plugin.PublisherOutputNukeWidget):
    plugin_name = 'sequence'
    widget = SequenceWidget


def register(api_object, **kw):
    plugin = ImageSequencePluginWidget(api_object)
    plugin.register()
