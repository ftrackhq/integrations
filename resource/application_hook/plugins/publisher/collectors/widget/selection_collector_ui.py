# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from functools import partial

from ftrack_connect_pipeline_maya import plugin
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget

from Qt import QtWidgets

import maya.cmds as mcd


class SelectionCollectorWidget(BaseOptionsWidget):

    def __init__(
        self, parent=None, session=None, data=None, name=None,
        description=None, options=None, context=None
    ):

        super(SelectionCollectorWidget, self).__init__(
            parent=parent,
            session=session, data=data, name=name,
            description=description, options=options,
            context=context)

    def build(self):
        '''build function , mostly used to create the widgets.'''
        self.group = QtWidgets.QButtonGroup()
        selection = QtWidgets.QRadioButton('Selection')
        all = QtWidgets.QRadioButton('All')

        self.group.addButton(selection)
        self.group.addButton(all)

        self.layout().addWidget(self.group)


    def post_build(self):
        super(SelectionCollectorWidget, self).post_build()
        update_fn = partial(self.set_option_result, key='camera_name')

        self.cameras.editTextChanged.connect(update_fn)
        self.set_option_result(self.maya_cameras[0], key='camera_name')


class SelectionCollectorPluginWidget(plugin.CollectorMayaWidget):
    plugin_name = 'picker_ui'

    def run(self, context=None, data=None, name=None, description=None, options=None):
        return SelectionCollectorWidget(
            context=context,
            session=self.session, data=data, name=name,
            description=description, options=options
        )


def register(api_object, **kw):
    plugin = SelectionCollectorPluginWidget(api_object)
    plugin.register()
