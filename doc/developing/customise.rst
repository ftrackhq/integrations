..
    :copyright: Copyright (c) 2022 ftrack

.. _developing/customise:

*********
Customise
*********

Here follows some general customisations guidelines on each Framework module.

ftrack-connect-pipeline
-----------------------

Generally you will never need to touch the core module in order to customise your
pipeline, the most common addon would in case be a custom engine providing new
functionality to the Framework. Another case would be providing shared integration
utility code that can be used across all DCC applications and definition plugins.


ftrack-connect-pipeline-definition
----------------------------------

This module repository is designed to be the place where main customisations will happen
within the resource directory.


ftrack-connect-pipeline-qt
--------------------------

This module is the repository were :term:`Qt` widgets, images and fonts resides,
together with the base style of integrations. Modify this repository on order to
augment the look and feel of the integrations, or if you seek to supply new widgets
that is to be used across DCC integrations.


ftrack-connect-pipeline-host_type
---------------------------------

The module repository were you would make changes to each individual DCC
application when it comes to the ftrack menu, clients and base plugins
and widgets that are referenced from within the definition.


Tutorial
********

We provide a comprehensive :ref:`tutorial` on how to customise the Framework in practise,
with fully working source code attached.