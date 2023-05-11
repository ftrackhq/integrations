# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_qt.plugin.widget.dynamic import DynamicWidget


class MaxAbcLoaderImporterOptionsWidget(DynamicWidget):
    '''Max FBX publisher options user input plugin widget'''

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

        super(MaxAbcLoaderImporterOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

    def define_options(self):
        '''Default renderable options for dynamic widget'''
        return {
            "ABCCoordinateSystem": 3,
            "ABCImportToRoot": False,
            "ABCFitTimeRange": True,
            "ABCSetStartTime": False,
            "ABCUVs": True,
            "ABCNormals": True,
            "ABCVertexColors": True,
            "ABCExtraChannels": True,
            "ABCVelocity": True,
            "ABCMaterialIDs": True,
            "ABCVisibility": True,
            "ABCCustomAttributes": True,
            "ABCShapeSuffix": True,
            "ABCObjectAttributes": True,
        }

    def get_options_group_name(self):
        '''Override'''
        return 'Alembic exporter Options'

    def build(self):
        '''build function , mostly used to create the widgets.'''

        self.update(self.define_options())

        super(MaxAbcLoaderImporterOptionsWidget, self).build()


class MaxAbcLoaderImporterOptionsPluginWidget(
    plugin.MaxLoaderImporterPluginWidget
):
    plugin_name = 'max_abc_loader_importer'
    widget = MaxAbcLoaderImporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxAbcLoaderImporterOptionsPluginWidget(api_object)
    plugin.register()
