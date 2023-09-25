# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_constants.framework import event

TOPIC_PING = "{}.ping".format(event._BASE_)
TOPIC_PONG = "{}.pong".format(event._BASE_)

TOPIC_TOOL_LAUNCH = "{}.tool.launch".format(event._BASE_)

TOPIC_DOCUMENT_GET = "{}.document.get".format(event._BASE_)
