..
    :copyright: Copyright (c) 2014 ftrack

.. _using/publishing:

**********
Publishing
**********

Connect provides a simple publisher application to support publishing files
directly from your computer without the need to open another application (though
publishing from within many applications, including from the ftrack web
interface, is also supported).

To publish, ensure you have the interface open by selecting :guilabel:`Open`
from the :term:`service context menu` and then selecting the :guilabel:`Publish`
tab.

.. image:: /image/publisher_tab.png

Add components
==============

Drag and drop files from your computer onto the publisher (or use the
:guilabel:`Browse` button to browse and select files).

.. note::

    Sequences of files will be automatically detected and added as one entry.

.. image:: /image/publisher_drop_files.png

Each file will be added as a component with a name based on the filename of the
file. You can manually edit the name if desired by clicking in the name of the
component and typing a new name.

.. image:: /image/publisher_edit_component_name.png

Components can be removed by clicking the :guilabel:`Remove` icon next to each
entry.

Select a linked entity
======================

To change the entity that the publish will be linked to, click the
:guilabel:`Browse` button next to the :guilabel:`Linked Entity` field.

.. image:: /image/publisher_linked_entity_field.png

A browser, similar to the file browser, will appear, but it allows browsing
ftrack rather than the filesystem.

.. image:: /image/entity_browser.png

You can navigate through a project structure by double clicking on items in the
list. A navigation bar at the top will show you where you are and you can also
click an item in the navigation bar to jump back up the hierarchy.
Alternatively, use the neighbouring :guilabel:`Navigate Up` tool button to move
up a level at a time.

.. note::

    If an item you expect to see in the list is not appearing, try clicking the
    :guilabel:`Reload` tool button to refresh the list from the server.

To select the entity to link against, select an item in the list and then click
the :guilabel:`Choose` button. Alternatively, to cancel making any changes
click the :guilabel:`Cancel` button.

.. _using/publishing/choose_or_create_asset:

Choose or create asset
======================

You can now choose if you like to publish a new version of an previously
published :term:`asset` or if you like to publish the first version of a new
:term:`asset`.

.. image:: /image/publisher_asset_options.png

To create a new :term:`asset`, select :guilabel:`Create new` and fill in the
following options.

:Type: The type of :term:`asset` to publish. Choose from a list retrieved from
       the connected :term:`ftrack` server.
:Name: The name of :term:`asset` to publish. The name and type must be unique
       when creating new assets.

To publish a new version of an existing :term:`asset`, select 
:guilabel:`Version up existing` instead. In the list which is shown below the
radio buttons, select the :term:`asset` you wish to use.

.. image:: /image/publisher_asset_existing.png

Fill out remaining fields
=========================

Fill out the remaining fields in the publisher.

.. image:: /image/publisher_filled_out.png

:Web playable: If you want one of the components to be encoded for playing on
               the web select it in this field from the list of components
               added.
:Thumbnail: Drag and drop a small thumbnail of the asset onto this field to give
            others a better indication of what the asset is before opening.
:Description: A brief description of the published asset or the changes made
              since the last published version.

Publish
=======

When ready, press :guilabel:`Publish` to start the publish. During this time
you will see a progress indicator.

.. image:: /image/publisher_publish_progress.png

.. important:: Do not quit the service whilst the publish is in progress.

Once completed, the indicator will change to a notification.

.. image:: /image/publisher_publish_success.png