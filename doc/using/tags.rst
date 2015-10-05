..
    :copyright: Copyright (c) 2015 ftrack

.. _using/tags:

****
Tags
****

As part of the project setup process tags are used to link Nuke Studio shots
with sequences, shots and tasks in ftrack. In order for the context tags to
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

.. _using/tags/customising_tag_expressions/modify_for_a_single_session/example_expressions:

Example expressions
^^^^^^^^^^^^^^^^^^^

Sequence and shot separated with underscore
*******************************************

If your shot names contain both the name of the shot and the sequence separated
by an underscore you can use an expression for shot and sequence looking like
this:

========    ====================
Context     Expression
========    ====================
Shot        (\\_)(?P<value>\\.+)
Sequence    (?P<value>\\.+)\\_
========    ====================

Given three shots named **001_A010**, **001_B010** and **002_010** would generate
a hierarchy like:

.. image:: /image/example_expression.png

.. note::
    
    You will need to clear and re-add the tags to the shots in the timeline
    after they are modified.

Persist changes in hook
-----------------------

To make you changes persisted between Nuke Studio sessions you will need to
modify the default hook that loads the tags.

The file to modify is called `context_tags_hook.py` located in different
locations depending on how you are running the Nuke Studio plugin.

If you are using a built ftrack connect package application, the file can
be found in the following locations:

========    ====================
Platform    Path
========    ====================
OS X        /Applications/ftrack-connect.app/Contents/MacOS/resource/ftrack_connect_nuke_studio/application_hook
Windows     C:\Program Files\ftrack-connect package\resource\ftrack_connect_nuke_studio\application_hook
Centos      <Installation directory>/ftrack-connect-package/resource/ftrack_connect_nuke_studio/application_hook
========    ====================

If running from source the hooks can be found in **resource/application_hook/**
in the plugin project folder.

Once you've found the file, open it in your favorite text editor. The file
should look something like this::

    # :coding: utf-8
    # :copyright: Copyright (c) 2015 ftrack

    import logging

    import ftrack


    class ContextTags(object):
        '''Return context tags for Nuke Studio.'''

        def __init__(self, *args, **kwargs):
            '''Initialise context tags hook.'''
            self.logger = logging.getLogger(
                __name__ + '.' + self.__class__.__name__
            )

            super(ContextTags, self).__init__(*args, **kwargs)

        def launch(self, event):
            '''Return context tags.

            Should be list with tags using the format:

                ('tag_id', 'ftrack_type_id', 'regexp')

            '''

            self.logger.debug('Loading context tags from hook.')


            return [
                ('project', 'show', None),
                ('episode', 'episode', '(\w+.)?EP(\d+)'),
                ('sequence', 'sequence', '(\w+.)?SQ(\d+)'),
                ('shot', 'shot', '(\w+.)?SH(\d+)')
            ]

        def register(self):
            '''Register hook.'''
            ftrack.EVENT_HUB.subscribe(
                'topic=ftrack.connect.nuke-studio.get-context-tags',
                self.launch
            )


    def register(registry, **kw):
        '''Register hooks for context tags.'''

        # Validate that registry is instance of ftrack.Registry, if not
        # return early since the register method probably is called
        # from the new API.
        if not isinstance(registry, ftrack.Registry):
            return

        plugin = ContextTags()
        plugin.register()

The part you need to focus on is the one returning the actual tags::

    return [
        ('project', 'show', None),
        ('episode', 'episode', '(\w+.)?EP(\d+)'),
        ('sequence', 'sequence', '(\w+.)?SQ(\d+)'),
        ('shot', 'shot', '(\w+.)?SH(\d+)')
    ]

Edit the value for each context type to desired expression, below is an modified
example with the
:ref:`example expression <using/tags/customising_tag_expressions/modify_for_a_single_session/example_expressions>`::

    return [
        ('project', 'show', None),
        ('episode', 'episode', '(\w+.)?EP(\d+)'),
        ('sequence', 'sequence', '(\_)(?P<value>\.+)'),
        ('shot', 'shot', '(?P<value>\.+)\_')
    ]

In this example the double *\\\\* are replaced with single *\\* due to that
escaping is not needed when the expressions are created from Python code.

.. seealso::
    
    :ref:`event_list/ftrack.connect.nuke-studio.get-context-tags`