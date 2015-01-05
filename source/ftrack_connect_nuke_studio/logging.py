# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from __future__ import absolute_import

import logging

import FnAssetAPI.logging


class FoundryHandler(logging.Handler):
    '''Logging handler to direct messages to Foundry logging API.'''

    def emit(self, record):
        '''Emit *record*.'''
        try:
            message = self.format(record)
            level = record.levelname.lower()
            try:
                handle = getattr(FnAssetAPI.logging, level)
            except AttributeError:
                handle = FnAssetAPI.logging.debug

            handle(message)

        except (KeyboardInterrupt, SystemExit):
            raise

        except:
            self.handleError(record)
