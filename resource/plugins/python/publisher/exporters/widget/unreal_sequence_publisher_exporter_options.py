# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

from Qt import QtWidgets, QtCore, QtGui

import unreal

import ftrack_api

from ftrack_connect_pipeline_qt.plugin.widget.dynamic import DynamicWidget
from ftrack_connect_pipeline_qt.ui.utility.widget import dialog

from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal.utils import (
    sequencer as unreal_sequencer_utils,
)


class UnrealSequencePublisherExporterOptionsWidget(DynamicWidget):
    '''Unreal sequence publisher user input plugin widget'''

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
        super(UnrealSequencePublisherExporterOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

    def define_options(self):
        '''Default renderable options for dynamic widget'''
        return {
            'file_format': [
                {
                    'value': 'exr',
                    'default': True,
                },
                {'value': 'jpg'},
                {'value': 'bmp'},
                {'value': 'png'},
            ],
            'resolution': [
                {'value': '320x240(4:3)'},
                {'value': '640x480(4:3)'},
                {'value': '640x360(16:9)'},
                {
                    'value': '1280x720(16:9)',
                    'default': True,
                },
                {'value': '1920x1080(16:9)'},
                {'value': '3840x2160(16:9)'},
            ],
        }

    def get_options_group_name(self):
        '''Override'''
        return 'Unreal sequence exporter Options'

    def build(self):
        '''build function , mostly used to create the widgets.'''

        # Update current options with the given ones from definitions and store
        self.update(self.define_options())

        bg = QtWidgets.QButtonGroup(self)

        self.pickup_rb = QtWidgets.QRadioButton('Pick up rendered sequence')
        bg.addButton(self.pickup_rb)
        self.layout().addWidget(self.pickup_rb)

        # TODO: Store video capture output folder in Unreal project
        self._choose_folder_widget = QtWidgets.QWidget()
        self._choose_folder_widget.setLayout(QtWidgets.QHBoxLayout())
        self._choose_folder_widget.layout().setContentsMargins(0, 0, 0, 0)
        self._choose_folder_widget.layout().setSpacing(0)

        self._choose_folder_widget.layout().addWidget(
            QtWidgets.QLabel('Capture folder:')
        )

        self._render_folder_input = QtWidgets.QLineEdit(
            '<please choose a folder>'
            if not 'file_path' in self.options
            else self.options['file_path']
        )
        self._render_folder_input.setReadOnly(True)

        self._choose_folder_widget.layout().addWidget(
            self._render_folder_input, 20
        )

        self._browser_button = QtWidgets.QPushButton('BROWSE')
        self._browser_button.setObjectName('borderless')

        self._choose_folder_widget.layout().addWidget(self._browser_button)
        self.layout().addWidget(self._choose_folder_widget)

        self.render_rb = QtWidgets.QRadioButton('Render from sequence')
        bg.addButton(self.render_rb)
        self.layout().addWidget(self.render_rb)

        if not 'mode' in self.options:
            self.set_option_result('pickup', 'mode')  # Set default mode
        mode = self.options['mode'].lower()
        if mode == 'pickup':
            self.pickup_rb.setChecked(True)
        else:
            self.render_rb.setChecked(True)

        # Call the super build to automatically generate the options
        super(UnrealSequencePublisherExporterOptionsWidget, self).build()

    def post_build(self):
        super(UnrealSequencePublisherExporterOptionsWidget, self).post_build()

        self.render_rb.clicked.connect(self._update_render_mode)
        self.pickup_rb.clicked.connect(self._update_render_mode)

        self._update_render_mode()

        self._browser_button.clicked.connect(self._show_file_dialog)

    def _update_render_mode(self):
        mode = 'render'
        if self.pickup_rb.isChecked():
            mode = 'pickup'
        self.set_option_result(mode, 'mode')

        self._choose_folder_widget.setVisible(mode == 'pickup')
        self.option_group.setVisible(mode == 'render')

    def _show_file_dialog(self):
        '''Shows the file dialog'''

        if self._render_folder_input.text() == '<please choose a folder>':
            start_dir = os.path.realpath(
                os.path.join(
                    unreal.SystemLibrary.get_project_saved_directory(),
                    "VideoCaptures",
                )
            )
        else:
            start_dir = os.path.dirname(self._render_folder_input.text())

        path = QtWidgets.QFileDialog.getExistingDirectory(
            caption='Choose directory containing rendered image sequence',
            dir=start_dir,
            options=QtWidgets.QFileDialog.ShowDirsOnly,
        )

        if not path:
            return

        (
            sequence_path,
            first,
            last,
        ) = unreal_sequencer_utils.find_image_sequence(path)

        if sequence_path:
            self._render_folder_input.setText(sequence_path)
            self._render_folder_input.setToolTip(sequence_path)
            self.set_option_result(sequence_path, 'file_path')
            self.set_option_result(first, 'first')
            self.set_option_result(last, 'last')
        else:
            dialog.ModalDialog(
                None,
                title='Locate rendered image sequence',
                message='An image sequence on the form "prefix.NNNN.ext" were not found in: {}!'.format(
                    path
                ),
            )


class UnrealSequencePublisherExporterOptionsPluginWidget(
    plugin.UnrealPublisherExporterPluginWidget
):
    plugin_name = 'unreal_sequence_publisher_exporter'
    widget = UnrealSequencePublisherExporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealSequencePublisherExporterOptionsPluginWidget(api_object)
    plugin.register()
