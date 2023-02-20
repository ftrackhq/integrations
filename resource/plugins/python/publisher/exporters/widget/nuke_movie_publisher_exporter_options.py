# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
from functools import partial

from Qt import QtWidgets

import nuke

import ftrack_api


from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget
from ftrack_connect_pipeline_qt.ui.utility.widget import group_box


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

        bg = QtWidgets.QButtonGroup(self)
        self.render_rb = QtWidgets.QRadioButton(
            'Render movie from script - create write'
        )
        bg.addButton(self.render_rb)
        self.layout().addWidget(self.render_rb)

        frames_option = {
            'start_frame': nuke.root()['first_frame'].value(),
            'end_frame': nuke.root()['last_frame'].value(),
        }
        self.file_formats = self.options.get(
            'supported_file_formats', ['mov', 'mxf']
        )
        self.default_file_format = self.options.get('file_format')

        self.option_group = group_box.GroupBox('Movie options')
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

        self.render_write_rb = QtWidgets.QRadioButton(
            'Render movie from selected write node'
        )
        bg.addButton(self.render_write_rb)
        self.layout().addWidget(self.render_write_rb)

        self.render_write_note = QtWidgets.QLabel(
            '<html><i>Make sure you selected a write node that is setup to render a movie.</i></html>'
        )
        self.layout().addWidget(self.render_write_note)
        self.render_write_note.setVisible(False)

        self.render_from_sequence_rb = QtWidgets.QRadioButton(
            'Render movie from existing rendered sequence write/read node'
        )
        bg.addButton(self.render_from_sequence_rb)
        self.layout().addWidget(self.render_from_sequence_rb)

        self.render_from_sequence_note = QtWidgets.QLabel(
            '<html><i>Make sure you select a write/read node pointing to a rendered sequence.</i></html>'
        )
        self.layout().addWidget(self.render_from_sequence_note)
        self.render_from_sequence_note.setVisible(False)

        self.pickup_rb = QtWidgets.QRadioButton(
            'Pick up existing movie from selected write/read node'
        )
        bg.addButton(self.pickup_rb)
        self.layout().addWidget(self.pickup_rb)

        self.pickup_note = QtWidgets.QLabel(
            '<html><i>Make sure you select a write/read node pointing to a rendered movie.</i></html>'
        )
        self.pickup_note.setVisible(False)
        self.layout().addWidget(self.pickup_note)

        if not 'mode' in self.options:
            self.set_option_result('render', 'mode')
        mode = self.options['mode'].lower()
        if mode == 'render_write':
            self.render_write_rb.setChecked(True)
        elif mode == 'render_from_sequence':
            self.pickup_rb.setChecked(True)
        elif mode == 'pickup':
            self.render_from_sequence_rb.setChecked(True)
        else:
            self.render_rb.setChecked(True)

    def on_file_format_update(self, file_format):
        '''File format *file_format* has been chosen by user'''
        self.set_option_result(file_format, key='file_format')
        # Rebuild codecs
        codec_knob_name = self.options.get(
            self.file_format_cb.currentText(), {}
        ).get('codec_knob_name')
        if codec_knob_name:
            default_codec = self.options.get(file_format, {}).get(
                codec_knob_name
            )
        self.codec_cb.clear()
        index = 0
        for codec in self.options.get(file_format, {}).get('codecs'):
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

        self.render_rb.clicked.connect(self._update_render_mode)
        self.render_write_rb.clicked.connect(self._update_render_mode)
        self.render_from_sequence_rb.clicked.connect(self._update_render_mode)
        self.pickup_rb.clicked.connect(self._update_render_mode)

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

    def _update_render_mode(self):
        value = 'render'
        if self.render_write_rb.isChecked():
            value = 'render_write'
        elif self.render_from_sequence_rb.isChecked():
            value = 'render_from_sequence'
        elif self.pickup_rb.isChecked():
            value = 'pickup'
        self.set_option_result(value, 'mode')
        self.render_from_sequence_note.setVisible(
            self.render_from_sequence_rb.isChecked()
        )
        self.render_write_note.setVisible(self.render_write_rb.isChecked())
        self.pickup_note.setVisible(self.pickup_rb.isChecked())


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
