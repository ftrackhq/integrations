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
         * Source code: `<https://github.com/ftrackhq/integrations/projects/application-launcher>`_

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
         * Source code: `<https://github.com/ftrackhq/integrations/apps/connect>`_

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

         * `ftrack_framework_maya <https://ftrackhq.github.io/integrations/projects/framework-maya/>`_
         * Source code: `<https://github.com/ftrackhq/integrations/projects/framework-maya>`_

    Tool_config
        A :term:`JSON` configuration file defining :term:`Framework` :term:`engine` behaviour -
        which plugins and widgets to use. Is validated against a :term:`schema`.
        Example of a tool_config is the *Maya Geometry* publisher. Tool_configs lives within
        the resource/tool_configs folder within each framework plugin.

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
        or standalone. The core Framework module is called framework-core which
        this documentation is part of, source code to be found here:
        `<https://github.com/ftrackhq/integrations/libs/framework-core>`_

    Host
        The central part of the core Framework that discovers and executes tool_configs
        through engines, handle the context and much more. The host is designed to
        be able to operate in remote mode through the ftrack event system.

    Host type
        The host type is the actual DCC type and is used to identify a DCC module
        and bind a tool_config to the DCC application. An example host types value
        is **maya**.

    JSON
        JSON is a lightweight format for storing and transporting data, and stands
        for JavaScript Object Notation. For more information
        `<https://www.json.org/>`_

    Monorepo
        A way to organise code in a single repository, to benefit from a common
        build and testing process both locally and on a CI server. The ftrack integrations
        monorepo is were all :term:`Framework` code resides:
        `<https://github.com/ftrackhq/integrations.git>`_

    Plugin
        A module designed to be discovered by the :term:`ftrack Python API`. Plugins
        designed to be discovered by Connect is called Connect plugins and are main
        components of the :term:`Framework`. Framework plugins resides within the
        tool_config module and are referenced from the with the :term:`tool_config` JSON
        configurations.

    Plugin manager
        A :term:`Connect` widget that allows discovery and installation of Connect
        plugins, resources:

         * :doc:`ftrack Connect Plugin Manager documentation <ftrack-connect-plugin-manager:index>`
         * Source code: `<https://github.com/ftrackhq/integrations/projects/connect-plugin-manager>`_

    Python
        A programming language that lets you work more quickly and integrate
        your systems more effectively. Often used in creative industries. Visit
        the language website at `<http://www.python.org>`_

    Qt
        The default UI Framework utilised by the Framework, through PySide and
        the Qt.py Python binding module. The correponding Framework module containing
        UI bindings is named ftrack-connect-pipeline-qt, resources:

         * `ftrack_framework_qt <https://ftrackhq.github.io/integrations/libs/framework-qt/>`_
         * Source code: `<https://github.com/ftrackhq/integrations/libs/framework-qt>`_
         * Qt; `<https://www.qt.io/>`_

    UI
        User Interface of the Framework, built with :term:`Qt`.

    Schema
        A :term:`JSON` configuration defining the strict structure and syntax of
        a :term:`tool_config` for use with an :term:`engine`.


