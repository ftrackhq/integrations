# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

import nuke

import ftrack_api

from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    radio_button_group,
    browse_widget,
    node_combo_box,
    file_dialog,
)
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
            report_status = True
            report_message = '1 movie selected'
        else:
            movie_path = '<please choose a movie>'
            self.set_option_result(None, 'movie_path')
            report_status = False
            report_message = 'No movie selected'

        # Update UI
        self._browse_widget.set_path(movie_path)
        self._browse_widget.set_tool_tip(movie_path)

        self.inputChanged.emit(
            {
                'status': report_status,
                'message': report_message,
            }
        )

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
            report_status = True
            report_message = '1 image sequence selected'
        else:
            image_sequence_path = '<please choose a image sequence>'
            self.set_option_result(None, 'image_sequence_path')
            report_status = False
            report_message = 'No image sequence selected'

        # Update UI
        self._browse_image_sequence_widget.set_path(image_sequence_path)
        self._browse_image_sequence_widget.set_tool_tip(image_sequence_path)

        self.inputChanged.emit(
            {
                'status': report_status,
                'message': report_message,
            }
        )

    @property
    def node_names(self):
        '''Return the list node names'''
        return self._node_names

    @node_names.setter
    def node_names(self, node_names):
        '''Store *node_names* in options and update widgets'''
        self._node_names = node_names
        self._nodes_cb.add_items(node_names, self._node_name)
        self._nodes_cb.hide_warning()
        if not node_names:
            self._nodes_cb.show_warning("No selected nodes!")

    @property
    def write_node_names(self):
        '''Return the list renderable write node names'''
        return self._write_node_names

    @write_node_names.setter
    def write_node_names(self, node_names):
        '''Store list of renderable write node *node_names* and update widgets'''
        self._write_node_names = node_names
        self._write_nodes_cb.add_items(node_names, self._node_name)

        self._write_nodes_cb.hide_warning()
        if not node_names:
            self._write_nodes_cb.show_warning("No movie write node selected!")

        node_name = None
        if not self._node_name and self.write_node_names:
            node_name = self.write_node_names[0]

        node_file_path = None
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

        self.rbg = radio_button_group.RadioButtonGroup()
        self._nodes_cb = node_combo_box.NodeComboBox()
        self.rbg.add_button(
            'render_create_write',
            'Create write node at selected node:',
            self._nodes_cb,
        )
        self._write_nodes_cb = node_combo_box.NodeComboBox()
        self.rbg.add_button(
            'render_selected', 'Render selected node:', self._write_nodes_cb
        )
        self._browse_image_sequence_widget = browse_widget.BrowseWidget()
        self.rbg.add_button(
            'render_from_sequence',
            'Render movie from existing image sequence:',
            self._browse_image_sequence_widget,
        )
        self._browse_widget = browse_widget.BrowseWidget()
        self.rbg.add_button(
            'pickup', 'Pick up rendered movie:', self._browse_widget
        )

        self.layout().addWidget(self.rbg)

        # Use supplied value from definition if available
        if self.options.get('movie_path'):
            self.movie_path = self.options['movie_path']

        if 'mode' not in self.options:
            self.set_option_result(
                'render_create_write', 'mode'
            )  # Set default mode

    def post_build(self):
        ''' Connect signals'''
        super(NukeMoviePublisherCollectorOptionsWidget, self).post_build()

        self._nodes_cb.text_changed.connect(self._on_node_selected)
        self._write_nodes_cb.text_changed.connect(self._on_node_selected)

        self._nodes_cb.refresh_clicked.connect(self.refresh_nodes)
        self._write_nodes_cb.refresh_clicked.connect(self.refresh_nodes)

        self.rbg.option_changed.connect(self.set_mode)

        self._browse_widget.browse_button_clicked.connect(
            self._show_movie_dialog
        )

        self._browse_image_sequence_widget.browse_button_clicked.connect(
            self._show_image_sequence_dialog
        )

        self.rbg.set_default(self.options['mode'].lower())

    def refresh_nodes(self):
        ''' Run fetch function '''
        self.on_run_plugin(method="fetch")

    def set_mode(self, mode_name, widget, inner_widget):
        ''' Set up the mode of the widget '''
        self.set_option_result(mode_name, 'mode')
        if inner_widget in [self._nodes_cb, self._write_nodes_cb]:
            self._on_node_selected(inner_widget.get_text())
        else:
            if (
                mode_name == 'render_from_sequence'
                and not self.image_sequence_path
            ):
                report_status = False
                report_message = 'No image sequence selected'
                self.inputChanged.emit(
                    {
                        'status': report_status,
                        'message': report_message,
                    }
                )
            elif mode_name == 'pickup' and not self.movie_path:
                report_status = False
                report_message = 'No movie selected'
                self.inputChanged.emit(
                    {
                        'status': report_status,
                        'message': report_message,
                    }
                )

    def _on_node_selected(self, node_name):
        '''Callback when node is selected in either on of the combo boxes.'''
        if not node_name:
            if 'node_name' in self.options:
                del self.options['node_name']
                report_message = 'No script node selected!'
                report_status = False
                self.inputChanged.emit(
                    {
                        'status': report_status,
                        'message': report_message,
                    }
                )
            return
        self.set_option_result(node_name, 'node_name')
        report_status = True
        report_message = '1 node selected'
        self.inputChanged.emit(
            {
                'status': report_status,
                'message': report_message,
            }
        )

    def on_fetch_callback(self, result):
        '''This function is called by the _set_internal_run_result function of
        the BaseOptionsWidget'''
        self.node_names = result.get('all_nodes', [])
        self.write_node_names = result.get('write_nodes', [])

    def _show_image_sequence_dialog(self):
        '''Shows the file dialog for image sequences'''
        start_dir = None
        if self.image_sequence_path:
            start_dir = os.path.dirname(self._browse_widget.get_path())

        dialog_filter = (
            'Images (*.cin *.dng *.dpx *.dtex *.gif *.bmp *.float *.pcx '
            '*.png *.psd *.tga *.jpeg *.jpg *.exr *.dds *.hdr *.hdri *.cgi '
            '*.tif *.tiff *.tga *.targa *.yuv);;All files (*)'
        )
        dialog_result = file_dialog.ImageSequenceFileDialog(
            start_dir, dialog_filter
        )
        self.image_sequence_path = dialog_result.path

    def _show_movie_dialog(self):
        '''Shows the file dialog to select a movie'''

        start_dir = None
        if self.movie_path:
            start_dir = os.path.dirname(self._movie_path_le.text())

        dialog_filter = 'Movies (*.mov *.r3d *.mxf *.avi);;All files (*)'
        dialog_result = file_dialog.MovieFileDialog(start_dir, dialog_filter)
        self.movie_path = dialog_result.path


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
