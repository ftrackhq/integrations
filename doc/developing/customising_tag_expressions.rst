..
    :copyright: Copyright (c) 2015 ftrack

.. _developing/customising_tag_expressions:

***************************
Customising tag expressions
***************************

It is possible to customise the tag expressions used when matching the clip
names to work with your own naming convention. This can be done in two
different ways, either per session or persisted in Connect.

Modify for a single session
---------------------------

If you temporarily want to change the expression used when matching the clip
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
    
    :ref:`Example expressions <developing/customising_tag_expressions/example_expressions>`

.. seealso::

    https://docs.python.org/2/howto/regex.html

.. note::
    
    You will need to clear and re-add the tags to the clips in the timeline
    after the tags are modified.

Persist changes in hook
-----------------------

To persist changes to the tag expressions between Nuke Studio sessions you will
need to modify the default hook that loads the tags.

The file to modify is called `context_tags_hook.py` located in different
locations depending on how you are running the Nuke Studio plugin.

If you are using a built ftrack connect package application, the file can
be found in the following locations:

========    ====================
Platform    Path
========    ====================
OS X        /Applications/ftrack-connect.app/Contents/MacOS/resource/ftrack_connect_nuke_studio/application_hook
Windows     C:/\Program Files/\ftrack-connect package/\resource/\ftrack_connect_nuke_studio/\application_hook
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
                ('episode', 'episode', 'EP(?P<value>\d+)|(?P<value>.+)'),
                ('sequence', 'sequence', 'SQ(?P<value>\d+)|(?P<value>.+)'),
                ('shot', 'shot', 'SH(?P<value>\d+)|(?P<value>.+)')
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
        ('episode', 'episode', 'EP(?P<value>\d+)|(?P<value>.+)'),
        ('sequence', 'sequence', 'SQ(?P<value>\d+)|(?P<value>.+)'),
        ('shot', 'shot', 'SH(?P<value>\d+)|(?P<value>.+)')
    ]

Edit the value for each context type to desired expression, below is a modified
example with the
:ref:`example expression <developing/customising_tag_expressions/example_expressions>`::

    return [
        ('project', 'show', None),
        ('episode', 'episode', 'EP(?P<value>\d+)|(?P<value>.+)'),
        ('sequence', 'sequence', r'(\_)(?P<value>\.+)'),
        ('shot', 'shot', r'(?P<value>\.+)\_')
    ]

In this example we're returning raw string to avoid the expression being
escaped.

.. seealso::
    
    :ref:`event_list/ftrack.connect.nuke-studio.get-context-tags`

.. _developing/customising_tag_expressions/example_expressions:

Example expressions
-------------------

Sequence and shot separated with underscore
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your shot names contain both the name of the shot and the sequence separated
by an underscore you can use an expression for shot and sequence looking like
this:

========    ====================
Context     Expression
========    ====================
Sequence    (?P<value>\\.+)\_
Shot        (\_)(?P<value>\.+)
========    ====================

Given three shots named **001_A010**, **001_B010** and **002_010** would generate
a hierarchy like:

.. image:: /image/example_expression.png
