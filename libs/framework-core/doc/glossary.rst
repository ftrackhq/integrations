..
    :copyright: Copyright (c) 2022 ftrack

********
Glossary
********

.. glossary::

    Application launcher
        The Connect component responsible for discovery and launch of DCC applications,
        relies on the ftrack event system for communication. Further resources:

         * :doc:`ftrack Application Launcher documentation <ftrack-application-launcher:index>`
         * Source code: `<https://github.com/ftrackhq/ftrack-application-launcher.git>`_

    ftrack Python api
        The supported :term:`Python` Application Programmable Interface for
        communicating with the ftrack workspace. Further resources:

         * :doc:`ftrack Python API documentation <ftrack-python-api:index>`
         * Source code: `<https://github.com/ftrackhq/ftrack-python-api>`_

    Client
        The host counterpart interacting with the user, communicates with the host
        through the ftrack Event system. Clients are launched from the DCC module
        through an event, or invoked directly in standalone mode. A client can
        choose to rely on the :term:`UI` module or run standalone. Example of a
        client is the Maya publisher panel.

    Connect
        The ftrack desktop application capable of launching DCC applications,
        publishing files and plugin management. Further resources:

         * :doc:`ftrack Connect documentation <ftrack-connect:index>`
         * Download: `<https://www.ftrack.com/en/portfolio/connect>`_
         * Source code: `<https://github.com/ftrackhq/ftrack-connect.git>`_

    Connect package
        The :term:`Connect package` is Connect built and packaged for a certain
        target platform. typically Windows, Mac OS and Linux. If supplies a default
        Python runtime for running a Connect as an executable, compiled using cx_freeze.

         * :doc:`ftrack Connect Package documentation <ftrack-connect-package:index>`
         * Source code: `<https://github.com/ftrackhq/ftrack-connect-package.git>`_

    DCC
        Digital Content Creation tool, e.g. Maya, 3D Studio Max, Unreal, Blender and
        so on. Each DCC application is defined by a :term:`host type` and has an
        associated Framework plugin. For example the Maya plugin has the following
        resources:

         * `ftrack_connect_pipeline_maya <https://ftrackhq.github.io/ftrack-connect-pipeline-maya/>`_
         * Source code: `<https://github.com/ftrackhq/ftrack-connect-pipeline-maya.git>`_

    Definition
        A :term:`JSON` configuration file defining :term:`Framework` :term:`engine` behaviour -
        which plugins and widgets to use. Is validated against a :term:`schema`.
        Example of a definition is the *Maya Geometry* publisher. Definitions lives within
        the ftrack-connect-pipeline-definition plugin, resources:

         * `ftrack_connect_pipeline_definition <https://ftrackhq.github.io/ftrack-connect-pipeline-definition/>`_
         * Source code: `<https://github.com/ftrackhq/ftrack-connect-pipeline-definition.git>`_

    Engine
        A core Python module driving a specific behaviour within the :term:`Framework`,
        for example publishing or asset management.

    Event manager
        A module responsible sending and receiving ftrack events, through the
        :term:`ftrack Python API`.

    Framework
        A Framework is a structure that you can build software on. It serves as a foundation,
        so you're not starting entirely from scratch. Frameworks are typically associated
        with a specific programming language and are suited to different types of tasks.
        The ftrack pipeline Framework is a set of modules/layers enabling asset publish,
        load, management and other core functionality within an :term:`DCC` application
        or standalone. The core Framework module is called ftrack-connect-pipeline which
        this documentation is part of, source code to be found here:
        `<https://github.com/ftrackhq/ftrack-connect-pipeline.git>`_

    Host
        The central part of the core Framework that discovers and executes definitions
        through engines, handle the context and much more. The host is designed to
        be able to operate in remote mode through the ftrack event system.

    Host type
        The host type is the actual DCC type and is used to identify a DCC module
        and bind a definition to the DCC application. An example host types value
        is **maya**.

    JSON
        JSON is a lightweight format for storing and transporting data, and stands
        for JavaScript Object Notation. For more information
        `<https://www.json.org/>`_

    Plugin
        A module designed to be discovered by the :term:`ftrack Python API`. Plugins
        designed to be discovered by Connect is called Connect plugins and are main
        components of the :term:`Framework`. Framework plugins resides within the
        definition module and are referenced from the with the :term:`definition` JSON
        configurations.

    Plugin manager
        A :term:`Connect` widget that allows discovery and installation of Connect
        plugins, resources:

         * :doc:`ftrack Connect Plugin Manager documentation <ftrack-connect-plugin-manager:index>`
         * Source code: `<https://github.com/ftrackhq/ftrack-connect-plugin-manager.git>`_

    Python
        A programming language that lets you work more quickly and integrate
        your systems more effectively. Often used in creative industries. Visit
        the language website at `<http://www.python.org>`_

    Qt
        The default UI Framework utilised by the Framework, through PySide and
        the Qt.py Python binding module. The correponding Framework module containing
        UI bindings is named ftrack-connect-pipeline-qt, resources:

         * `ftrack_connect_pipeline_qt <https://ftrackhq.github.io/ftrack-connect-pipeline-qt/>`_
         * Source code: `<https://github.com/ftrackhq/ftrack-connect-pipeline-qt.git><`_
         * Qt; `<https://www.qt.io/>`_

    UI
        User Interface of the Framework, built with :term:`Qt`.

    Schema
        A :term:`JSON` configuration defining the strict structure and syntax of
        a :term:`definition` for use with an :term:`engine`.


