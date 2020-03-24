# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from functools import partial

from ftrack_connect_pipeline_maya import plugin
from ftrack_connect_pipeline_qt.client.widgets.options.dynamic import DynamicWidget

from Qt import QtWidgets

import maya.cmds as mcd


class AlembicOptionsWidget(DynamicWidget):

    def __init__(
        self, parent=None, session=None, data=None, name=None,
        description=None, options=None, context=None
    ):

        self.options_cb = {}

        super(AlembicOptionsWidget, self).__init__(
            parent=parent,
            session=session, data=data, name=name,
            description=description, options=options,
            context=context)

    def build(self):
        '''build function , mostly used to create the widgets.'''
        super(AlembicOptionsWidget, self).build()

        frames_option = [
            'frameStart',
            'frameEnd',
        ]

        bool_options = [
            'alembicAnimation',
            'alembicUvwrite',
            'alembicWorldspace',
            'alembicWritevisibility',
            'alembicEval'
        ]

        self.option_group = QtWidgets.QGroupBox('Alembic Output Options')
        self.option_group.setToolTip(self.description)

        self.option_layout = QtWidgets.QVBoxLayout()
        self.option_group.setLayout(self.option_layout)

        self.layout().addWidget(self.option_group)
        for option in bool_options:
            option_check = QtWidgets.QCheckBox(option)

            self.options_cb[option] = option_check
            self.option_layout.addWidget(option_check)

            update_fn = partial(self.set_option_result, key=option)
            option_check.stateChanged.connect(update_fn)

    def post_build(self):
        super(AlembicOptionsWidget, self).post_build()

        for option, widget in self.options_cb.items():
            update_fn = partial(self.set_option_result, key=option)
            widget.stateChanged.connect(update_fn)


class AlembicOptionsPluginWidget(plugin.OutputMayaWidget):
    plugin_name = 'alembic_options'

    def run(self, context=None, data=None, name=None, description=None, options=None):
        return AlembicOptionsWidget(
            context=context,
            session=self.session, data=data, name=name,
            description=description, options=options
        )


def register(api_object, **kw):
    plugin = AlembicOptionsPluginWidget(api_object)
    plugin.register()
