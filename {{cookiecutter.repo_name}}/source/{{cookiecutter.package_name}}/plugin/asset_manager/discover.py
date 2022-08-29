# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline import plugin
from ftrack_connect_pipeline_{{cookiecutter.host_type}}.plugin import {{cookiecutter.host_type|capitalize}}BasePlugin


class {{cookiecutter.host_type|capitalize}}AssetManagerDiscoverPlugin(
    plugin.AssetManagerDiscoverPlugin, {{cookiecutter.host_type|capitalize}}BasePlugin
):
    '''
    Class representing a Asset Manager Discover {{cookiecutter.host_type|capitalize}} Plugin
    '''
