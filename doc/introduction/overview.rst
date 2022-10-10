..
    :copyright: Copyright (c) 2022 ftrack

.. _introduction/overview:

********
Overview
********

TBC


*********************************
Key design elements and tradeoffs
*********************************

Connect 2 comes with a new framework, designed to be a starting point for developers
who seek to further extend it and use it as a base for a complete studio toolset.
The key design elements are:

 - Modular design; divided into different layered core plugins with well-defined API:s.
 - Schema based definitions; enabling customizable departmentalised processes.
 - Python 3 compatibility; Aligning with latest VFX standards.
 - Host - UI abstraction layer; Enabling non-QT DCC applications or even headless operation.
 - Open source; everyone should be able to contribute to the new framework.

The new framework attempts to strike a balance between built-in functionality and
configurability, yet being easy to understand and adopt.

One main design decision was to build a central definition repository, containing
schemas and plugins. The main reason is that all DCC apps usually share a lot of functionality within a medium-large pipeline, keeping this inside each integration plugin would cause a lot of duplicate code needing to be maintained.

