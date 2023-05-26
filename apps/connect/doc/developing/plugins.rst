..
    :copyright: Copyright (c) 2016 ftrack

.. _developing/plugins:

*******
Plugins
*******

By placing plugin hooks in a discoverable :term:`plugin directory` Connect will
automatically register them. A plugin hook can be used for custom event
processing, actions and location plugins.

In this article we will learn about the structure of a plugin and some best
practices that will help you on your way to become an ftrack Connect ninja.

Structure
=========

A plugin's structure is easy to grasp and relies on a simple directory
structure. The plugin itself is made up of a directory, `my_custom_plugin`, and
inside that a `hook` directory::

    <ftrack-connect-plugin-directory>/
        my_custom_plugin/
            hook/
                my_action.py

When Connect starts it will go over the hook directories in the
:term:`plugin directory` and call register on each of the python scripts in the
hook directory. The `my_action.py` may look something like this::

    import ftrack_api

    ...

    def register(session, **kw):
        '''Register plugin.'''

        # Validate that session is an instance of ftrack_api.Session. If not,
        # assume that register is being called from an incompatible API
        # and return without doing anything.
        if not isinstance(session, ftrack_api.Session):
            # Exit to avoid registering this plugin again.
            return

        # Register plugin event listener.
        ...

This example is using the ftrack-python-api but the concept is valid for the
legacy api as well.

Separating resources
--------------------

Although possible we recommend keeping the `hook` directory as clean as possible
and have any shared modules or other data in a separate directory. This is not
something you have to do but it will make things easier down the line. 

Now let's say that you have a few different actions that share the same modules.
You want to keep things
`DRY <https://en.wikipedia.org/wiki/Don%27t_repeat_yourself>`_
and therefore place them in a resource directory, `resource`::


    <ftrack-connect-plugin-directory>/
        my_custom_plugin/
            hook/
                my_action.py
                another_action.py
            resource/
                my_module/
                    __init__.py

To access the module in the `resource/ folder we need to do some manual work
to allow us to import it. In my_action.py we will add it to the `sys.path`::

    import os
    import sys

    RESOURCE_DIRECTORY = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'resource', 'my_module')
    )

    if RESOURCE_DIRECTORY not in sys.path:
        sys.path.append(RESOURCE_DIRECTORY)

    import my_module

    # Define register and rest of action.
    ...

Separating locations and actions
--------------------------------

We've now learned how to add our own actions in Connect and how to share code
between them. Another type of plugin that we may want to use is a
:term:`location plugin`. Registering it is easy since we only have to put it
into our hook directory.

A location plugin you will typically want to have accessible inside an
:term:`integration` as well. This can be done by adding the path to the
environment when an application is launched,
see :ref:`developing/hooks/application_launch`.

But if we just add it to the hook directory and add the hook directory to the
environment, other Actions may be registered from inside the integration. This
could lead to situations where the `My action` action is registered
twice, one from Connect and one from the integration you've started.

To solve this we recommend separating actions and locations into separate
sub-directories::

    <ftrack-connect-plugin-directory>/
        my_custom_plugin/
            hook/
                action/
                    my_action.py
                    another_action.py
                location/
                    custom_location_plugin.py
            resource/
                my_module/
                    __init__.py

When Connect starts it will traverse the directory structure in the `hook`
directory and register each plugin. This separation will allow us to **only**
add the `<ftrack-connect-plugin-directory>/my_custom_plugin/hook/location/`
directory when launching our integrations.

.. seealso::

    :ref:`Location plugin example <developing/tutorial/adding_a_location>` to
    learn how to use it with application launch hook.
