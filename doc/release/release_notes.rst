..
    :copyright: Copyright (c) 2014 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: Upcoming

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
