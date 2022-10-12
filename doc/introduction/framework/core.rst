..
    :copyright: Copyright (c) 2022 ftrack

.. _introduction/framework/core:

*******************
Core Pipeline layer
*******************

.. highlight:: bash

Repository: https://github.com/ftrackhq/ftrack-connect-pipeline.git

The core pipeline Framework module is the backbone of the pipeline, on which all
other modules rely.

It is in the core were all the interaction with the underlaying :term:`host type` is
performed, except when it comes to bootstrap of the DCC.

The core us depending on the :term:`definition` module to be present.

The module composes X major components:

 * The Host
 * The Client
 * The Engines
 * Notification and log management


Host
----

To use the framework, a :term:`host` must be instantiated with an :term:`Event manager`.

The host:

 * Loads the supplied context(task) from the FTRACK_CONTEXTID environment variable.
 * Discovers and validates each definition against its :term:`schema`.
 * Serves each :term:`Client` with data, handles context change.
 * Runs definitions by instantiating an :term:`Engine`.
 * Manages logging by listening to client notifications.


Client
------

The :term:`Client` is the the user facing component that communicates with host through
the host connection over the ftrack event system.

Clients are categorized into the engine types, see below.

Clients reads the definition and context from the host, and then commands the host
to run the augmented definition and its plugins with options collected from the user.


Engine
------

An Framework :term:`Engine` are a module within the core that define a function and require
an associated :term:`schema`. The current defined engine types are:

 * Publisher
 * Loader
 * Asset manager
 * Opener

Logs
----

Clients sends notifications to host which is stored in an internal SQLite database
valid during the session.


Customisation notes
-------------------

Generally you will never need to touch the core module in order to customize your
pipeline, the most common addon would in case be a custom engine providing new
functionality to the framework.

The core would be the place shared integration code that will be used
across all DCC applications and definition plugins, for example functions that
apply statuses or provide common validation and other shared pipeline functionality.





