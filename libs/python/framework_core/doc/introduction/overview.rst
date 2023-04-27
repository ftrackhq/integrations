..
    :copyright: Copyright (c) 2022 ftrack

.. _introduction/overview:

********
Overview
********

Prerequisites
=============

To be able to get the most out of this document, we assume you have basic knowledge of:

 * What ftrack(https://ftrack.com) are and what it does.
 * :term:`Python`, specifically the ftrack Python API.
 * Source code management, specifically Git.
 * :term:`DCC` applications, i.e. Maya, Nuke.
 * ftrack :term:`Connect` 2 Package, installation - app launch - publish and load.


Key design elements and tradeoffs
=================================

The new Framework is designed to be a starting point for developers who seek to
further extend it and use it as a base for a complete studio toolset.

The key design elements are:

 - Modular design; divided into different layered core plugins with well-defined API:s.
 - Schema based definitions; enabling customizable departmentalised processes.
 - Python 3 compatibility; Aligning with latest VFX standards.
 - Host - UI abstraction layer; Enabling non-QT DCC applications or even headless operation.
 - Open source; everyone should be able to contribute to the new Framework.

The new Framework attempts to strike a balance between built-in functionality and
configurability, yet being easy to understand and adopt.

One main design decision was to build a central definition repository, containing
schemas and plugins. The main reason is that all DCC apps usually share a lot of functionality within a medium-large pipeline, keeping this inside each integration plugin would cause a lot of duplicate code needing to be maintained.

Architecture
============

.. image:: image/architecture.svg



ftrack
------

ftrack acts as the database from which the Framework retrieves and stores information.
These are the key entities involved with the Framework:

 * **Context**; The task entity that the DCC work session is bound to, and comes from the task launched within ftrack or Connect.
 * **AssetVersion**; Created during publish, resolved by assembler during load.
 * **Component**; Created during publish, loaded and managed as an asset.



Python API
----------

The :term:`ftrack Python api` is the core dependency of Connect and the Framework,
enabling communication with the ftrack workspace.

The API also comes with the ftrack location system, allowing storage and resource
identifier(file path) aware implementations.





