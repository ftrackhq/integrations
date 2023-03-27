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


class NukeMoviePublisherCollectorOptionsWidget(BaseOptionsWidget):
    '''Nuke sequence collector widget plugin'''

    # Run fetch nodes function on widget initialization
    auto_fetch_on_init = True

    @property
    def movie_path(self):
        '''Return the media path from options'''
        result = self.options.get('movie_path')
        if result:
            result = result.strip()
            if len(result) == 0:
                result = None
        return result

    @movie_path.setter
    def movie_path(self, movie_path):
        '''Store *movie_path* in options and update widgets'''
        if movie_path:
            self.set_option_result(movie_path, 'movie_path')
        else:
            movie_path = '<please choose a movie>'
            self.set_option_result(None, 'movie_path')

        # Update UI
        self._movie_path_le.setText(movie_path)
        self._movie_path_le.setToolTip(movie_path)

    @property
    def image_sequence_path(self):
        '''Return the image sequence path for movie render from options'''
        result = self.options.get('image_sequence_path')
        if result:
            result = result.strip()
            if len(result) == 0:
                result = None
        return result

    @image_sequence_path.setter
    def image_sequence_path(self, image_sequence_path):
        '''Store *image_sequence_path* for movie render in options and update widgets'''
        if image_sequence_path:
            self.set_option_result(image_sequence_path, 'image_sequence_path')
        else:
            image_sequence_path = '<please choose a image sequence>'
            self.set_option_result(None, 'image_sequence_path')

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
        for (index, node_name) in enumerate(self.node_names):
            self._nodes_cb.addItem(node_name)
            if node_name == self._node_name:
                self._nodes_cb.setCurrentIndex(index)

    @property
    def write_node_names(self):
        '''Return the list renderable write node names'''
        return self._write_node_names

    @write_node_names.setter
    def write_node_names(self, node_names):
        '''Store list of renderable write node *node_names* and update widgets'''
        self._write_node_names = node_names
        if self.write_node_names:
            self._write_nodes_cb.setDisabled(False)
        else:
            self._write_nodes_cb.setDisabled(True)

        self._write_nodes_cb.clear()
        for (index, node_name) in enumerate(self.write_node_names):
            self._write_nodes_cb.addItem(node_name)
            if node_name == self._node_name:
                self._write_nodes_cb.setCurrentIndex(index)

        self._render_warning.setVisible(False)
        if len(self.write_node_names) == 0:
            self._render_warning.setVisible(True)
            self._render_warning.setText(
                '<html><i style="color:red">No movie write node selected!</i></html>'
            )

        # Extract a path from the write node
        node_name = self._node_name
        if not node_name and len(self.write_node_names) > 0:
            node_name = self.write_node_names[0]

        if node_name:
            node = nuke.toNode(node_name)
            node_file_path = node.knob('file').value()
            self.movie_path = node_file_path

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
        self._write_node_names = []
        self._node_name = options.get('node_name')
        super(NukeMoviePublisherCollectorOptionsWidget, self).__init__(
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
        super(NukeMoviePublisherCollectorOptionsWidget, self).build()

        bg = QtWidgets.QButtonGroup(self)

        # Render section

        self._render_rb = QtWidgets.QRadioButton('Render movie from script')
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

        self._nodes_cb = QtWidgets.QComboBox()
        self._render_widget.layout().addWidget(self._nodes_cb)

        self._render_selected_rb = QtWidgets.QRadioButton(
            'Render selected node:'
        )
        bg2.addButton(self._render_selected_rb)
        self._render_widget.layout().addWidget(self._render_selected_rb)

        self._write_nodes_cb = QtWidgets.QComboBox()
        self._render_widget.layout().addWidget(self._write_nodes_cb)

        self._render_warning = QtWidgets.QLabel()

        self._render_warning.setVisible(False)
        self._render_widget.layout().addWidget(self._render_warning)

        self.layout().addWidget(self._render_widget)

        # Render from image sequence
        self._render_from_sequence_rb = QtWidgets.QRadioButton(
            'Render movie from existing image sequence:'
        )
        bg.addButton(self._render_from_sequence_rb)
        self.layout().addWidget(self._render_from_sequence_rb)

        self._browse_image_sequence_widget = QtWidgets.QWidget()
        self._browse_image_sequence_widget.setLayout(QtWidgets.QHBoxLayout())
        self._browse_image_sequence_widget.layout().setContentsMargins(
            15, 0, 0, 0
        )
        self._browse_image_sequence_widget.layout().setSpacing(0)

        self._image_sequence_path_le = QtWidgets.QLineEdit()

        self._browse_image_sequence_widget.layout().addWidget(
            self._image_sequence_path_le, 20
        )

        self._browse_image_sequence_path_btn = QtWidgets.QPushButton('BROWSE')
        self._browse_image_sequence_path_btn.setObjectName('borderless')

        self._browse_image_sequence_widget.layout().addWidget(
            self._browse_image_sequence_path_btn
        )
        self.layout().addWidget(self._browse_image_sequence_widget)

        # Pick up already rendered media
        self._pickup_rb = QtWidgets.QRadioButton('Pick up rendered movie:')
        bg.addButton(self._pickup_rb)
        self.layout().addWidget(self._pickup_rb)

        self._browse_movie_widget = QtWidgets.QWidget()
        self._browse_movie_widget.setLayout(QtWidgets.QHBoxLayout())
        self._browse_movie_widget.layout().setContentsMargins(15, 0, 0, 0)
        self._browse_movie_widget.layout().setSpacing(0)

        self._movie_path_le = QtWidgets.QLineEdit()

        self._browse_movie_widget.layout().addWidget(self._movie_path_le, 20)

        self._browse_movie_path_btn = QtWidgets.QPushButton('BROWSE')
        self._browse_movie_path_btn.setObjectName('borderless')

        self._browse_movie_widget.layout().addWidget(
            self._browse_movie_path_btn
        )
        self.layout().addWidget(self._browse_movie_widget)

        # Use supplied value from definition if available
        if len(self.options.get('movie_path') or '') > 0:
            self.movie_path = self.options['movie_path']

        if 'mode' not in self.options:
            self.set_option_result(
                'render_create_write', 'mode'
            )  # Set default mode
        mode = self.options['mode'].lower()
        if mode == 'pickup':
            self._pickup_rb.setChecked(True)
            self._render_create_write_rb.setChecked(True)
        elif mode == 'render_from_sequence':
            self._render_from_sequence_rb.setChecked(True)
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

    def _update_render_mode(self):
        '''Update widget based on selected render mode'''
        mode = None
        if self._pickup_rb.isChecked():
            mode = 'pickup'
        elif self._render_from_sequence_rb.isChecked():
            mode = 'render_from_sequence'
        elif self._render_create_write_rb.isChecked():
            mode = 'render_create_write'
        elif self._render_selected_rb.isChecked():
            mode = 'render_selected'
        self.set_option_result(mode, 'mode')

        self._nodes_cb.setVisible(mode == 'render_create_write')
        self._write_nodes_cb.setVisible(mode == 'render_selected')
        self._render_widget.setVisible(
            mode in ['render_create_write', 'render_selected']
        )
        self._browse_movie_widget.setVisible(mode == 'pickup')
        self._browse_image_sequence_widget.setVisible(
            mode == 'render_from_sequence'
        )
        self._on_node_selected(self.options.get('node_name'))

        self.report_input()

    def post_build(self):
        super(NukeMoviePublisherCollectorOptionsWidget, self).post_build()

        self._nodes_cb.currentTextChanged.connect(self._on_node_selected)
        self._write_nodes_cb.currentTextChanged.connect(self._on_node_selected)

        self._render_rb.clicked.connect(self._update_render_mode)
        self._render_create_write_rb.clicked.connect(self._update_render_mode)
        self._render_selected_rb.clicked.connect(self._update_render_mode)

        self._render_from_sequence_rb.clicked.connect(self._update_render_mode)
        self._browse_image_sequence_path_btn.clicked.connect(
            self._show_image_sequence_dialog
        )

        self._pickup_rb.clicked.connect(self._update_render_mode)

        self._browse_movie_path_btn.clicked.connect(self._show_movie_dialog)

        self._update_render_mode()

    def on_fetch_callback(self, result):
        '''This function is called by the _set_internal_run_result function of
        the BaseOptionsWidget'''
        self.node_names = [
            node_name for (node_name, unused_is_write_node) in result
        ]
        # Evaluate which nodes writes an image sequence
        write_nodes = []
        for (node_name, is_compatible_write_node) in result:
            if is_compatible_write_node:
                write_nodes.append(node_name)
        self.write_node_names = write_nodes

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

    def _show_movie_dialog(self):
        '''Shows the file dialog to select a movie'''

        start_dir = None
        if self.movie_path:
            start_dir = os.path.dirname(self._movie_path_le.text())

        (
            movie_path,
            unused_selected_filter,
        ) = QtWidgets.QFileDialog.getOpenFileName(
            caption='Choose rendered movie file',
            dir=start_dir,
            filter='Movies (*.mov *.r3d *.mxf *.avi);;All files (*)',
        )

        if not movie_path:
            return

        self.movie_path = os.path.normpath(movie_path)

        self.report_input()

    def report_input(self):
        '''(Override) Amount of collected objects has changed, notify parent(s)'''
        status = False
        if self._render_create_write_rb.isChecked():
            if self._nodes_cb.isEnabled():
                message = '1 script node selected'
                status = True
            else:
                message = 'No script node selected!'
        elif self._render_selected_rb.isChecked():
            if (
                self._write_nodes_cb.isEnabled()
                and self._write_nodes_cb.count() > 0
            ):
                message = '1 write node selected'
                status = True
            else:
                message = 'No write node selected!'
        elif self._render_from_sequence_rb.isChecked():
            if self.image_sequence_path:
                message = '1 image sequence selected'
                status = True
            else:
                message = 'No image sequence selected!'
        else:
            if self.movie_path:
                message = '1 movie selected'
                status = True
            else:
                message = 'No movie selected'

        self.inputChanged.emit(
            {
                'status': status,
                'message': message,
            }
        )


class NukeMoviePublisherCollectorPluginWidget(
    plugin.NukePublisherCollectorPluginWidget
):
    plugin_name = 'nuke_movie_publisher_collector'
    widget = NukeMoviePublisherCollectorOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeMoviePublisherCollectorPluginWidget(api_object)
    plugin.register()
