# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack


def register():
    '''Register all shared pyblish plugins.'''
    # Importing the submodules will cause plugins to register.
    import ftrack_connect_pipeline.shared_pyblish_plugins.collect
    import ftrack_connect_pipeline.shared_pyblish_plugins.validate
    import ftrack_connect_pipeline.shared_pyblish_plugins.integrate
