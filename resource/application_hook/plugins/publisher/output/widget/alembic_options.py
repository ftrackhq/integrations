# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from functools import partial

from ftrack_connect_pipeline_maya import plugin
from ftrack_connect_pipeline_qt.client.widgets.options.dynamic import DynamicWidget

from Qt import QtWidgets

import maya.cmds as cmd
import ftrack_api


class AlembicOptionsWidget(DynamicWidget):

    def __init__(
        self, parent=None, session=None, data=None, name=None,
        description=None, options=None, context=None
    ):

        self.options_cb = {}
        self.options_le = {}

        super(AlembicOptionsWidget, self).__init__(
            parent=parent,
            session=session, data=data, name=name,
            description=description, options=options,
            context=context)

    def build(self):
        '''build function , mostly used to create the widgets.'''
        super(AlembicOptionsWidget, self).build()
        frames_option = {
            'frameStart': str(cmd.playbackOptions(q=True, ast=True)),
            'frameEnd': str(cmd.playbackOptions(q=True, aet=True)),
            'alembicEval': '1.0'
        }

        bool_options = [
            'alembicAnimation',
            'alembicUvwrite',
            'alembicWorldspace',
            'alembicWritevisibility'
        ]

        self.option_group = QtWidgets.QGroupBox('Alembic Output Options')
        self.option_group.setToolTip(self.description)

        self.option_layout = QtWidgets.QVBoxLayout()
        self.option_group.setLayout(self.option_layout)

        self.animation_layout = QtWidgets.QVBoxLayout()
        self.frames_widget = QtWidgets.QWidget()
        self.frames_H_layout = QtWidgets.QHBoxLayout()
        self.frames_widget.setLayout(self.frames_H_layout)
        self.option_layout.addLayout(self.animation_layout)

        self.layout().addWidget(self.option_group)
        for option in bool_options:
            option_check = QtWidgets.QCheckBox(option)

            self.options_cb[option] = option_check

            if option == 'alembicAnimation':
                self.animation_layout.addWidget(option_check)
                self.animation_layout.addWidget(self.frames_widget)
            else:
                self.option_layout.addWidget(option_check)

        for option, default_value in sorted(frames_option.items(), reverse=True):
            frames_V_layout = QtWidgets.QVBoxLayout()
            option_label = QtWidgets.QLabel(option)
            option_line_edit = QtWidgets.QLineEdit(default_value)
            self.options_le[option] = option_line_edit
            frames_V_layout.addWidget(option_label)
            frames_V_layout.addWidget(option_line_edit)
            self.frames_H_layout.addLayout(frames_V_layout)
            self.frames_widget.hide()

    def post_build(self):
        super(AlembicOptionsWidget, self).post_build()

        for option, widget in self.options_cb.items():
            if option == 'alembicAnimation':
                widget.stateChanged.connect(self._on_alembic_animation_changed)
            else:
                update_fn = partial(self.set_option_result, key=option)
                widget.stateChanged.connect(update_fn)

        for option, widget in self.options_le.items():
            update_fn = partial(self.set_option_result, key=option)
            widget.textChanged.connect(update_fn)

    def _on_alembic_animation_changed(self, value):
        '''Updates the options dictionary with provided *path* when
        textChanged of line_edit event is triggered'''
        if value:
            self.frames_widget.show()
            for option, widget in self.options_le.items():
                self.set_option_result(widget.text(), key=option)
        else:
            self.frames_widget.hide()
        self.set_option_result(value, key='alembicAnimation')



class AlembicOptionsPluginWidget(plugin.PublisherOutputMayaWidget):
    plugin_name = 'alembic_options'
    widget = AlembicOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = AlembicOptionsPluginWidget(api_object)
    plugin.register()
