
..
    :copyright: Copyright (c) 2015 ftrack

.. _release/migration:

***************
Migration notes
***************

.. _release/migration/upcoming:

Migrate from 1.X to 2.0
=======================

.. _release/migration/upcoming/developer_notes:

Users of a downloaded 
`Connect package <https://www.ftrack.com/portfolio/connect>`_ are
recommended to test the new version before upgrading all workstations.
Especially if you have custom code implemented with the `legacy api`.


Developer notes
---------------
With version 2.0, ftrack-connect drops support for `ftrack-python-legacy-api <https://bitbucket.org/ftrack/ftrack-python-legacy-api>`_, and will stop including backward compatibility modules such as:

 * `ftrack-location-compatibility <https://bitbucket.org/ftrack/ftrack-location-compatibility/src/master/>`_

Legacy locations will have to update to `ftrack-python-api <http://ftrack-python-api.rtd.ftrack.com/en/stable/locations/index.html>`_ syntax in order to keep them working.


Modules and interpreter changes
...............................

With the move to connect2 some of the basic modules and systems have been updated or changed to match the current `VFX platform <https://vfxplatform.com/>`_.:

* Python: 2.7 --> 3.7
* PySide: 1.1.3   --> 1.3.x
* Qt: 4.8 --> 5.14.X
* QtExt: 0.2.2 -> Qt.py 1.3.3
* ftrack-python-api: 1.8.X -> 2.X

Launching applications
......................

The application launch logic has now been moved to the `ftrack-application-launcher <https://bitbucket.org/ftrack/ftrack-application-launcher>`_

.. warning::

    Is likely your application launcher or hooks could have import references to: **ftrack_connect.application**
    This should be replaced with: **ftrack_application_launcher.application**

    For other changes regarding the launch of applications please refer to the `ftrack-application-launcher <https://bitbucket.org/ftrack/ftrack-application-launcher>`_ `documentation <http://ftrack-application-launcher.rtd.ftrack.com/en/latest/>`_.


hooks
.....

Updating hooks mostly means updating the registration function from:


.. code-block:: python

    def register(registry, **kw):
        if registry is not ftrack.EVENT_HANDLERS:
            return


to:

.. code-block:: python

    def register(api_object, **kw):
        if registry is not isinstance(api_object, ftrack.Session):
            return


or will not be discovered anymore.

connector
.........

Due to the changes of python interpreter and pyside version, we also dropping the support for connector integration from within connect itself.

To allow backward compatiblity , the codebase has been moved into a `separate repository <https://bitbucket.org/ftrack/ftrack-connector-legacy.git>`_
And will have to be included as dependency in the integration that requires connector to be present.

.. note::

    Any reference to **ftrack_connect.connector** should be replaced with **ftrack_connector_legacy.connector**

    Eg, from ::

        from ftrack_connect.connector import (
            FTAssetHandlerInstance,
            HelpFunctions,
            FTAssetType,
            FTComponent
        )

    To ::

        from ftrack_connector_legacy.connector import (
            FTAssetHandlerInstance,
            HelpFunctions,
            FTAssetType,
            FTComponent
        )

Migrate from 0.1.19 to 0.1.20
===============================

.. _release/migration/0.1.20/developer_notes:

Developer notes
---------------

The :ref:`ftrack-python-api <ftrack-python-api:introduction>` will from now discover plugins that
are added to the `FTRACK_EVENT_PLUGIN_PATH`.

This means that register functions will be called several times, both for
the ftrack-python-api and the legacy api. To avoid registering a hook multiple
times, developers should validate the register functions arguments.


For event listeners like actions or event processing scripts we do::

    import ftrack

    ...

    def register(registry, **kw):
        '''Register plugin.'''

        # Validate that registry is the correct ftrack.Registry. If not,
        # assume that register is being called with another purpose or from a
        # new or incompatible API and return without doing anything.
        if registry is not ftrack.EVENT_HANDLERS:
            # Exit to avoid registering this plugin again.
            return

        # Register plugin event listener.
        ...

And for location plugins we verify that the registry is a
`ftrack.LOCATION_PLUGINS`::

    import ftrack

    ...

    def register(registry, **kw):
        '''Register plugin.'''

        # Validate that registry is the correct ftrack.Registry. If not,
        # assume that register is being called with another purpose or from a
        # new or incompatible API and return without doing anything.
        if registry is not ftrack.LOCATION_PLUGINS:
            # Exit to avoid registering this plugin again.
            return

        # Register location plugin.
        ...

Plugins for the new Python API must validate that they are called with an
`ftrack_api.session.Session` as a first argument::

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



.. _release/migration/0_1_3:

Migrate from 0.1.2 to 0.1.3
===========================

.. _release/migration/0_1_3/developer_notes:

Developer notes
---------------

.. _release/migration/0_1_3/developer_notes/updated_action_hooks:

Updated action hooks
--------------------

The default :ref:`discover <developing/hooks/action_discover>` and
:ref:`launch <developing/hooks/action_launch>` action hooks has been updated
to support the updated action format in ftrack 3.0.3. If you have created
custom hooks, please make sure they are updated accordingly. In the updated
format of the event data ``selection`` and the contents of ``actionData`` has
been moved to the root, ``event['data']``, level.