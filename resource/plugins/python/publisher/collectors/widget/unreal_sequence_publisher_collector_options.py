# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
from functools import partial

import unreal

from Qt import QtWidgets

import ftrack_api

from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget
from ftrack_connect_pipeline_qt.ui.utility.widget import dialog
from ftrack_connect_pipeline_unreal import plugin
from ftrack_connect_pipeline_unreal import utils as unreal_utils


class UnrealSequencePublisherCollectorOptionsWidget(BaseOptionsWidget):
    '''Unreal sequence collector widget plugin'''

    # Run fetch function on widget initialization
    auto_fetch_on_init = True

    @property
    def image_sequence(self):
        '''Return True if the collector should collect image sequences, False if it should collect reviewable/movie.'''
        return self.options.get('image_sequence', True) is True

    @property
    def media_path(self):
        '''Return the media path from options'''
        result = self.options.get('media_path')
        if result:
            result = result.strip()
            if len(result) == 0:
                result = None
        return result

    @media_path.setter
    def media_path(self, media_path):
        '''Store *media_path* in options and update widgets'''
        if media_path is not None and len(media_path) > 0:
            self.set_option_result(media_path, 'media_path')
            # Remember last used path
            key = '{}_media_path'.format(
                'image_sequence' if self.image_sequence else 'movie'
            )
            unreal_utils.update_project_settings({key: media_path})
        else:
            media_path = '<please choose a {}>'.format(
                'image sequence' if self.image_sequence else 'movie'
            )
            self.set_option_result(None, 'media_path')

        # Update UI
        self._media_path_le.setText(media_path)
        self._media_path_le.setToolTip(media_path)

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
        '''Store *render_path* in options and update widgets'''
        if render_path is not None and len(render_path) > 0:
            self.set_option_result(render_path, 'render_path')
            # Remember last used path
            key = '{}_render_path'.format(
                'image_sequence' if self.image_sequence else 'movie'
            )
            unreal_utils.update_project_settings({key: render_path})
        else:
            render_path = '<please choose>'
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
        super(UnrealSequencePublisherCollectorOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

    def add_sequences(self):
        '''Add Unreal level sequence names to the widget.'''
        self._sequences_cb.clear()
        if not self.unreal_sequences:
            self._sequences_cb.setDisabled(True)
            self._sequences_cb.addItem(
                'No suitable level sequences found, please add to level.'
            )
        else:
            self._sequences_cb.setDisabled(False)
            for index, data in enumerate(self.unreal_sequences):
                self._sequences_cb.addItem(data['value'])
                if data.get('default') is True:
                    self._sequences_cb.setCurrentIndex(index)

    def build(self):
        '''Build the options widget'''
        super(UnrealSequencePublisherCollectorOptionsWidget, self).build()

        bg = QtWidgets.QButtonGroup(self)

        self._pickup_rb = QtWidgets.QRadioButton(
            'Pick up rendered {}:'.format(
                'image sequence' if self.image_sequence else 'movie'
            )
        )
        bg.addButton(self._pickup_rb)
        self.layout().addWidget(self._pickup_rb)

        self._browse_media_path_widget = QtWidgets.QWidget()
        self._browse_media_path_widget.setLayout(QtWidgets.QHBoxLayout())
        self._browse_media_path_widget.layout().setContentsMargins(0, 0, 0, 0)
        self._browse_media_path_widget.layout().setSpacing(0)

        self._media_path_le = QtWidgets.QLineEdit()
        self._media_path_le.setReadOnly(True)

        self._browse_media_path_widget.layout().addWidget(
            self._media_path_le, 20
        )

        self._browse_media_path_btn = QtWidgets.QPushButton('BROWSE')
        self._browse_media_path_btn.setObjectName('borderless')

        self._browse_media_path_widget.layout().addWidget(
            self._browse_media_path_btn
        )
        self.layout().addWidget(self._browse_media_path_widget)

        # Use previous value if available
        path = self.media_path
        if path is None or len(path) == 0:
            key = '{}_media_path'.format(
                'image_sequence' if self.image_sequence else 'movie'
            )
            path = unreal_utils.get_project_settings().get(key)
        self.media_path = path

        self._render_rb = QtWidgets.QRadioButton('Render from level sequence:')
        bg.addButton(self._render_rb)
        self.layout().addWidget(self._render_rb)

        self._render_widget = QtWidgets.QWidget()
        self._render_widget.setLayout(QtWidgets.QVBoxLayout())
        self._render_widget.layout().setContentsMargins(0, 0, 0, 0)
        self._render_widget.layout().setSpacing(0)

        self._sequences_cb = QtWidgets.QComboBox()
        self._sequences_cb.setToolTip(self.description)
        self._render_widget.layout().addWidget(self._sequences_cb)

        self._browse_render_path_widget = QtWidgets.QWidget()
        self._browse_render_path_widget.setLayout(QtWidgets.QHBoxLayout())
        self._browse_render_path_widget.layout().setContentsMargins(0, 0, 0, 0)
        self._browse_render_path_widget.layout().setSpacing(0)

        self._browse_render_path_widget.layout().addWidget(
            QtWidgets.QLabel('Render folder:')
        )

        self._render_path_le = QtWidgets.QLineEdit()
        self._render_path_le.setReadOnly(True)

        self._browse_render_path_widget.layout().addWidget(
            self._render_path_le, 20
        )

        self._browse_render_path_btn = QtWidgets.QPushButton('BROWSE')
        self._browse_render_path_btn.setObjectName('borderless')

        self._browse_render_path_widget.layout().addWidget(
            self._browse_render_path_btn
        )
        self._render_widget.layout().addWidget(self._browse_render_path_widget)

        # Use previous value if available
        path = self.render_path
        if path is None or len(path) == 0:
            key = '{}_render_path'.format(
                'image_sequence' if self.image_sequence else 'movie'
            )
            path = unreal_utils.get_project_settings().get(key)
        self.render_path = path

        self.layout().addWidget(self._render_widget)

        if self.options.get('level_sequence_name'):
            self.unreal_sequences.append(
                {'value': self.options.get('level_sequence_name')}
            )

        self.add_sequences()

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
        super(UnrealSequencePublisherCollectorOptionsWidget, self).post_build()

        self._browse_media_path_btn.clicked.connect(
            self._show_media_path_dialog
        )

        self._browse_render_path_btn.clicked.connect(
            self._show_render_path_dialog
        )
        update_fn = partial(self.set_option_result, key='level_sequence_name')
        self._sequences_cb.currentTextChanged.connect(update_fn)
        if self.unreal_sequences:
            self.set_option_result(
                self._sequences_cb.currentText(), key='level_sequence_name'
            )

        self._render_rb.clicked.connect(self._update_render_mode)
        self._pickup_rb.clicked.connect(self._update_render_mode)
        self._update_render_mode()

    def _update_render_mode(self):
        '''Update widget based on selected render mode'''
        mode = 'pickup'
        if self._render_rb.isChecked():
            mode = 'render'
        self.set_option_result(mode, 'mode')

        self._browse_media_path_widget.setVisible(mode == 'pickup')
        self._render_widget.setVisible(mode == 'render')

        self.report_input()

    def on_fetch_callback(self, result):
        '''This function is called by the _set_internal_run_result function of
        the BaseOptionsWidget'''
        self.unreal_sequences = result
        self.add_sequences()

    def _show_media_path_dialog(self):
        '''Shows the file dialog for choosing media path'''
        if self.image_sequence:
            self._show_image_sequence_dialog()
        else:
            self._show_movie_dialog()

    def _show_image_sequence_dialog(self):
        '''Shows the file dialog for image sequences'''
        if self.media_path is None:
            start_dir = os.path.realpath(
                os.path.join(
                    unreal.SystemLibrary.get_project_saved_directory(),
                    "VideoCaptures",
                )
            )
        else:
            start_dir = os.path.dirname(self._media_path_le.text())

        media_path = QtWidgets.QFileDialog.getExistingDirectory(
            caption='Choose directory containing rendered image sequence',
            dir=start_dir,
            options=QtWidgets.QFileDialog.ShowDirsOnly,
        )

        if not media_path:
            return

        media_path = os.path.normpath(media_path)

        image_sequence_path = unreal_utils.find_image_sequence(media_path)

        if not image_sequence_path:
            dialog.ModalDialog(
                None,
                title='Locate rendered image sequence',
                message='An image sequence on the form "prefix.NNNN.ext" were not found in: {}!'.format(
                    media_path
                ),
            )

        self.media_path = image_sequence_path

        self.report_input()

    def _show_movie_dialog(self):
        '''Shows the file dialog to select a movie'''

        if self.media_path is None:
            start_dir = os.path.realpath(
                os.path.join(
                    unreal.SystemLibrary.get_project_saved_directory(),
                    "VideoCaptures",
                )
            )
        else:
            start_dir = os.path.dirname(self._media_path_le.text())

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

        self.media_path = os.path.normpath(movie_path)

        self.report_input()

    def _show_render_path_dialog(self):
        '''Show the file dialog to select a render path'''
        if self.render_path is None:
            start_dir = os.path.realpath(
                os.path.join(
                    unreal.SystemLibrary.get_project_saved_directory(),
                    "VideoCaptures",
                )
            )
        else:
            start_dir = os.path.dirname(self._render_path_le.text())

        render_path = QtWidgets.QFileDialog.getExistingDirectory(
            caption='Choose render output directory',
            dir=start_dir,
            options=QtWidgets.QFileDialog.ShowDirsOnly,
        )

        if not render_path:
            return

        self.render_path = os.path.normpath(render_path)

    def report_input(self):
        '''(Override) Amount of collected objects has changed, notify parent(s)'''
        status = False
        if self._pickup_rb.isChecked():
            num_objects = (
                1
                if self.media_path is not None and len(self.media_path) > 0
                else 0
            )
            if num_objects > 0:
                message = '1 {} selected'.format(
                    'image sequence' if self.image_sequence else 'movie'
                )
                status = True
            else:
                message = 'No media selected!'
        else:
            num_objects = 1 if self._sequences_cb.isEnabled() else 0
            if num_objects > 0:
                message = '1 level sequence selected'
                status = True
            else:
                message = 'No level sequence selected!'
        self.inputChanged.emit(
            {
                'status': status,
                'message': message,
            }
        )


class UnrealSequencePublisherCollectorPluginWidget(
    plugin.UnrealPublisherCollectorPluginWidget
):
    plugin_name = 'unreal_sequence_publisher_collector'
    widget = UnrealSequencePublisherCollectorOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = UnrealSequencePublisherCollectorPluginWidget(api_object)
    plugin.register()
