..
    :copyright: Copyright (c) 2022 ftrack

.. _introduction/connect:

*******
Connect
*******

:term:`Connect` is the ftrack desktop GUI application enabling DCC application launch
and publishing. Connect locates the Framework plugins, and together with the
:term:`Application launcher` plugin, enables discovery and launch of DCC applications.

The Framework modules are connect plugins, which means that need to implement a launch
hook containing the logic to discover and launch the DCC application.


Application launcher
====================

The :term:`Application launcher` is a Connect plugin responsible for discovery and
launch of DCC applications.

The application launcher reads its :term:`JSON` configuration files and performs
discovery of :term:`DCC` applications.

The tutorial part of this documentation shows an example on how to modify the
configuration.

For more information on how the application launcher works, please refer to the
:doc:`ftrack Application Launcher documentation <ftrack-application-launcher:index>`.


Connect Package
===============

The :term:`Connect package` is a build of Connect, shipped as an installer, available
for each major operating system platform.



