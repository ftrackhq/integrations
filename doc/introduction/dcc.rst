..
    :copyright: Copyright (c) 2022 ftrack

.. _introduction/dcc:

*********************
DCC integration layer
*********************


The plugin for a specific DCC app (maya, nuke and so on), depends on the plugins
above for bootstrapping and providing the three main framework features:

 * Load files/components.
 * Publish files/components.
 * Asset management.

The integration achieves this by:

 * Bootstrapping the DCC app.
 * Launching the pipeline host.
 * Adding menu items to the “ftrack” menu within the DCC app, enabling launch of
the features described above.

