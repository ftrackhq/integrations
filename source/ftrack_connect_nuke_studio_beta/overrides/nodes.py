from hiero.core.nuke import ReadNode


def register_nodes_overrides():

    if not hasattr(ReadNode, '_default_init'):
        ReadNode._default_init = ReadNode.__init__
        ReadNode.__init__ = ftrack_ReadNode_init

    if


def ftrack_ReadNode_init(self, *args, **kwargs):
    ReadNode._default_init(self, *args, **kwargs)
    self.addTabKnob("ftracktab", "ftrack")
    # self.addInputTextKnob("componentId", "componentId", value=obj.getEntityRef())
    # self.addInputTextKnob("componentName", "componentName", value=obj.getName())
    # self.addInputTextKnob("assetVersionId", "assetVersionId", value=assetVersion.getEntityRef())
    # self.addInputTextKnob("assetVersion", "assetVersion", value=assetVersion.getVersion())
    # self.addInputTextKnob("assetName", "assetName", value=asset.getName())
    # self.addInputTextKnob("assetType", "assetType", value=asset.getType().getShort())




