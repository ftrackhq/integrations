..
    :copyright: Copyright (c) 2015 ftrack

.. _release/migration:

***************
Migration notes
***************

.. _release/migration/upcoming:


Moving from 1.X to 2.X
======================

This new release is a complete rewrite of the plugin, and introduces different
workflow and breaking changes. Is therefore suggested, as minimum, to
`cleanup the project from any custom ftrack tag <https://learn.foundry.com/
nuke/content/timeline_environment/usingtags/removing_tags.html>`_,
and remove any previously saved task and processor presets users might have been
saving. Is prefereable though to create a new project from scratch so no old
settings and hidden tags are retained.

Custom Processors
-----------------
With this new integration we have been moving away from separated processors and task logic
and we now rely on the natural Nuke Studio / Hiero ones.
If you had any custom processor written for the previous version, it is suggested
to see at first if the customisation of the settings of the new default ftrack tasks and processors
is enough.


Moving to the new API
=====================

The Connect nuke studio integration has changed to use the `ftrack-python-api`
instead of the `legacy api`. Since custom locations are not compatible between
the different APIs all users running from source with custom locations for
the `legacy api` must either:

#.  Use the
    `Location compatibility layer <https://bitbucket.org/ftrack/ftrack-location-compatibility/>`_
    by putting it's resource folder on the `FTRACK_EVENT_PLUGIN_PATH`.
#.  Or, re-write the location using the `ftrack-python-api`.

for more information about the migration process please look at the main `ftrack-connect`
`Documentation <http://ftrack-connect.rtd.ftrack.com/en/latest/release/migration.html>