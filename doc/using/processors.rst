..
    :copyright: Copyright (c) 2015 ftrack

.. _using/processors:

**********
Processors
**********

After the project structure is created a series of processors run for each of
the Nuke Studio shots. The processors are small scripts that renders plates,
proxies, thumbnails and web playeable clips. They are written in Python and easy
to extend.

.. seealso::

    To learn more about developing your own custom processors please refer to
    this :ref:`article <developing/processors>`.

Export project dialog
=====================

To see which processors will be running you can click on an item in the Export
project dialog. This will show the name of the asset being published and the
components.

.. image:: /image/processors.png

In the image above we can see that four processors will run for the selected
shot: Ingest proxy, Ingest, Review and Thumbnail. These are the four default
processers that are packaged with the ftrack Nuke Studio plugin.

Thumbnail
=========

The thumbnail will be generate from the source material and set as thumbnail on
the version and the shot. If the processor is tweaked to run on a task it will
also set the thumbnail on that task.

Ingest / Plate
==============

The plate is rendered from the source material based on the configured FPS and
Resolution. See :ref:`project settings <using/project_settings>`

Proxy
=====

The proxy is a lower resolution version of the ingest. By default the proxy is 
half the resolution of the ingest.

Review
======

Along with the other components a web reviewable video clip is generated.

.. note::

    For the default web reviewable to work the
    :term:`ftrack server <ftrack server>` must be hosted by ftrack. Local
    installations will need to modify this hook in order for it work properly.
