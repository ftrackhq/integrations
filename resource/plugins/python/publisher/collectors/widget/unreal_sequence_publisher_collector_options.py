# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

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
    auto_fetch_on_init = False

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
        if image_sequence_path and len(image_sequence_path) > 0:
            self.set_option_result(image_sequence_path, 'image_sequence_path')
            # Remember last used path
            unreal_utils.update_project_settings({'image_sequence_path': image_sequence_path})
        else:
            image_sequence_path = '<please choose am image sequence>'
            self.set_option_result(None, 'image_sequence_path')

        # Update UI
        self._img_seq_le.setText(image_sequence_path)
        self._img_seq_le.setToolTip(image_sequence_path)

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

    def build(self):
        '''Build the options widget'''
        super(UnrealSequencePublisherCollectorOptionsWidget, self).build()

        self._pickup_label = QtWidgets.QLabel(
            'Pick up rendered image sequence: '
        )

        self._browse_img_seq_widget = QtWidgets.QWidget()
        self._browse_img_seq_widget.setLayout(QtWidgets.QHBoxLayout())
        self._browse_img_seq_widget.layout().setContentsMargins(0, 0, 0, 0)
        self._browse_img_seq_widget.layout().setSpacing(0)

        self._img_seq_le = QtWidgets.QLineEdit()
        self._img_seq_le.setReadOnly(True)

        self._browse_img_seq_widget.layout().addWidget(
            self._img_seq_le, 20
        )

        self._browse_img_seq_btn = QtWidgets.QPushButton('BROWSE')
        self._browse_img_seq_btn.setObjectName('borderless')

        self._browse_img_seq_widget.layout().addWidget(
            self._browse_img_seq_btn
        )
        self.layout().addWidget(self._browse_img_seq_widget)

        # Use previous value if available
        path = self.image_sequence_path
        if not path or len(path) == 0:
            path = unreal_utils.get_project_settings().get('image_sequence_path')
        self.image_sequence_path = path

        self.report_input()

    def post_build(self):
        super(UnrealSequencePublisherCollectorOptionsWidget, self).post_build()

        self._browse_img_seq_btn.clicked.connect(
            self._show_image_sequence_dialog
        )

    def _show_image_sequence_dialog(self):
        '''Shows the file dialog for image sequences'''
        if not self.image_sequence_path:
            start_dir = os.path.realpath(
                os.path.join(
                    unreal.SystemLibrary.get_project_saved_directory(),
                    "VideoCaptures",
                )
            )
        else:
            start_dir = os.path.dirname(self._img_seq_le.text())

        image_sequence_path = QtWidgets.QFileDialog.getOpenFileName(
            caption='Choose directory containing rendered image sequence',
            dir=start_dir,
            filter="Images (*.bmp *.float *.pcx *.png *.psd *.tga *.jpg *.exr *.dds *.hdr);;All files (*)"
        )

        if not image_sequence_path:
            return

        image_sequence_path = os.path.normpath(image_sequence_path[0])

        image_sequence_path = unreal_utils.find_image_sequence(image_sequence_path)

        if not image_sequence_path:
            dialog.ModalDialog(
                None,
                title='Locate rendered image sequence',
                message='An image sequence on the form "prefix.NNNN.ext" were not found in: {}!'.format(
                    image_sequence_path
                ),
            )

        self.image_sequence_path = image_sequence_path

        self.report_input()

    def report_input(self):
        '''(Override) Amount of collected objects has changed, notify parent(s)'''
        status = False
        num_objects = (
            1
            if self.image_sequence_path and len(self.image_sequence_path) > 0
            else 0
        )
        if num_objects > 0:
            message = '1 image sequence selected'
            status = True
        else:
            message = 'No media selected!'
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
