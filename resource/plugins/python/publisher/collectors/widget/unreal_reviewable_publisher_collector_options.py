# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

import unreal

from Qt import QtWidgets

import ftrack_api

from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget
from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal import utils as unreal_utils


class UnrealReviewablePublisherCollectorOptionsWidget(BaseOptionsWidget):
    '''Unreal Reviewable collector widget plugin'''

    # Run fetch function on widget initialization
    auto_fetch_on_init = False

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
        if movie_path and len(movie_path) > 0:
            self.set_option_result(movie_path, 'movie_path')
            # Remember last used path
            unreal_utils.update_project_settings({'movie_path': movie_path})
        else:
            movie_path = '<please choose a movie>'
            self.set_option_result(None, 'movie_path')

        # Update UI
        self._movie_path_le.setText(movie_path)
        self._movie_path_le.setToolTip(movie_path)

    @property
    def render_path(self):
        '''Return the render path from options'''

        result = self.options.get('render_path')
        if result:
            result = result.strip()
            if len(result) == 0:
                result = None
        return result

    @render_path.setter
    def render_path(self, render_path):
        '''Store *movie_path* in options and update widgets'''
        if render_path and len(render_path) > 0:
            self.set_option_result(render_path, 'render_path')
        else:
            render_path = '<please choose a image sequence>'
            self.set_option_result(None, 'render_path')

        # Update UI
        self._render_path_le.setText(render_path)
        self._render_path_le.setToolTip(render_path)

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
        self.unreal_sequences = []
        super(UnrealReviewablePublisherCollectorOptionsWidget, self).__init__(
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
        '''Build the options widget'''
        super(UnrealReviewablePublisherCollectorOptionsWidget, self).build()

        bg = QtWidgets.QButtonGroup(self)

        self._pickup_rb = QtWidgets.QRadioButton(
            'Pick up rendered movie:'
        )
        bg.addButton(self._pickup_rb)
        self.layout().addWidget(self._pickup_rb)

        self._browse_movie_path_widget = QtWidgets.QWidget()
        self._browse_movie_path_widget.setLayout(QtWidgets.QHBoxLayout())
        self._browse_movie_path_widget.layout().setContentsMargins(0, 0, 0, 0)
        self._browse_movie_path_widget.layout().setSpacing(0)

        self._movie_path_le = QtWidgets.QLineEdit()
        self._movie_path_le.setReadOnly(True)

        self._browse_movie_path_widget.layout().addWidget(
            self._movie_path_le, 20
        )

        self._browse_movie_path_btn = QtWidgets.QPushButton('BROWSE')
        self._browse_movie_path_btn.setObjectName('borderless')

        self._browse_movie_path_widget.layout().addWidget(
            self._browse_movie_path_btn
        )
        self.layout().addWidget(self._browse_movie_path_widget)

        # Use previous value if available
        path = self.movie_path
        if path is None or len(path) == 0:
            path = unreal_utils.get_project_settings().get('movie_path')
        self.movie_path = path

        self._render_rb = QtWidgets.QRadioButton('Generate from Image sequence')
        bg.addButton(self._render_rb)
        # Deactivating render for now
        # self.layout().addWidget(self._render_rb)

        self._render_widget = QtWidgets.QWidget()
        self._render_widget.setLayout(QtWidgets.QVBoxLayout())
        self._render_widget.layout().setContentsMargins(0, 0, 0, 0)
        self._render_widget.layout().setSpacing(0)

        self._render_path_le = QtWidgets.QLineEdit()
        self._render_path_le.setReadOnly(True)

        self._render_widget.layout().addWidget(self._render_path_le)

        self.render_path = unreal_utils.get_project_settings().get('image_sequence_path')

        # Deactivating render for now
        # self.layout().addWidget(self._render_widget)

        if 'mode' not in self.options:
            self.set_option_result('pickup', 'mode')  # Set default mode
        mode = self.options['mode'].lower()
        if mode == 'render':
            self._render_rb.setChecked(True)
        elif mode == 'pickup':
            self._pickup_rb.setChecked(True)
        else:
            # Fallback to pickup mode
            self._pickup_rb.setChecked(True)
        self.report_input()

    def post_build(self):
        super(UnrealReviewablePublisherCollectorOptionsWidget, self).post_build()

        self._browse_movie_path_btn.clicked.connect(
            self._show_movie_path_dialog
        )

        self._render_rb.clicked.connect(self._update_render_mode)
        self._pickup_rb.clicked.connect(self._update_render_mode)
        self._update_render_mode()

    def _update_render_mode(self):
        '''Update widget based on selected render mode'''
        mode = 'pickup'
        if self._render_rb.isChecked():
            mode = 'render'
            self.set_option_result(None, 'movie_path')
            self.render_path = unreal_utils.get_project_settings().get('image_sequence_path')
        self.set_option_result(mode, 'mode')

        self._browse_movie_path_widget.setVisible(mode == 'pickup')
        self._render_widget.setVisible(mode == 'render')

        self.report_input()

    def _show_movie_path_dialog(self):
        '''Shows the file dialog for choosing media path'''
        self._show_movie_dialog()

    def _show_movie_dialog(self):
        '''Shows the file dialog to select a movie'''

        if not self.movie_path:
            start_dir = os.path.realpath(
                os.path.join(
                    unreal.SystemLibrary.get_project_saved_directory(),
                    "VideoCaptures",
                )
            )
        else:
            start_dir = os.path.dirname(self._movie_path_le.text())

        (
            movie_path,
            unused_selected_filter,
        ) = QtWidgets.QFileDialog.getOpenFileName(
            caption='Choose rendered movie file',
            dir=start_dir,
            filter='Avi files (*.avi);;Movies (*.mov);;All files (*)',
        )

        if not movie_path:
            return

        self.movie_path = os.path.normpath(movie_path)

        self.report_input()

    def report_input(self):
        '''(Override) Amount of collected objects has changed, notify parent(s)'''
        status = False
        if self._pickup_rb.isChecked():
            num_objects = (
                1
                if self.movie_path and len(self.movie_path) > 0
                else 0
            )
            if num_objects > 0:
                message = '1 movie selected'
                status = True
            else:
                message = 'No media selected!'
        else:
            message = 'Generate from image sequence'
            status = True
        self.inputChanged.emit(
            {
                'status': status,
                'message': message,
            }
        )


class UnrealReviewablePublisherCollectorPluginWidget(
    plugin.UnrealPublisherCollectorPluginWidget
):
    plugin_name = 'unreal_reviewable_publisher_collector'
    widget = UnrealReviewablePublisherCollectorOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealReviewablePublisherCollectorPluginWidget(api_object)
    plugin.register()
