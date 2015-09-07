..
    :copyright: Copyright (c) 2015 ftrack

.. _using/tags:

****
Tags
****

As part of the project setup process tags are used to link Nuke studio shots
with sequences, shots and tasks in ftrack. 

Shot names
==========

In order for the context tags to sucessfully extract the names from the clip,
these have to be named matching the expression defined in the tag. In the case of
a sequence it will be looking for **SQ**, for shot **SH** and for
episodes **EP**.

The Rename Shots dialog can be used to multi-edit the name of the the selected
shots.

    **Editorial -> Rename Shots (Alt+Shift+/)**

.. image:: /image/rename.png

.. note::
    Rename shots works on a selection of shots. The ### will be replaced by the
    increment value and the number of selected shots.

Shot tagging
============

.. image:: /image/tags.png

When the shots are correctly named, you are ready to start the tagging process.
All you will have to do is to select the required tags from the tags menu and
drop them on your shots.

.. image:: /image/ftag_drop.png

To review which tags have been applied just click on the tag icon on the clip.

.. image:: /image/applied_ftags.png

In this window you'll be able to see which values have been extracted, for the
single tag, from the clip name.
