# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
from ftrack_connect_pipeline import utils as core_utils

import nuke

from Qt import QtWidgets

import ftrack_api

from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget
from ftrack_connect_pipeline_qt.ui.utility.widget import dialog
from ftrack_connect_pipeline_nuke import plugin


class NukeSequencePublisherCollectorOptionsWidget(BaseOptionsWidget):
    '''Nuke image sequence collector widget plugin'''

    # Run fetch nodes function on widget initialization
    auto_fetch_on_init = True

    @property
    def image_sequence_path(self):
        '''Return the media path from options'''
        result = self.options.get('image_sequence_path')
        if result:
            result = result.strip()
            if len(result) == 0:
                result = None
        return result

    @image_sequence_path.setter
    def image_sequence_path(self, image_sequence_path):
        '''Store *image_sequence_path* in options and update widgets'''
        if image_sequence_path:
            self.set_option_result(image_sequence_path, 'image_sequence_path')
        else:
            image_sequence_path = '<please choose a image sequence>'
            self.set_option_result(None, 'image_sequence_path')

        # Update UI
        self._image_sequence_path_le.setText(image_sequence_path)
        self._image_sequence_path_le.setToolTip(image_sequence_path)

    @property
    def node_names(self):
        '''Return the list node names'''
        return self._node_names

    @node_names.setter
    def node_names(self, node_names):
        '''Store *node_names* in options and update widgets'''
        self._node_names = node_names
        if self.node_names:
            self._nodes_cb.setDisabled(False)
        else:
            self._nodes_cb.setDisabled(True)
        self._nodes_cb.clear()
        self._nodes_cb.addItems(self.node_names)
        # Check for file path on nodes
        node_file_path = first = last = is_movie = None
        for node_name in self.node_names:
            node = nuke.toNode(node_name)
            if node.knob('file') and node.knob('first') and node.knob('last'):
                node_file_path = node.knob('file').value()
                if os.path.splitext(node_file_path.lower())[-1] in [
                    '.mov',
                    '.mxf',
                    '.avi',
                    '.r3d',
                ]:
                    is_movie = True
                else:
                    is_movie = False
                first = node.knob('first').value()
                last = node.knob('last').value()
                break
        if node_file_path and not is_movie:
            full_path = '{} [{}-{}]'.format(node_file_path, first, last)
            self.image_sequence_path = full_path

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
        self._node_names = []
        super(NukeSequencePublisherCollectorOptionsWidget, self).__init__(
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
        '''Build the collector widget'''
        super(NukeSequencePublisherCollectorOptionsWidget, self).build()

        bg = QtWidgets.QButtonGroup(self)

        # Render section

        self._render_rb = QtWidgets.QRadioButton(
            'Render image sequence from script'
        )
        bg.addButton(self._render_rb)
        self.layout().addWidget(self._render_rb)

        self._render_widget = QtWidgets.QWidget()
        self._render_widget.setLayout(QtWidgets.QVBoxLayout())
        self._render_widget.layout().setContentsMargins(15, 0, 0, 0)
        self._render_widget.layout().setSpacing(2)

        bg2 = QtWidgets.QButtonGroup(self)

        self._render_create_write_rb = QtWidgets.QRadioButton(
            'Create write node at selected node:'
        )
        bg2.addButton(self._render_create_write_rb)
        self._render_widget.layout().addWidget(self._render_create_write_rb)

        self._render_selected_rb = QtWidgets.QRadioButton(
            'Render selected node:'
        )
        bg2.addButton(self._render_selected_rb)
        self._render_widget.layout().addWidget(self._render_selected_rb)

        self._nodes_cb = QtWidgets.QComboBox()
        self._render_widget.layout().addWidget(self._nodes_cb)

        self._render_warning = QtWidgets.QLabel()
        self._render_warning.setVisible(False)
        self._render_widget.layout().addWidget(self._render_warning)

        self.layout().addWidget(self._render_widget)

        # Pick up already rendered media
        self._pickup_rb = QtWidgets.QRadioButton(
            'Pick up rendered image sequence:'
        )
        bg.addButton(self._pickup_rb)
        self.layout().addWidget(self._pickup_rb)

        self._browse_image_sequence_path_widget = QtWidgets.QWidget()
        self._browse_image_sequence_path_widget.setLayout(
            QtWidgets.QHBoxLayout()
        )
        self._browse_image_sequence_path_widget.layout().setContentsMargins(
            15, 0, 0, 0
        )
        self._browse_image_sequence_path_widget.layout().setSpacing(0)

        self._image_sequence_path_le = QtWidgets.QLineEdit()

        self._browse_image_sequence_path_widget.layout().addWidget(
            self._image_sequence_path_le, 20
        )

        self._browse_image_sequence_path_btn = QtWidgets.QPushButton('BROWSE')
        self._browse_image_sequence_path_btn.setObjectName('borderless')

        self._browse_image_sequence_path_widget.layout().addWidget(
            self._browse_image_sequence_path_btn
        )
        self.layout().addWidget(self._browse_image_sequence_path_widget)

        # Use supplied value from definition if available
        if self.options.get('image_sequence_path'):
            self.image_sequence_path = self.options['image_sequence_path']

        if 'mode' not in self.options:
            self.set_option_result(
                'render_create_write', 'mode'
            )  # Set default mode
        mode = self.options['mode'].lower()
        if mode == 'pickup':
            self._pickup_rb.setChecked(True)
            self._render_create_write_rb.setChecked(True)
        else:
            self._render_rb.setChecked(True)
            if mode == 'render_create_write':
                self._render_create_write_rb.setChecked(True)
            elif mode == 'render_selected':
                self._render_selected_rb.setChecked(True)
            else:
                # Fall back to create write
                self._render_create_write_rb.setChecked(True)

        self.report_input()

    def _on_node_selected(self, node_name):
        '''Callback when node is selected in the combo box.'''
        self._render_warning.setVisible(False)
        if not node_name:
            if 'node_name' in self.options:
                del self.options['node_name']
            return
        self.set_option_result(node_name, 'node_name')
        # Validate node selection against current mode, display warning
        if (
            self._render_rb.isChecked()
            and self._render_selected_rb.isChecked()
        ):
            input_node = nuke.toNode(node_name)
            if input_node.Class() != 'Write':
                self._render_warning.setVisible(True)
                self._render_warning.setText(
                    '<html><i style="color:red">The selected node is not a write node!</i></html>'
                )
            else:
                # Check file format
                file_path = input_node['file'].value()
                writing_movie = os.path.splitext(file_path.lower())[-1] in [
                    '.mov',
                    '.mxf',
                    '.avi',
                    '.r3d',
                ]
                if writing_movie:
                    self._render_warning.setVisible(True)
                    self._render_warning.setText(
                        '<html><i style="color:red">The selected write node is writing a movie!</i></html>'
                    )

    def _update_render_mode(self):
        '''Update widget based on selected render mode'''
        mode = None
        if self._pickup_rb.isChecked():
            mode = 'pickup'
        elif self._render_create_write_rb.isChecked():
            mode = 'render_create_write'
        elif self._render_selected_rb.isChecked():
            mode = 'render_selected'
        self.set_option_result(mode, 'mode')

        self._render_widget.setVisible(
            mode in ['render_create_write', 'render_selected']
        )
        self._browse_image_sequence_path_widget.setVisible(mode == 'pickup')
        self._on_node_selected(self.options.get('node_name'))

        self.report_input()

    def post_build(self):
        super(NukeSequencePublisherCollectorOptionsWidget, self).post_build()

        self._nodes_cb.currentTextChanged.connect(self._on_node_selected)
        if self.node_names:
            self._on_node_selected(self._nodes_cb.currentText())

        self._render_rb.clicked.connect(self._update_render_mode)
        self._render_create_write_rb.clicked.connect(self._update_render_mode)
        self._render_selected_rb.clicked.connect(self._update_render_mode)

        self._pickup_rb.clicked.connect(self._update_render_mode)

        self._browse_image_sequence_path_btn.clicked.connect(
            self._show_image_sequence_dialog
        )

        self._update_render_mode()

    def on_fetch_callback(self, result):
        '''This function is called by the _set_internal_run_result function of
        the BaseOptionsWidget'''
        self.node_names = result

    def _show_image_sequence_dialog(self):
        '''Shows the file dialog for image sequences'''
        start_dir = None
        if self.image_sequence_path:
            start_dir = os.path.dirname(self._image_sequence_path_le.text())
        (
            file_path,
            unused_selected_filter,
        ) = QtWidgets.QFileDialog.getOpenFileName(
            caption='Choose image sequence',
            dir=start_dir,
            filter='Images (*.cin *.dng *.dpx *.dtex *.gif *.bmp *.float *.pcx '
            '*.png *.psd *.tga *.jpeg *.jpg *.exr *.dds *.hdr *.hdri *.cgi '
            '*.tif *.tiff *.tga *.targa *.yuv);;All files (*)',
        )

        if not file_path:
            return

        file_path = os.path.normpath(file_path)

        image_sequence_path = core_utils.find_image_sequence(file_path)

        if not image_sequence_path:
            dialog.ModalDialog(
                None,
                title='Locate image sequence',
                message='An image sequence on the form "prefix.NNNN.ext" were not '
                'found at {}!'.format(file_path),
            )

        self.image_sequence_path = image_sequence_path
        self.report_input()

    def report_input(self):
        '''(Override) Amount of collected objects has changed, notify parent(s)'''
        status = False
        if self._render_rb.isChecked():
            if self._nodes_cb.isEnabled() and self._nodes_cb.count() > 0:
                message = '1 script node selected'
                status = True
            else:
                message = 'No script node selected!'
        else:
            if self.image_sequence_path:
                message = '1 image sequence selected'
                status = True
            else:
                message = 'No image sequence selected'

        self.inputChanged.emit(
            {
                'status': status,
                'message': message,
            }
        )


class NukeSequencePublisherCollectorPluginWidget(
    plugin.NukePublisherCollectorPluginWidget
):
    plugin_name = 'nuke_sequence_publisher_collector'
    widget = NukeSequencePublisherCollectorOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeSequencePublisherCollectorPluginWidget(api_object)
    plugin.register()
