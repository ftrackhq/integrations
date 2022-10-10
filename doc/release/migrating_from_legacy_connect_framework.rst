..
    :copyright: Copyright (c) 2022 ftrack

.. _release/migrating_from_legacy_connect_framework:

************************************
Migrating from old Connect framework
************************************

Why a new Framework?
====================

The legacy DCC framework did not carry any means of configuring engines, publisher
or the plugins (e.g. importers, exporters) used within.

Neither were there any possibility to run the framework in remote mode or easily
customise the look and feel.

The new DCC framework addresses this by providing a modular approach, configurable
through the pipeline :term:`definition`s.



Compability
===========

The new framework is not backward compatible, which means that previously publish
DCC project files containing tracked assets imported using the legacy integrations
will not be recognised.

