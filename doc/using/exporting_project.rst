..
    :copyright: Copyright (c) 2015 ftrack

.. _using/export_project:

*******************
Exporting a project
*******************

Setup the project structure
===========================

As part of the project export process tags are used to link Nuke Studio clips
with sequences, shots and tasks in ftrack. In order for the context tags to
successfully extract the names from the clip, these have to be named matching
the expression defined in the tag.

Tagging
-------

Let's walk through how to tag your timeline to be able to export to ftrack.

To see available tags open the tag window,
:menuselection:`Window --> Tags` and navigating to the *ftrack folder*.

.. image:: /image/tags.png

In the ftrack folder you can see both context tags and task type tags. The
context tags are used to generate the hierarchy in ftrack and the task type
tags are used to create tasks.

Before tagging, we first need to rename our clips to match our naming structure.
By default the different context tags will match:

* Episodes: **EP** followed by any numbers. If not found the entire clip name will be used.
* Sequence: **SQ** followed by any numbers. If not found the entire clip name will be used.
* Shot: **SH** followed by any numbers. If not found the entire clip name will be used.

For example, if a clip named *SQ001_SH010* has the shot and sequence
context tags applied it will yield a structure like this:

.. image:: /image/hierarchy_first.png

If the clip instead named *SQ001_010* the shot tag will match the entire 
name and yield a hierarchy looking like this:

.. image:: /image/hierarchy_second.png

If adding task type tags the the same clip the hierarchy will look like this:

.. image:: /image/hierarchy_with_tasks.png

.. seealso::
    
    :ref:`Customising tag expressions <developing/customising_tag_expressions>`

Rename shots
^^^^^^^^^^^^

To quickly rename a bunch of clips to match the tag patterns you can use the
builtin Rename Shots dialog. It is located in the context menu under
:menuselection:`Editorial --> Rename Shots (Alt+Shift+/)`

.. image:: /image/rename.png

.. note::

    Rename shots works on a selection of shots. The ### will be replaced by the
    increment value and the number of selected shots.

    `Renaming clips in Nuke Studio <http://help.thefoundry.co.uk/nuke/9.0/#timeline_environment/conforming/renaming_track_items.html>`_

Apply tags
^^^^^^^^^^

When the shots are correctly named, you are ready to start the tagging process.
Select the context tags you want to use and drop them on your clips.

.. seealso::
    
    `Tagging in Nuke Studio <http://help.thefoundry.co.uk/nuke/9.0/#timeline_environment/usingtags/tagging_track_items.html>`_

.. image:: /image/ftag_drop.png

To review which tags have been applied just click on the tag icon on the clip.

.. image:: /image/applied_ftags.png

In this window you'll be able to see which values have been extracted, for the
single tag, from the clip name.

When done tagging your're ready to export you project.

Preview project structure
-------------------------

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
----------------

From this interface you'll be able to set the attributes for all the shots,
such as resolution, fps, and handles.  You will also be able to pick the
workflow schema for the project creation and define other attributes such as
handles and the start frame offset.

All the project settings will be added as attributes to the shot.

.. image:: /image/create_project_settings.png

.. note::

    Some attributes, such as timecode related ones, are stored as metadata. This
    might change in the future.

Exporting
---------

Once you are happy with the configuration, all you have to do will be to
press the Export button. As soon as the export finishes, a message will be
displayed.

.. image:: /image/create_project_done.png

At this point the project are created on your
:term:`ftrack server <ftrack server>` and from the Project spreadsheet it is
possible to see the project and the structure that was defined in Nuke Studio.

At this point you can go and have a look on the
` for the result. In here you will be able
to see your project and the structure as was defined from within Nuke Studio.

.. image:: /image/create_project_remote_result.png

As well as the attributes and metadata, which have been added to the shot.

.. image:: /image/create_project_remote_result_attributes.png

.. seealso::

    Besides creating and updating the project structure in ftrack several
    versions are published. To learn more about this please refer to this 
    :ref:`article <using/processors>`
