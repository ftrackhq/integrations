# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import logging
import ftrack_api
import pkgutil
import inspect
logger = logging.getLogger('ftrack_framework_plugins.register')

# TODO: maybe all plugins provided by ftrack can be defined here, just add the
#  DCC ones in a separated folder like maya/loader/plugin_name. Still clients
#  can nadd new plugins by simply creating ftrack_framework_myStudio_plugins,
#  or we can add prototype plugins by adding:
#  ftrack_framework_<SpecificDCC>_plugins.


# This is faster than glob and walk found in:
# https://stackoverflow.com/questions/973473/getting-a-list-of-all-subdirectories-in-the-current-directory
def fast_scandir(dirname):
    subfolders = [f.path for f in os.scandir(dirname) if f.is_dir()]
    for dirname in list(subfolders):
        subfolders.extend(fast_scandir(dirname))
    return subfolders


# TODO: Maybe move the registry code to a utility tool where user can point to,
#  something like:
#  from framework_utilities import register_plugin
#  register_plugin.register( current_dir )
def register(api_object, **kw):
    '''Register plugin to api_object.'''

    # Validate that api_object is an instance of ftrack_api.Session. If not,
    # assume that _register is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    # TODO: add the basePluginType class here.
    framework_plugin_type = ""
    current_dir = os.path.dirname(__file__)

    subfolders = fast_scandir(current_dir)

    registred_plugins = []
    for loader, module_name, is_pkg in pkgutil.walk_packages(subfolders):
        _module = loader.find_module(module_name).load_module(module_name)
        cls_members = inspect.getmembers(_module, inspect.isclass)
        success_registry = False
        for name, obj in cls_members:
            if framework_plugin_type not in inspect.getmro(obj):
                logger.debug("Not registring {} because is not type of {}".format(name, framework_plugin_type))
                continue
            #TODO: check if session is still necessary after the refactor We should pass the event manager and host_id
            try:
                # TODO: we need to pass event manager, host id.
                plugin = obj(api_object)
                plugin.register()
                registred_plugins.append(obj.__class__)
            except Exception as e:
                logger.warning(
                    "Couldn't register plugin {} \n error: {}".format(name, e)
                )
                continue
            logger.debug("Plugin {} registred".format(name))
            success_registry = True

        if not success_registry:
            logger.warning(
                "No framework compatible plugin found in module {} "
                "in path{}".format(module_name, loader.path)
            )
    return registred_plugins
