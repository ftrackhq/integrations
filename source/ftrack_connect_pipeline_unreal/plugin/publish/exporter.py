# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import sys
import subprocess
import os

import unreal

from ftrack_connect_pipeline import plugin

from ftrack_connect_pipeline_qt import plugin as pluginWidget

from ftrack_connect_pipeline_unreal.plugin import (
    UnrealBasePlugin,
    UnrealBasePluginWidget,
)
from ftrack_connect_pipeline_unreal import utils as unreal_utils


class UnrealPublisherExporterPlugin(
    plugin.PublisherExporterPlugin, UnrealBasePlugin
):
    '''Class representing an Exporter Plugin
    .. note::

        _required_output a Dictionary
    '''


class UnrealPublisherExporterPluginWidget(
    pluginWidget.PublisherExporterPluginWidget, UnrealBasePluginWidget
):
    '''Class representing an Eporter Widget
    .. note::

        _required_output a Dictionary
    '''
