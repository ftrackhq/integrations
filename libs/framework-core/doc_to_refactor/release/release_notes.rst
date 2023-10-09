..
    :copyright: Copyright (c) 2022 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: 1.3.2
    :date: 2023-08-1

    .. change:: changed

        First release from monorepo CI

.. release:: 1.3.1
    :date: 2023-06-15

    .. change:: changed
        :tags: scm

        Moved repository to monorepo package libs/framework-core.

.. release:: 1.3.0
    :date: 2023-04-05

    .. change:: fix
        :tags: asset manager

        Aligned load method on changing version, fixing bug where and tracked and then loaded asset could not have its version changed and stay loaded.

    .. change:: changed
        :tags: tool_configs

        Remove ftrack-connect-pipeline-tool_configs repository.
        Add plugins and tool_configs on each integration.

    .. change:: changed
        :tags: load_asset

        Init nodes returning dictionary with result key and not run_method key.

    .. change:: changed
        :tags: collector

        Common loader and opener collector return value changed from list to dictionary

    .. change:: changed
        :tags: asset_info

        Asset info has now a create method.

    .. change:: fix

       Ability to disable stages and plugins.

.. release:: 1.2.0
    :date: 2022-12-15

    .. change:: new

        Client multithreaded property, as part of 3ds Max integration.

    .. change:: new
        :tags: doc

        Finalised documentation.

.. release:: 1.1.0
    :date: 2022-11-08

    .. change:: new
        :tags: tool_config

        Tool_config_object module implemented on client.

    .. change:: fix
        :tags: dependencies

        Fix markdown error on pipeline

    .. change:: changed
        :tags: context

        Rewired the context event flow to support standalone delayed context set

    .. change:: changed
        :tags: doc

        Added release notes and API documentation

    .. change:: changed
        :tags: utils

        Added shared safe_string util function

    .. change:: changed
        :tags: doc

        Fixed AM client docstrings

.. release:: 1.0.1
    :date: 2022-08-01

    .. change:: new

        Initial release

