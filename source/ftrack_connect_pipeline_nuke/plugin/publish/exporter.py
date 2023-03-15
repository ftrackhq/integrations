# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_qt import plugin as pluginWidget
from ftrack_connect_pipeline_nuke.plugin import (
    NukeBasePlugin,
    NukeBasePluginWidget,
)


class NukePublisherExporterPlugin(
    plugin.PublisherExporterPlugin, NukeBasePlugin
):
    '''Class representing an exporter Plugin
    .. note::

        _required_output a Dictionary
    '''

    def _apply_movie_file_format_options(self, write_node, options):
        '''Apply movie options to write node'''
        selected_file_format = str(options.get('file_format'))

        write_node['file_type'].setValue(selected_file_format)

        # Set additional file format options
        # TODO: Document macOs crash and how to choose mp4v codec if mov file format as a work around
        if len(options.get(selected_file_format) or {}) > 0:
            for k, v in options[selected_file_format].items():
                if k not in ['codecs', 'codec_knob_name']:
                    write_node[k].setValue(v)


class NukePublisherExporterPluginWidget(
    pluginWidget.PublisherExporterPluginWidget, NukeBasePluginWidget
):
    '''Class representing an exporter Widget
    .. note::

        _required_output a Dictionary
    '''
