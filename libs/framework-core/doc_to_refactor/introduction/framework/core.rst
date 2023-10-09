..
    :copyright: Copyright (c) 2022 ftrack

.. _introduction/framework/core:

********************
Core Framework layer
********************

.. highlight:: bash

The core :term:`Framework` module is the backbone of the framework, on which all
other modules rely.

It is in the core were all the interaction with the underlying :term:`host type` is
performed, except when it comes to bootstrap of the DCC.

The module comprises four major components:

 * :ref:`The Host <host>`
 * :ref:`The Client <client>`
 * :ref:`The Engines <engine>`
 * :ref:`Notification and log management <log>`

.. _host:

Host
----

To use the Framework, a :term:`host` must be instantiated with an :term:`event manager`.

The host:

 * Loads the supplied context(task) from the FTRACK_CONTEXTID environment variable.
 * Discovers and validates each tool config against its :term:`schema`.
 * Serves each :term:`Client` with data, handles context change.
 * Run tool_configs by instantiating an :term:`Engine`.
 * Manages logging by listening to client notifications.

.. _client:

Client
------

The :term:`Client` is the user facing component that communicates with host through
the host connection over the ftrack event system.

Clients are categorised into the engine types, see below.

Clients reads the tool config and context from the host, and then commands the host
to run the augmented tool config and its plugins with options collected from the user.

.. _engine:

Engine
------

An Framework :term:`Engine` is a module within the core that defines a function
and require an associated :term:`schema`. The current defined engine types are:

 * Publisher
 * Loader
 * Asset manager
 * Opener

.. _log:

Logs
----

Clients sends notifications to the host which is stored in an internal SQLite database
valid during the session.






