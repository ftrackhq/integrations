# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_constants.framework import event

TOPIC_INTEGRATION_ALIVE = "{}.integration-alive".format(event._BASE_)
TOPIC_ACK = "{}.ack".format(event._BASE_)
TOPIC_CONTEXT_DATA = "{}.context-data".format(event._BASE_)
