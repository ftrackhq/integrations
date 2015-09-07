..
    :copyright: Copyright (c) 2015 ftrack

*******************
Exporting a project
*******************

When your track items have been properly :ref:`tagged <using/tags>` you are
ready to continue and export your project to ftrack.

Preview
===============

To preview and export the project and its attributes you'll have to open the
``Export project`` dialog:

.. image:: /image/create_project_context_menu.png

This will open Export project dialog. When the dialog opens it will check
against the server to see what's already available and existing on the server.

As soon as the check is done, the interface will be displaying the preview of
the project. The objects in ftrack are colored differently:

* **green**, for an exsting object.
* **white**, for a new object.
* **red**, for an error which prevented the object to be created.

.. image:: /image/create_project_dialog.png

.. _using/project_settings:

Project settings
================

From this interface you'll be able to set the attributes for all the shots,
such as resolution, fps, and handles. You will also be able to pick the workflow
schema for the project creation. You will also be able to define some other
attributes such as handles and and the start frame offset.

All the project settings will be added as attributes to the shot.

.. image:: /image/create_project_settings.png

.. note::

    Some attributes, such as timecode related ones, are added for the moment as
    metadata. This might be change in the future.


Exporting
=========

Once you are happy with the configuration, all you have to do will be to
press the Export button. As soon as the export finishes, a message will be
displayed.

.. image:: /image/create_project_done.png

At this point you can go and have a look on the
:term:`ftrack server <ftrack server>` for the result. In here you will be able
to see your project and the structure as was defined from within Nuke Studio.

.. image:: /image/create_project_remote_result.png

As well as the attributes and metadata, which have been added to the shot.

.. image:: /image/create_project_remote_result_attributes.png

.. seealso::

    Besides creating and updating the project structure in ftrack several
    versions are published. To learn more about this please refer to this 
    :ref:`article <using/processors>`
