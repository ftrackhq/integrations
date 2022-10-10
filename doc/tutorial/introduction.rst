..
    :copyright: Copyright (c) 2022 ftrack

.. _tutorial/introduction:

************
Introduction
************

In this section, we are getting our hands dirty and showing an example on how the
new framework can be customised to a studio specific needs.

The aim with this exercise is to inspire the reader on what can be achieved with
Connect - build a VFX studio pipeline that aids the artists to working the right
way, with correct file naming convention, minimising tedious and error prone tasks.


.. important::

    There is currently no GUI approach to configuring the framework, and no way of
    provide separate builds and configurations per project or context in general.
    This is subject to be improved with the next major release of the framework.


Checkout documentation code
---------------------------

The source code from this documentation, as fully working examples, can be found
in the *resource* directory.


The tool we are about to build
------------------------------

In this example, we implement a streamlined tool for the animation department so they can:

 * DCC bootstrap extension - launch application from ftrack and have the latest snapshot opened, or a new one generated from template and saved.
 * Custom loader - load a previewable (Quicktime) onto a camera image plane in Maya.
 * Custom publisher - publish the Maya node graph as XML, with options, into the studio custom folder structure.
 * Post a message on Slack with an animation playable for review.
 * Add a custom tool to the ftrack menu.

We also walk you through the process of customising the launch of DCC applications -
how to constrain application launch to a certain department (e.g. task type) and how
to set environment variables and add additional arguments.

On top of that we describe how to implement a custom folder structure and finally how
to build, deploy and maintain the customised framework pipeline within the studio.


Prequisites
-----------

TBC

