..
    :copyright: Copyright (c) 2022 ftrack

********
Glossary
********

.. glossary::

    Application launcher
        The Connect component responsible for discovery and launch of DCC applications,
        relies on the ftrack event system for communication. The plugin source code
        can be obtained here: https://github.com/ftrackhq/ftrack-application-launcher.git

    ftrack Python api
        The supported :term:`Python` Application Programmable Interface for
        communicating with the ftrack workspace. The source code lives here: https://github.com/ftrackhq/ftrack-python-api

    Client
        The host counterpart interacting with the user, communicates with the host
        through the ftrack Event system. Clients are launched from the DCC module
        through an event, or invoked directly in standalone mode. A client can
        choose to rely on the :term:`UI` module or run standalone. Example of a
        client is the Maya publisher panel.

    Connect
        The ftrack desktop application capable of launching DCC applications,
        publishing files and plugin management. For ftrack Connect documentation
        and downloads, please head over here: https://www.ftrack.com/en/portfolio/connect
        The Connect source code can be obtained here: https://github.com/ftrackhq/ftrack-connect.git

    Connect package
        The :term:`Connect package` is Connect built and packaged for a certain
        target platform. typically Windows, Mac OS and Linux. If supplies a default
        Python runtime for running a Connect as an executable, compiled using cx_freeze.
        Source code can be found here: https://github.com/ftrackhq/ftrack-connect-package.git

    DCC
        Digital Content Creation tool, e.g. Maya, 3D Studio Max, Unreal, Blender and
        so on. Each DCC application has an associated framework plugin, the current ones
        defined are:

         * Maya; https://github.com/ftrackhq/ftrack-connect-pipeline-maya.git
         * Nuke; https://github.com/ftrackhq/ftrack-connect-pipeline-nuke.git
         * Houdini; https://github.com/ftrackhq/ftrack-connect-pipeline-houdini.git

    Definition
        A :term:`JSON` configuration file defining :term:`Framework` :term:`engine` behaviour -
        which plugins and widgets to use. Is validated against a :term:`schema`.
        Example of a definition is the *Maya Geometry* publisher. Definitions lives within
        the ftrack-connect-pipeline-definition plugin, source code can be found here:
        https://github.com/ftrackhq/ftrack-connect-pipeline-definition.git

    Engine
        A core Python module driving a specific behaviour within the :term:`Framework`,
        for example publishing or asset management.

    Event manager
        A module responsible sendimg and receiving ftrack events, through the
        :term:`ftrack Python API`.

    Framework
        A framework is a structure that you can build software on. It serves as a foundation,
        so you're not starting entirely from scratch. Frameworks are typically associated
        with a specific programming language and are suited to different types of tasks.
        The ftrack pipeline Framework is a set of modules/layers enabling asset publish,
        load, management and other core functionality within an :term:`DCC` application
        or standalone. The core framework module is called ftrack-connect-pipeline, with
        source code to be found here: https://github.com/ftrackhq/ftrack-connect-pipeline.git

    Host
        The central part of the core framework that discovers and executes definitions
        through engines, handle the context and much more. The host is designed to
        be able to operate in remote mode through the ftrack event system.

    Host type
        The host type is the actual DCC type and is used to identify a DCC module
        and bind a definition to the DCC application. An example host types value
        is **maya**.

    JSON
        JSON is a lightweight format for storing and transporting data, and stands
        for JavaScript Object Notation. For more information
        https://www.json.org/

    Plugin
        A module designed to be discovered by the :term:`ftrack Python API`. Plugins
        designed to be discovered by Connect is called Connect plugins and are main
        components of the :term:`Framework`. Framework plugins resides within the
        definition module and are referenced from the with the :term:`definition` JSON
        configurations.

    Python
        A programming language that lets you work more quickly and integrate
        your systems more effectively. Often used in creative industries. Visit
        the language website at http://www.python.org

    Qt
        The default UI framework utilised by the Framework, through PySide and
        the Qt.py Python binding module. The corresonding Framework module containing
        UI bindings is named ftrack-connect-pipeline-qt and its source code can be
        found here: https://github.com/ftrackhq/ftrack-connect-pipeline-qt.git

        Further resources:
         * Qt; https://www.qt.io/
         * PySide2; https://pypi.org/project/PySide2/
         * Qt.py; https://github.com/mottosso/Qt.py

    UI
        User Interface of the Framework, built with :term:`Qt`.

    Schema
        A :term:`JSON` configuration defining the strict structure and syntax of
        a :term:`definition` for use with an :term:`engine`.


