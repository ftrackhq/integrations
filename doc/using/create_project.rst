Create a new Project
********************

Creating a project requires some simple stages.

* Shot Naming
* Shot Tagging
* Project Preview
* Project Settings
* Project Creation


Shot Naming
============

In order to have the context tags able to extract the names from the clip, these have to be named matching the regular expression defined in the tag.
In case of the sequence, will be looking for **SQ**, for shot **SH** and for episodes **EP**.

This function can be found under the shot context menu :

    **Editorial -> Rename Shots (Alt+Shift+/)**

.. image:: /image/rename.png

.. note::
    Rename shots works on a selection of shots.
    The ### will be replaced by the increment value and the number of selected shots.

Shot tagging
============

Once the shots are correctly named, you are ready to start the tagging process.
All you'll have to do is to select the required tags from the context menu and drop them on all the shots.

.. image:: /image/ftag_drop.png

To review which tags have been applied just click on the tag icon on the clip.

.. image:: /image/applied_ftags.png

In this window you'll be able to see which values have been extracted, for the single tag, from the clip name.

Project Preview
===============

In order to preview the project structure and its attributes, you'll have to trigger the project creation.

.. image:: /image/create_project_context_menu.png

Which will show the tool dialog loading.

.. image:: /image/create_project_loading.png

During the loading process it will check the tag struture against what's already available on the server.
As soon as the check is done, the interface will be displaying the preview of the project tree, showing all the data, which will be set to the shot.
This will be represented on the context treee, whith different colors.

* **green**, for an exsting item.
* **orange**, for a new item.
* **red**, for an error which prevented the item to be created.

.. image:: /image/create_project_dialog.png


Project Settings
================

From this interface you'll be able to set the attributes for all the shots, such as resolution, fps, and handles.
You'll also be able to pick the workflow schema for the project creation.

* **Worflow**

.. image:: /image/create_project_workflows.png


* **Resolution**

.. image:: /image/create_project_resolutions.png

* **Frame per second**

.. image:: /image/create_project_fps.png

From here you'll also be able to define some other attributes such as handles and and the start frame offset.

All the project settings will be added as attributes to the shot.

.. note::
    Some attributes, such as timecode related ones, are added for the moment as metadata.
    This might be change in the future


Project Creation
================

Once the project have been setup, all you'll have to do will be to press the create project button.

.. image:: /image/create_project_run.png

As soon as the project finishes , a message will be displayed.

.. image:: /image/create_project_done.png


At this poit you can go and have a look on the ftrack server for the result.

In here you'll be able to see your project and the structure as was defined fron within Nuke Studio interface.

.. image:: /image/create_project_remote_result.png

As well as the attributes and metadata, which have been added to the shot.
.. image:: /image/create_project_remote_result_attributes.png


