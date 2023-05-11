# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
from functools import partial

from Qt import QtWidgets

import ftrack_api

from ftrack_connect_pipeline_maya import plugin
from ftrack_connect_pipeline_qt.plugin.widget.dynamic import DynamicWidget


class MayaAbcPublisherExporterOptionsWidget(DynamicWidget):
    '''Maya Alembic publisher options user input plugin widget'''

    auto_fetch_on_init = True

    def define_options(self):
        '''Default options for dynamic widget'''
        return {
            'alembicUvwrite': True,
            'alembicWorldspace': False,
            'alembicWritevisibility': False,
        }

    @property
    def frames_options(self):
        '''Return options for custom widget'''
        _frames_option = {
            'frameStart': str(self.options.get('frameStart')),
            'frameEnd': str(self.options.get('frameEnd')),
            'alembicEval': str(self.options.get('alembicEval', '1.0')),
        }
        return _frames_option

    @property
    def bool_options(self):
        '''Return boolean options for custom widget'''
        _bool_options = {
            'alembicAnimation': self.options.get('alembicAnimation', False),
        }
        return _bool_options

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
        self.options_cb = {}
        self.options_le = {}
        self.frame_info = {}

        super(MayaAbcPublisherExporterOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

    def on_fetch_callback(self, result):
        '''This function is called by the _set_internal_run_result function of
        the BaseOptionsWidget'''
        for k, v in self.options_le.items():
            if v.text() == "None":
                if k in list(result.keys()):
                    self.options_le[k].setText(str(result[k]))
                else:
                    self.options_le[k].setText("0")

    def get_options_group_name(self):
        '''Override'''
        return 'Alembic exporter Options'

    def build(self):
        '''Build function , mostly used to create the widgets.'''

        # Define dynamic widgets
        self.update(self.define_options(), ignore=['alembicAnimation'])

        # Create dynamic widgets
        super(MayaAbcPublisherExporterOptionsWidget, self).build()

        # Create animation input
        self.animation_layout = QtWidgets.QVBoxLayout()

        for option, default_value in sorted(self.bool_options.items()):
            option_check = QtWidgets.QCheckBox(option)
            option_check.setChecked(default_value)

            self.options_cb[option] = option_check

            if option == 'alembicAnimation':
                self.animation_layout.addWidget(option_check)

        self.frames_widget = QtWidgets.QWidget()
        self.frames_H_layout = QtWidgets.QHBoxLayout()
        self.frames_widget.setLayout(self.frames_H_layout)

        for option, default_value in sorted(
            self.frames_options.items(), reverse=True
        ):
            frames_V_layout = QtWidgets.QVBoxLayout()
            option_label = QtWidgets.QLabel(option)
            option_line_edit = QtWidgets.QLineEdit(default_value)
            self.options_le[option] = option_line_edit
            frames_V_layout.addWidget(option_label)
            frames_V_layout.addWidget(option_line_edit)
            self.frames_H_layout.addLayout(frames_V_layout)

        self.animation_layout.addWidget(self.frames_widget)
        self.option_layout.addLayout(self.animation_layout)

    def post_build(self):
        super(MayaAbcPublisherExporterOptionsWidget, self).post_build()

        self.frames_widget.setVisible(self.bool_options['alembicAnimation'])

        for option, widget in self.options_cb.items():
            if option == 'alembicAnimation':
                widget.stateChanged.connect(self._on_alembic_animation_changed)
            else:
                update_fn = partial(self.set_option_result, key=option)
                widget.stateChanged.connect(update_fn)

        for option, widget in self.options_le.items():
            update_fn = partial(self.set_option_result, key=option)
            widget.textChanged.connect(update_fn)

    def _reset_default_animation_options(self):
        for k, v in self.frames_options.items():
            self.options_le[k].setText(str(v))

    def _on_alembic_animation_changed(self, value):
        '''Updates the options dictionary with provided *path* when
        textChanged of line_edit event is triggered'''
        self.frames_widget.setVisible(value)
        if value:
            self._reset_default_animation_options()
            for option, widget in self.options_le.items():
                self.set_option_result(widget.text(), key=option)
        self.set_option_result(value, key='alembicAnimation')


class MayaAbcPublisherExporterOptionsPluginWidget(
    plugin.MayaPublisherExporterPluginWidget
):
    plugin_name = 'maya_abc_publisher_exporter'
    widget = MayaAbcPublisherExporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MayaAbcPublisherExporterOptionsPluginWidget(api_object)
    plugin.register()
