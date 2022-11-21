..
    :copyright: Copyright (c) 2022 ftrack

.. _introduction/framework/ui:

********
UI layer
********

The :term:`UI` abstraction layer takes care of rendering widgets inside the DCC
application, with the ftrack default style applied. The UI sits on top of the
pipeline Framework core layer in the stack and is backed by the :term: `Qt`
framework plugin.

Each :term:`Client` is represented in the UI layer, which in turn is inherited by
the DCC layer (Maya and so on).

Structure:

.. code-block:: bash

    client/
    plugin/
    ui/
        assembler/
        asset_manager/
        factory/
        log_viewer/
        utility/

Description of main submodules:

 * **client**; Contains client UI implementations.
 * **plugin**; Contain bases for definition plugin widgets
 * **assembler**; The assembler/loader widget.
 * **asset_manager**; The asset manager widget.
 * **factory**; Contains widgets and logic for generating the publisher and parts of the loader, factorised from the definition.
 * **log_viewer**; The log viewer widget.
 * **utility**; Utility widgets such as the entity browser, context selectors and so on.

resource
========

The resource folder contains associated fonts, images and stylesheets.







