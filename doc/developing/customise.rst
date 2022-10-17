..
    :copyright: Copyright (c) 2022 ftrack

.. _developing/customise:

*********
Customise
*********

IDE
***

Internally at ftrack we successfully use PyCharm as our bespoked main developement
tool. Visual Studio would be our second editor of choice, which enables additional
free remote debugging against DCC:s/Maya.


Source Code Management
**********************

It is possible to edit the code and configurations directly without and SCM, but
that will make it very complicated to download and merge in new Framework releases
as they are announced.

The recommended way of doing this is to create your own repositories and then
sync in changes from ftrack by setting adding a remote pointer to our GitHub
repositories. This process is described in detail within the :ref:`tutorial`.


Customisation notes
*******************

Here follows some general customisations guidelines on each Framework module.

ftrack-connect-pipeline
-----------------------

Generally you will never need to touch the core module in order to customize your
pipeline, the most common addon would in case be a custom engine providing new
functionality to the Framework. Another case would be providing shared integration
utility code that can be used across all DCC applications and definition plugins.


ftrack-connect-pipeline-definition
----------------------------------

This module repository is designed to be the place were main customisations will happen
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