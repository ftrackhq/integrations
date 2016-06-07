..
    :copyright: Copyright (c) 2014 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: 0.2.4
    :date: 2016-06-07

    .. change:: fixed
        :tags: Ui

        Schema selection is not in sync with the selected exiting project.

.. release:: 0.2.3
    :date: 2016-05-02

    .. change:: fixed
        :tags: Compatibility

        Plugin doesn't work with Nuke Studio 10.0v1 beta.

.. release:: 0.2.2
    :date: 2016-04-04

    .. change:: fixed
        :tags: Processor

        Handles are not treated correctly when publishing through processors.

.. release:: 0.2.1
    :date: 2016-03-14

    .. change:: changed
        :tags: Processor, Development

        Track item is passed as `application_object` when discovering
        processors.

    .. change:: fixed
        :tags: Create project

        Fix issue where a project cannot be created or updated from the Create
        dialog.

    .. change:: fixed

        Meta data on project is overwritten when an existing project is updated.

.. release:: 0.2.0
    :date: 2015-11-10

    .. change:: new
        :tags: Context template, Context tag

        Introduced :term:`Context templates <Context template>` to simplify
        configuration of project structure on export.

        .. seealso::

            :ref:`Updated export project tutorial <using/export_project>`

        .. note::

            A ftrack server version of 3.3.4 or higher is required.

.. release:: 0.1.4
    :date: 2015-10-16

    .. change:: changed

        Default tag expressions now check for either the previous syntax or
        as-is naming to support a wider variety of use cases out of the box.

        .. note::

            As part of this change the regular expressions must now define a
            "value" named group in order to work.

        .. seealso::

            :ref:`developing/customising_tag_expressions`

    .. change:: changed

        Improved error messages shown when tag expression does not match.

.. release:: 0.1.3
    :date: 2015-10-01

    .. change:: changed

        Propagate thumbnails to tasks on export by default.

        .. seealso::

            :ref:`Thumbnail processor <using/processors/thumbnail>`

    .. change:: changed

        Publish and Proxy processors disabled as default.

    .. change:: changed

        Store reference to outermost ftrack entity in hierarchy when exporting
        track items.

    .. change:: fixed

        Info panel not updating if track item has effect track.

.. release:: 0.1.2
    :date: 2015-09-22

    .. change:: fixed

        Processors not working correct on Windows.

    .. change:: fixed

        Incomplete version number displayed for Nuke Studio application when
        discovered.

    .. change:: fixed

        Changes to context tags hook not being respected.

    .. change:: changed

        Read default export values for `fps` and `resolution` from the
        project settings.

.. release:: 0.1.1
    :date: 2015-09-10

    .. change:: fixed

        Dropping several tags of same type causes export to fail.

    .. change:: fixed

        Segmentation fault when closing down Nuke Studio with plugin loaded.

    .. change:: changed

        Updated default export values for `fps`, `resolution` and `handles`.

    .. change:: fixed
        :tags: Processors, Web playable component

        In and out points not calculated correctly when when offset is used
        on source clip.

.. release:: 0.1.0
    :date: 2015-09-08

    .. change:: new

        Initial release of ftrack connect Nuke studio plugin.
