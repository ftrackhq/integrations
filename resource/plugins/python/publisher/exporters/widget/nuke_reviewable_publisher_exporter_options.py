# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
from functools import partial

import nuke

import ftrack_api


from ftrack_connect_pipeline_nuke import plugin
from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget

from Qt import QtWidgets


class NukeReviewablePublisherExporterOptionsWidget(BaseOptionsWidget):
    '''Nuke reviewable publisher options user input plugin widget'''

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

        super(NukeReviewablePublisherExporterOptionsWidget, self).__init__(
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

        super(NukeReviewablePublisherExporterOptionsWidget, self).build()

        bg = QtWidgets.QButtonGroup(self)
        self.render_rb = QtWidgets.QRadioButton(
            'Render reviewable from script/connected node'
        )
        bg.addButton(self.render_rb)
        self.layout().addWidget(self.render_rb)

        self.render_from_sequence_rb = QtWidgets.QRadioButton(
            'Render reviewable from existing selected rendered write/read node sequence or movie'
        )
        bg.addButton(self.render_from_sequence_rb)
        self.layout().addWidget(self.render_from_sequence_rb)

        self.render_from_sequence_note = QtWidgets.QLabel(
            '<html><i>Make sure you select a write/read node pointing rendered media.</i></html>'
        )
        self.layout().addWidget(self.render_from_sequence_note)
        self.render_from_sequence_note.setVisible(False)

        self.pickup_rb = QtWidgets.QRadioButton(
            'Pick up existing movie from selected write/read node'
        )
        bg.addButton(self.pickup_rb)
        self.layout().addWidget(self.pickup_rb)

        self.pickup_note = QtWidgets.QLabel(
            '<html><i>Make sure you select a write/read node pointing to an existing rendered movie.</i></html>'
        )
        self.layout().addWidget(self.pickup_note)
        self.pickup_note.setVisible(False)

        if not 'mode' in self.options:
            self.set_option_result('render', 'mode')
        mode = self.options['mode'].lower()
        if mode == 'render_from_sequence':
            self.render_from_sequence_rb.setChecked(True)
        elif mode == 'pickup':
            self.pickup_rb.setChecked(True)
        else:
            self.render_rb.setChecked(True)

    def post_build(self):
        super(NukeReviewablePublisherExporterOptionsWidget, self).post_build()

        self.render_rb.clicked.connect(self._update_render_mode)
        self.render_from_sequence_rb.clicked.connect(self._update_render_mode)
        self.pickup_rb.clicked.connect(self._update_render_mode)

    def _update_render_mode(self):
        value = 'render'
        if self.render_from_sequence_rb.isChecked():
            value = 'render_from_sequence'
        elif self.pickup_rb.isChecked():
            value = 'pickup'
        self.set_option_result(value, 'mode')
        self.render_from_sequence_note.setVisible(
            self.render_from_sequence_rb.isChecked()
        )
        self.pickup_note.setVisible(self.pickup_rb.isChecked())


class NukeReviewablePublisherExporterOptionsPluginWidget(
    plugin.NukePublisherExporterPluginWidget
):
    plugin_name = 'nuke_reviewable_publisher_exporter'
    widget = NukeReviewablePublisherExporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = NukeReviewablePublisherExporterOptionsPluginWidget(api_object)
    plugin.register()
