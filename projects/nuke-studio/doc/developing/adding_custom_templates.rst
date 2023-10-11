..
    :copyright: Copyright (c) 2015 ftrack

.. _developing/adding_custom_templates:

***********************
Adding custom templates
***********************

It is possible to customise the templates available when exporting. This is done
by modifying the default hook that loads the templates.

The file to modify is called `context_template_hook.py` and is located in
different locations depending on how you are running the Nuke Studio plugin.

If you are using a built ftrack connect package application, the file can
be found in the following locations:

=========    ====================
Platform     Path
=========    ====================
Mac OS X     /Applications/ftrack-connect.app/Contents/MacOS/resource/ftrack_nuke_studio/application_hook
Windows      C:/\Program Files/\ftrack-connect package/\resource/\ftrack_nuke_studio/\application_hook
CentOS       <Installation directory>/ftrack-connect-package/resource/ftrack_nuke_studio/application_hook
=========    ====================

If running from source the hooks can be found in **resource/application_hook/**
in the plugin project folder.

Once you've found the file, open it in your favorite text editor. The file
should look something like this::

    # :coding: utf-8
    # :copyright: Copyright (c) 2014-2023 ftrack

    import logging
    import ftrack_api


    class ContextTemplates(object):
        '''Return context templates for Nuke Studio.'''

        def __init__(self, session, *args, **kwargs):
            '''Initialise context templates hook.'''
            self.logger = logging.getLogger(
                __name__ + '.' + self.__class__.__name__
            )

            self.session = session

            super(ContextTemplates, self).__init__(*args, **kwargs)

        def launch(self, event):
            '''Return context templates.'''
            # Define tag regular expressions.
            return [{
                'name': 'Classic, sequence and shot',
                'description': (
                    'Match SQ or SH and any subsequent numbers. '
                    'Example: SQ001_SH010 will be matched as Sequence with name '
                    '001 and a shot named 010.'
                ),
                'expression': '{_:SQ|sq}{Sequence:\d+}{_:.+(SH|sh)}{Shot:\d+}'
            }, {
                'name': 'Classic, shot only',
                'description': (
                    'Match SH and any subsequent digits. '
                    'Example: vfx_SH001 will match 001.'
                ),
                'expression': '{_:SH|sh}{Shot:\d+}'
            }, {
                'name': 'Full name, shot only',
                'description': (
                    'Match entire clip name. '
                    'Example: vfx_SH001 will match vfx_SH001.'
                ),
                'expression': '{Shot:.+}'
            }]

        def register(self):
            '''Register hook.'''
            self.session.event_hub.subscribe(
                'topic=ftrack.connect.nuke-studio.get-context-templates',
                self.launch
            )


    def register(session, **kw):
        '''Register plugin. Called when used as an plugin.'''
        # Validate that session is an instance of ftrack_api.Session. If not,
        # assume that register is being called from an old or incompatible API and
        # return without doing anything.
        if not isinstance(session, ftrack_api.session.Session):
            return

        plugin = ContextTemplates(
            session
        )

        plugin.register()
The part you need to focus on is the one returning the actual templates::

    return [{
        'name': 'Classic, sequence and shot',
        'description': (
            'Match SQ or SH and any subsequent numbers. '
            'Example: SQ001_SH010 will be matched as Sequence with name '
            '001 and a shot named 010.'
        ),
        'expression': 'SQ{Sequence:\d+}{_:.+}H{Shot:\d+}'
    }, {
        'name': 'Classic, shot only',
        'description': (
            'Match SH and any subsequent digits. '
            'Example: vfx_SH001 will match 001.'
        ),
        'expression': 'SH{Shot:\d+}'
    }, {
        'name': 'Full name, shot only',
        'description': (
            'Match entire clip name. '
            'Example: vfx_SH001 will match vfx_SH001.'
        ),
        'expression': '{Shot:.+}'
    }, ...]

Each item in the list represents a template and you can either modify one of
the existing templates or add a new one.

A template has the structure::
    
    dict(
        name='Name of template',
        description='Description of template',
        expression='The expression used to match the clip name'
    )

The `name` and `description` are regular strings and will be displayed in the
interface and can contain HTML if desired. The `expression` use a flavor of
`regular expressions <https://docs.python.org/2/library/re.html>`_ to define
the object types to match.

The expression needs to contain a named group matching the name of the object
type. Named groups are defined within curly brackets
`{ObjectTypeName:Expression}` starting with the name followed by the expression.

If you for example want to create a template which matches episodes and shots
it could look something like this::

    dict(
        name='Episode and shot',
        description='Match `EP` or `SH` and any subsequent numbers',
        expression='EP{Episode:\d+}_SH{Shot:\d+}'
    )

This template will match clips named `EP001_SH001`, `EP001_SH002` and so on.

To exclude things in the name you need to use our custom exclude group with
name `_`.

As you can see in the `Classic, sequence and shot` expression it use this
group in the middle, `{_:.+}`. This enables the name to have any characters
in between the `SQ` and `SH`. The `_` group can be used several times in the
same expression.

.. _developing/customise_template_output:
