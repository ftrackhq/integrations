..
    :copyright: Copyright (c) 2022 ftrack

.. _tutorial/introduction:

************
Introduction
************

In this section, we are getting our hands dirty and showing an example on how the
new Framework can be customised to a studio specific needs.

The aim with this exercise is to inspire the reader on what can be achieved -
build a VFX studio pipeline that aids the artists to working the right
way, with correct file naming convention, minimising tedious and error prone tasks.


..  important::

    There is currently no GUI approach to configuring the Framework, and no way to
    provide separate builds and configurations per project or context in general.
    This is subject to be improved with the next major release of the Framework and
    Connect.

Checkout documentation code
***************************

The source code present in this tutorial, as fully working examples, can be found
in the *resource* directory.


The tool we are about to build
******************************

In this tutorial, we will first show how to apply a custom file structure that
will apply to all API location based file operations - Connect and DCC integrations.

Next we target Maya and extend the Framework integration with a set of tools:

 * DCC bootstrap extension - have the latest snapshot opened, or a new one generated from template and saved.
 * Custom loader - load a previewable (Quicktime) onto a camera image plane in Maya.
 * Post a message on Slack upon publish, with a thumbnail attached.
 * Add a custom tool to the ftrack menu.

We also walk you through the process of customising the launch of DCC applications -
how to constrain application launch to a certain department (e.g. task type) and how
to set environment variables plus add additional arguments.

At the end we go more in depth on how to build, deploy and maintain the customised
Framework pipeline within the studio.


Disclaimer
**********

All code has been tested and provided as is, use it at your own risk as ftrack
cannot be held responsible for any damage caused by adopting code and instructions
supplied in this tutorial.





