..
    :copyright: Copyright (c) 2015 ftrack

.. _using/tags:

****
Tags
****

As part of the project setup process tags are used to link Nuke Studio shots
with sequences, shots and tasks in ftrack and in order for the context tags to
successfully extract the names from the shot, these have to be named matching
the expression defined in the tag.

Basic tagging
=============

The tags can be found by opening the tag window,
:menuselection:`Window --> Tags` and navigate to the *ftrack folder*.

.. image:: /image/tags.png

By default the different context tags in the *ftrack folder* will match:

* Shot: **SH** followed by any numbers. If not found the entire shot name will be used.
* Sequence: **SQ** followed by any numbers. If not found the entire shot name will be used.
* Episodes: **EP** followed by any numbers. If not found the entire shot name will be used.

For example, if a shot named *SQ001_SH010* and has the shot and sequence tag
applied it will yield a structure like this:

.. image:: /image/hierarchy_first.png

If the clip instead is named *SQ001_010* the shot tag will match the entire 
name and yield a hierarchy looking like this:

.. image:: /image/hierarchy_second.png

.. note::

    The task type tags will generate tasks on the context named by the type
    and are not bound to the name of the shot.

Rename shots
------------

The Rename Shots dialog can be used to multi-edit the name of the the selected
shots. It is located in the context menu under
:menuselection:`Editorial --> Rename Shots (Alt+Shift+/)`

.. image:: /image/rename.png

.. note::

    Rename shots works on a selection of shots. The ### will be replaced by the
    increment value and the number of selected shots.

Apply tags
----------

When the shots are correctly named, you are ready to start the tagging process.
Select the contexts you want to create and drop them on your clips.

.. image:: /image/ftag_drop.png

To review which tags have been applied just click on the tag icon on the clip.

.. image:: /image/applied_ftags.png

In this window you'll be able to see which values have been extracted, for the
single tag, from the clip name.

When done tagging continue on with :ref:`exporting your project <using/export_project>`.

Customising tag expressions
===========================

It is possible to customise the tag expressions used when matching the clip
names to work with your own naming convention. This can be done it two
different ways, either per session or persisted in Connect.

Modify for a single session
---------------------------

If you temporary want to change the expression used when matching the clip
names you can do it from within Nuke Studio.

Open the tag window, :menuselection:`Window --> Tags` and navigate to the
*ftrack folder* and double click on the tag you want to modify to bring up the
edit window.

.. note::

    Changes made in the tag window will be restored once Nuke Studio is
    restarted.

.. image:: /image/edit_tag.png

In the edit window you need to edit the **re** attribute in the **data** list.

The regular expression **must** define a named group called ``value`` which will
be used as the value when the expression matches. The expression is used in a
search, so use anchors if appropriate for exact matches.

.. seealso::

    https://docs.python.org/2/howto/regex.html

Example expressions
-------------------

Sequence and shot separated with underscore
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your shot names contain both the name of the shot and the sequence separated
by an underscore you can use an expression for shot and sequence looking like
this:

========    ==================
Context     Expression
========    ==================
Shot        (\\_)(?P<value>\\.+)
Sequence    (?P<value>\\.+)\\_
========    ==================

Given three shots named **001_A010**, **001_B010** and **002_010** would generate
a hierarchy like:

.. image:: /image/example_expression.png

.. note::
    
    You will need to clear and re-add the tags to the shots in the timeline
    after they are modified.

