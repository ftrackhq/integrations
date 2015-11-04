..
    :copyright: Copyright (c) 2015 ftrack

.. _using/export_project:

*******************
Exporting a project
*******************

Setup the project structure
===========================

As part of the project export process 
:term:`Context templates <Context template>` are used to define the hierarchy
to create in ftrack.

The template is applied to each clip and will use the name of the clip to
determine what entities to create.

The plugin comes with a couple of default templates which will create some
different structures. Lets look at two of the templates:

==========================  ====================
Template                    Description
==========================  ====================
Classic, sequence and shot  Match `SQ` or `SH` and any subsequent numbers. Example: `SQ001_SH010` will be matched as Sequence with name `001` and a shot named `010`.
Classic, shot only          Match `SH` and any subsequent digits. Example: `vfx_SH001` will match `001`.
Full name, shot only        Match entire clip name. Example: `vfx_SH001` will match `vfx_SH001`.
==========================  ====================

By applying different templates to the same selection in the timeline we'll
get different results. For example if we have a selection of clips in the timeline:

.. image:: /image/example_timeline.png

The clips have been renamed to a format of `vfx_SQ###_SH###` where `###` is
replaced with a sequential number.

If we apply the different templates to all the clips in the timeline we'll get
these different results:

.. figure:: /image/classic_sequence_shot_preview.png

    Classic, sequence and shot

    This template will generate a structure containing both sequences and shots.
    Any clips not matching the entire template is displayed in orange and will
    not yield any entites in ftrack.

.. figure:: /image/classic_shot_preview.png

    Classic, shot only

    This template will generate a structure containing only shots and as you can
    see only one clip does not match this template.

.. figure:: /image/full_name_shot_preview.png

    Full name, shot only

    This template will generate a structure containing only shots and as you can
    see all clips match the template since using the entire name of the clip.

.. seealso::
    
    :ref:`All available templates <using/templates>`

Rename clips
^^^^^^^^^^^^

To quickly rename a bunch of clips to match the :term:`Context template` you
are using the builtin Rename Shots dialog can be used. It is located in the
context menu under :menuselection:`Editorial --> Rename Shots (Alt+Shift+/)`

.. image:: /image/rename.png

.. note::

    Rename works on a selection of clips. The ### will be replaced by the
    increment value and the number of selected clips.

.. seealso::

    `Renaming clips in Nuke Studio <http://help.thefoundry.co.uk/nuke/9.0/#timeline_environment/conforming/renaming_track_items.html>`_

Apply task tags
^^^^^^^^^^^^^^^

When the clips are correctly named to match the :term:`Context template` you
can apply tags to specify which tasks you want to generate. If you don't want
to create any tasks you can jump straight to :ref:`exporting <using/export_project/exporting>`

To see available tags open the tag window,
:menuselection:`Window --> Tags` and navigating to the *ftrack folder*.

.. image:: /image/tags.png

.. seealso::
    
    `Tagging in Nuke Studio <http://help.thefoundry.co.uk/nuke/9.0/#timeline_environment/usingtags/tagging_track_items.html>`_

Select the tasks you want to create and drop them on the clips.

.. image:: /image/ftag_drop.png

To review which tags have been applied just click on the tag icon on the clip.

.. image:: /image/applied_ftags.png

When done tagging your're ready to export you project.

.. _using/export_project/exporting:

Exporting
=========

With the project structure setup, it is time to export the project to ftrack.

Open the :guilabel:`Export project` dialog to get started:

.. image:: /image/create_project_context_menu.png

Preview
^^^^^^^

When the dialog opens it will check against the server to see what's already
been created.

As soon as the check is done, the interface will display the preview of the
project. The items are color coded:

* **green** - an existing object.
* **white** - a new object.
* **red** - an error occurred regarding this object.

.. image:: /image/create_project_dialog.png

.. _using/project_settings:

Configure project settings
^^^^^^^^^^^^^^^^^^^^^^^^^^

From this interface you'll be able to set the attributes for all the mapped
shots, such as resolution, fps, and handles.  You will also be able to pick the
workflow schema for the project creation and define other attributes such as
handles and the start frame offset.

All the project settings will be added as attributes to each mapped shot.

.. image:: /image/create_project_settings.png

.. note::

    Some attributes, such as timecode related ones, are stored as metadata. This
    might change in the future.


Select template
^^^^^^^^^^^^^^^

Select the template you want to use when exporting the project. When selecting
a template the preview window will update with the new hierarchy::

.. image:: /image/select_template_preview.png

Any clips not matching the selected template are displayed in red in the group
called `Clips not matching template`.

.. note::
    
    The selected template will be stored in the Nuke Studio project file and
    will be preselected if running export again.

Export
^^^^^^

Once you are happy with the configuration, all you have to do is press the
:guilabel:`Export` button. As soon as the export finishes, a message will be
displayed.

.. image:: /image/create_project_done.png

At this point the project has been created on your
:term:`ftrack server <ftrack server>` and from the Project spreadsheet it is
possible to see the project and the structure that was defined in Nuke Studio.

.. image:: /image/create_project_remote_result.png

As well as the attributes and metadata, which have been added to the mapped
shots.

.. image:: /image/create_project_remote_result_attributes.png

.. seealso::

    Besides creating and updating the project structure in ftrack several
    versions are published. To learn more about this please refer to this 
    :ref:`article <using/processors>`
