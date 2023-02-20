..
    :copyright: Copyright (c) 2022 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: upcoming
    .. change:: changed
        :tags: definitions

        Remove ftrack-connect-pipeline-definitions repository.
        Add plugins and definitions on each integration.

    .. change:: changed
        :tags: load_asset

        Init nodes returning dictionary with result key and not run_method key.

    .. change:: changed
        :tags: collector

        Common loader and opener collector return value changed from list to dictionary

    .. change:: changed
        :tags: asset_info

        Asset info has now a create method.

.. release:: 1.2.0
    .. change:: 2022-12-15
    .. change:: new

        Client multithreaded property, as part of 3ds Max integration.

    .. change:: new
        :tags: doc

        Finalised documentation.

.. release:: 1.1.0
    :date: 2022-11-08

    .. change:: new
        :tags: definition

        Definition_object module implemented on client.

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

