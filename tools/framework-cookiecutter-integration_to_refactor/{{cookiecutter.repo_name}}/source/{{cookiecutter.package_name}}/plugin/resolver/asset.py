# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from ftrack_connect_pipeline import plugin
from {{cookiecutter.package_name}}.plugin import {{cookiecutter.host_type_capitalized}}BasePlugin


class {{cookiecutter.host_type_capitalized}}AssetResolverPlugin(
    plugin.AssetResolverPlugin, {{cookiecutter.host_type_capitalized}}BasePlugin
):
    '''
    Class representing a {{cookiecutter.host_type_capitalized}} Asset Resolver Plugin
    '''
