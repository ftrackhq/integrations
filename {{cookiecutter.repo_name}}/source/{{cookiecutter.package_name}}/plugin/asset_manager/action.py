# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.plugin import {{cookiecutter.host_type_capitalized}}BasePlugin


class {{cookiecutter.host_type_capitalized}}AssetManagerActionPlugin(
    plugin.AssetManagerActionPlugin, {{cookiecutter.host_type_capitalized}}BasePlugin
):
    '''
    Class representing a Asset Manager Action {{cookiecutter.host_type_capitalized}} Plugin
    '''
