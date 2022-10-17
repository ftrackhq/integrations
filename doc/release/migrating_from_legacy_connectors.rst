..
    :copyright: Copyright (c) 2022 ftrack

.. _release/migrating_from_legacy_connectors:

************************************
Migrating from old ftrack Connectors
************************************

Why a new Framework?
====================

The legacy DCC Connectors implementing did not carry any means of configuring
engines, publisher or the plugins (e.g. importers, exporters) used within.

Neither were there any possibility to run the integrations in remote mode or easily
customise the look and feel.

The new DCC Framework addresses this by providing a modular approach, configurable
through the pipeline definitions and plugins.



Compability
===========

The new Framework is not backward compatible, which means that previously publish
DCC project files containing tracked assets imported using the legacy integrations
will not be recognised.

