..
    :copyright: Copyright (c) 2022 ftrack

.. _introduction/framework/dcc:

*********************
DCC integration layer
*********************

The plugin for a specific :term:`DCC` application (maya, nuke and so on) and is
identified by the :term:`host type`. Depends on the core Framework plugins above
for bootstrapping and providing the three main Framework features:

 * Publish files/components.
 * Load files/components.
 * Asset management.

The integration achieves this by:

 * Bootstrapping the DCC app.
 * Launching the pipeline host.
 * Adding menu items to the “ftrack” menu within the DCC app, enabling launch of each :term:`client` widget.

The DCC module sits on top of the :term:`UI` layer in the pipeline Framework stack.

Structure:

.. code-block:: bash

    asset/
    client/
    host/
    plugin/
    utils/

Description of main submodules:

 * **asset**; Contains asset manager logic for handling DCC objects.
 * **client**; DCC implementation of each :term;`client`.
 * **host**; DCC implementation of the :term;`host`.
 * **plugin**; Contain DCC implementation of bases for definition plugin widgets.
 * **utils**; Contains additional utils and tools related to the DCC application.

resource
========

The resource folder contains the bootstrap scripts, the hook is assumed to setup
the DCC by either environment variables or arguments so it is able to find and load
the bootstrap script(s).


