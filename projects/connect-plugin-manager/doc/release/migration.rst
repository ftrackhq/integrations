
..
    :copyright: Copyright (c) 2021 ftrack

.. _release/migration:


###############
Migration Notes
###############


.. note::

 If you are porting old custom application hooks, please check first the configuration options if are suitable for you.


changes
=======

If you come from Connect 1.X here you can find some information on how to port your custom launchers into this new plugin.


application hooks
-----------------

Application hooks (launchers) are now hosted in the application-launcher itself and not in the integrations.


integration hooks
-----------------

Integration hooks now provide the data required to be configured and launched, but not the application itself.

environment variables management
--------------------------------

* Environment variable management is now handled from within the integration and not the launcher itself.
  All the imports from ftrack_connect in this regard will not be vailable anymore:

  * ftrack_connect.application.appendPath
  * ftrack_connect.application.prependPath

  this example::

        environment = ftrack_connect.application.appendPath(
            maya_connect_plugins,
            'MAYA_PLUG_IN_PATH',
            environment
        )

  can be easily replaced with the this integration configuration::

       {
         "env": {
             "MAYA_PLUG_IN_PATH.append": maya_connect_plugins
          }
       }




