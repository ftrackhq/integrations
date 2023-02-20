# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
from functools import partial

import nuke

import ftrack_api


from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_qt.plugin.widgets import BaseOptionsWidget
from ftrack_connect_pipeline_qt.ui.utility.widget import group_box

from Qt import QtWidgets


class NukeSequencePublisherExporterOptionsWidget(BaseOptionsWidget):
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

        bg = QtWidgets.QButtonGroup(self)
        self.render_rb = QtWidgets.QRadioButton(
            'Render sequence from scene - create write'
        )
        bg.addButton(self.render_rb)
        self.layout().addWidget(self.render_rb)

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

        self.option_group = group_box.GroupBox('Image sequence options')
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

        self.render_write_rb = QtWidgets.QRadioButton(
            'Render sequence from selected write node'
        )
        bg.addButton(self.render_write_rb)
        self.layout().addWidget(self.render_write_rb)

        self.render_write_note = QtWidgets.QLabel(
            '<html><i>Make sure you selected a write node that is setup to render a sequence.</i></html>'
        )
        self.layout().addWidget(self.render_write_note)
        self.render_write_note.setVisible(False)

        self.pickup_rb = QtWidgets.QRadioButton(
            'Pick up existing sequence from selected write/read node'
        )
        bg.addButton(self.pickup_rb)
        self.layout().addWidget(self.pickup_rb)

        self.pickup_note = QtWidgets.QLabel(
            '<html><i>Make sure you select a write/read node pointing to a rendered sequence.</i></html>'
        )
        self.layout().addWidget(self.pickup_note)
        self.pickup_note.setVisible(False)

        if not 'mode' in self.options:
            self.set_option_result('render', 'mode')
        mode = self.options['mode'].lower()
        if mode == 'pickup':
            self.pickup_rb.setChecked(True)
        elif mode == 'render_write':
            self.render_write_rb.setChecked(True)
        else:
            self.render_rb.setChecked(True)

    def post_build(self):
        super(NukeSequencePublisherExporterOptionsWidget, self).post_build()

        self.render_rb.clicked.connect(self._update_render_mode)
        self.render_write_rb.clicked.connect(self._update_render_mode)
        self.pickup_rb.clicked.connect(self._update_render_mode)

        def update_fn(index):
            text = self.img_format_cb.itemText(index)
            self.set_option_result(text, 'image_format')

        self.img_format_cb.currentIndexChanged.connect(update_fn)
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

        self._update_render_mode()

    def _update_render_mode(self):
        mode = 'render'
        if self.render_write_rb.isChecked():
            mode = 'render_write'
        elif self.pickup_rb.isChecked():
            mode = 'pickup'
        self.set_option_result(mode, 'mode')
        self.pickup_note.setVisible(self.pickup_rb.isChecked())
        self.render_write_note.setVisible(self.render_write_rb.isChecked())


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
