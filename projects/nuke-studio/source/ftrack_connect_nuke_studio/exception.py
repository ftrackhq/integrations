# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import sys
import traceback


class Error(Exception):
    '''ftrack specific error.'''

    default_message = 'Unspecified error occurred.'

    def __init__(self, message=None, details=None):
        '''Initialise exception with *message*.

        If *message* is None, the class 'default_message' will be used.

        *details* should be a mapping of extra information that can be used in
        the message and also to provide more context.

        '''
        if message is None:
            message = self.default_message

        self.message = message
        self.details = details
        if self.details is None:
            self.details = {}

        self.traceback = traceback.format_exc()

    def __str__(self):
        '''Return string representation.'''
        keys = {}
        for key, value in self.details.iteritems():
            if isinstance(value, unicode):
                value = value.encode(sys.getfilesystemencoding())
            keys[key] = value

        return str(self.message.format(**keys))


class ValidationError(Error):
    '''Raise when an validation error occurs.'''

    default_message = 'Validation error.'


class PermissionDeniedError(Error):
    '''Raise when permission is denied.'''

    default_message = 'Permission denied.'


class TemplateError(Error):
    '''Raise when an template error occurs.'''

    default_message = 'Template error'
