# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
from functools import partial

import nuke

import ftrack_api


from ftrack_framework_nuke import plugin
from ftrack_framework_qt.plugin.widget import BaseOptionsWidget
from ftrack_framework_qt.ui.utility.widget import group_box

from Qt import QtWidgets


class NukeSequencePublisherExporterOptionsWidget(BaseOptionsWidget):
    '''Nuke image sequence publisher render options user input plugin widget'''

    def __init__(
        self,
        parent=None,
        session=None,
        data=None,
        name=None,
        description=None,
        options=None,
        context_id=None,
        asset_type_name=None,
    ):
        super(NukeSequencePublisherExporterOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

    def build(self):
        super(NukeSequencePublisherExporterOptionsWidget, self).build()

        frames_option = {
            'start_frame': nuke.root()['first_frame'].value(),
            'end_frame': nuke.root()['last_frame'].value(),
        }
        self.file_formats = [
            'exr',
            'jpeg',
            'png',
            'pic',
            'targa',
            'tiff',
            'dpx',
            'dng',
            'sgi',
        ]
        self.default_file_format = self.options.get('file_format') or 'exr'

        self.option_group = group_box.GroupBox('Image sequence render options')
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
        super(NukeSequencePublisherExporterOptionsWidget, self).post_build()

        update_fn = partial(self.set_option_result, key='image_format')
        self.img_format_cb.currentTextChanged.connect(update_fn)
        if self.default_file_format:
            index = self.img_format_cb.findText(self.default_file_format)
            if index:
                self.nodes_cb.setCurrentIndex(index)
        self.set_option_result(
            self.img_format_cb.currentText(), 'image_format'
        )

        update_fn = partial(self.set_option_result, key='start_frame')
        self.stf_text_edit.textChanged.connect(update_fn)
        self.set_option_result(self.stf_text_edit.text(), 'start_frame')

        update_fn = partial(self.set_option_result, key='end_frame')
        self.enf_text_edit.textChanged.connect(update_fn)
        self.set_option_result(self.enf_text_edit.text(), 'end_frame')


class NukeSequencePublisherExporterOptionsPluginWidget(
    plugin.NukePublisherExporterPluginWidget
):
    plugin_name = 'nuke_sequence_publisher_exporter'
    widget = NukeSequencePublisherExporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeSequencePublisherExporterOptionsPluginWidget(api_object)
    plugin.register()
