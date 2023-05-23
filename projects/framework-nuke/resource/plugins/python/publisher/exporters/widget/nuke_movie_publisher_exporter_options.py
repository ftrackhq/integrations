# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
from functools import partial

from Qt import QtWidgets

import nuke

import ftrack_api


from ftrack_framework_nuke import plugin
from ftrack_framework_qt.plugin.widget import BaseOptionsWidget
from ftrack_framework_qt.ui.utility.widget import group_box


class NukeMoviePublisherExporterOptionsWidget(BaseOptionsWidget):
    '''Nuke movie publisher options user input plugin widget'''

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
        super(NukeMoviePublisherExporterOptionsWidget, self).__init__(
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
        super(NukeMoviePublisherExporterOptionsWidget, self).build()

        frames_option = {
            'start_frame': nuke.root()['first_frame'].value(),
            'end_frame': nuke.root()['last_frame'].value(),
        }
        self.file_formats = self.options.get('supported_file_formats', ['mov'])
        self.default_file_format = self.options.get('file_format')

        self.option_group = group_box.GroupBox('Movie render options')
        self.option_group.setToolTip(self.description)
        options_v_lay = QtWidgets.QVBoxLayout()
        self.option_group.setLayout(options_v_lay)

        img_format_lay = QtWidgets.QHBoxLayout()

        file_format_text = QtWidgets.QLabel("File format")
        self.file_format_cb = QtWidgets.QComboBox()
        self.file_format_cb.addItems(self.file_formats)

        img_format_lay.addWidget(file_format_text)
        img_format_lay.addWidget(self.file_format_cb)

        img_codec_lay = QtWidgets.QHBoxLayout()

        codec_text = QtWidgets.QLabel("Codec")
        self.codec_cb = QtWidgets.QComboBox()

        img_codec_lay.addWidget(codec_text)
        img_codec_lay.addWidget(self.codec_cb)

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

        options_v_lay.addLayout(img_format_lay)
        options_v_lay.addLayout(img_codec_lay)
        options_v_lay.addLayout(range_v_lay)
        self.layout().addWidget(self.option_group)

    def on_file_format_update(self, file_format):
        '''File format *file_format* has been chosen by user'''
        self.set_option_result(file_format, key='file_format')
        # Rebuild codecs
        self.codec_cb.clear()
        index = 0
        default_codec = self.options.get('codec', 'mp4v')
        codecs = self.options.get(file_format, {}).get('codecs')
        if not codecs:
            codecs = [default_codec]
        for codec in codecs:
            self.codec_cb.addItem(codec)
            if (
                default_codec
                and codec.lower().find(default_codec.lower()) > -1
            ):
                self.codec_cb.setCurrentIndex(index)
            index += 1

        self.set_option_result(self.codec_cb.currentText(), 'codec')

    def on_codec_update(self, codec_label):
        '''Movie codec *codec_label* has been chosen by user'''
        codec_knob_name = self.options.get(
            self.file_format_cb.currentText(), {}
        ).get('codec_knob_name')
        if codec_knob_name:
            self.options[self.file_format_cb.currentText()][
                codec_knob_name
            ] = codec_label.split('|')[0]

    def post_build(self):
        super(NukeMoviePublisherExporterOptionsWidget, self).post_build()

        self.file_format_cb.currentTextChanged.connect(
            self.on_file_format_update
        )
        self.codec_cb.currentTextChanged.connect(self.on_codec_update)
        if self.default_file_format:
            index = self.file_format_cb.findText(self.default_file_format)
            if index:
                self.nodes_cb.setCurrentIndex(index)
        self.set_option_result(
            self.file_format_cb.currentText(), 'file_format'
        )
        self.on_file_format_update(self.file_format_cb.currentText())

        update_fn = partial(self.set_option_result, key='start_frame')
        self.stf_text_edit.textChanged.connect(update_fn)
        self.set_option_result(self.stf_text_edit.text(), 'start_frame')

        update_fn = partial(self.set_option_result, key='end_frame')
        self.enf_text_edit.textChanged.connect(update_fn)
        self.set_option_result(self.enf_text_edit.text(), 'end_frame')


class NukeMoviePublisherExporterOptionsPluginWidget(
    plugin.NukePublisherExporterPluginWidget
):
    plugin_name = 'nuke_movie_publisher_exporter'
    widget = NukeMoviePublisherExporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeMoviePublisherExporterOptionsPluginWidget(api_object)
    plugin.register()
