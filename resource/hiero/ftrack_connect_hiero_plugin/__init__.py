# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import logging

import ftrack_connect_nuke_studio.plugin
import ftrack_connect_nuke_studio.logging

# Configure Python logging for use with Foundry Asset API.
# TODO: Standardise this in ftrack-connect-foundry.
logger = logging.getLogger('ftrack_connect_nuke_studio')
logger.setLevel(logging.DEBUG)
logger.propagate = False
handler = ftrack_connect_nuke_studio.logging.FoundryHandler()
handler.setFormatter(logging.Formatter('%(name)s:%(message)s'))
logger.addHandler(handler)

# Assign to name that Foundry API will search for in order to register plugin.
plugin = ftrack_connect_nuke_studio.plugin.Plugin
