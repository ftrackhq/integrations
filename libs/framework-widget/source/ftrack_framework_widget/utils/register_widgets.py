# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import logging
import pkgutil
import inspect

from ftrack_framework_widget import Widget, Dialog

logger = logging.getLogger('ftrack_framework_widgets.register')

# TODO: put this in ftrack_utils???
# This is faster than glob and walk found in:
# https://stackoverflow.com/questions/973473/getting-a-list-of-all-subdirectories-in-the-current-directory
def fast_scandir(dirname):
    subfolders = [f.path for f in os.scandir(dirname) if f.is_dir()]
    for dirname in list(subfolders):
        subfolders.extend(fast_scandir(dirname))
    return subfolders


# TODO: Maybe move the registry code to a utility tool where user can point to,
#  something like:
#  from framework_utilities import register_plugins
#  register_plugins.register( current_dir )
def register_widgets(
        current_dir, event_manager, client_id, context_id, plugin_definition, dialog_run_plugin_method_callback, dialog_property_getter_connection_callback):
    '''Register plugin to api_object.'''

    framework_plugin_type = Widget

    subfolders = fast_scandir(current_dir)

    registred_widgets = []
    for loader, module_name, is_pkg in pkgutil.walk_packages(subfolders):
        _module = loader.find_module(module_name).load_module(module_name)
        cls_members = inspect.getmembers(_module, inspect.isclass)
        success_registry = False
        for name, obj in cls_members:
            if obj == framework_plugin_type:
                continue
            if framework_plugin_type not in inspect.getmro(obj):
                logger.debug(
                    "Not registring {} because is not type of {}".format(
                        name, framework_plugin_type
                    )
                )
                continue
            #TODO: check if session is still necessary after the refactor We should pass the event manager and host_id
            try:
                # TODO: we need to pass event manager, host id.
                widget = obj(
                    event_manager,
                    client_id,
                    context_id = None,
                    plugin_definition = None,
                    dialog_run_plugin_method_callback = None,
                    dialog_property_getter_connection_callback = None,
                )
                # TODO: can register be a classmethod so we don't have to initialize the widget?
                widget.register()
                registred_widgets.append(obj)
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
    return registred_widgets
