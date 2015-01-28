# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

'''Event handlers.'''


def hieroToNukeAddClip(bridge, hieroClip, fileOrRef, readNode, nukeScript):
    '''Add ftrack information to *readNode* in Nuke.'''
    reference = None

    if bridge.isEntityReference(fileOrRef):
        reference = fileOrRef

    elif hasattr(hieroClip, 'entityReference'):
        clipReference = hieroClip.entityReference()
        if bridge.isEntityReference(clipReference):
            reference = clipReference

    if reference:
        obj = bridge.getEntityById(reference)
        assetVersion = obj.getVersion()
        asset = assetVersion.getAsset()

        readNode.addTabKnob('ftracktab', 'ftrack')
        readNode.addInputTextKnob(
            'componentId', 'componentId', value=obj.getEntityRef()
        )
        readNode.addInputTextKnob(
            'componentName', 'componentName', value=obj.getName()
        )
        readNode.addInputTextKnob(
            'assetVersionId', 'assetVersionId',
            value=assetVersion.getEntityRef()
        )
        readNode.addInputTextKnob(
            'assetVersion', 'assetVersion', value=assetVersion.getVersion()
        )
        readNode.addInputTextKnob(
            'assetName', 'assetName', value=asset.getName()
        )
        readNode.addInputTextKnob(
            'assetType', 'assetType', value=asset.getType().getShort()
        )


def hieroToNukeAddWrite(bridge, hieroClip, fileOrRef, writeNode, nukeScript):
    '''Add ftrack information to *writeNode* in Nuke.'''
    # This import is inlined as hiero may not always be importable (such as
    # when using the test ui).
    from hiero.core import nuke

    writeNode.addTabKnob('ftracktab', 'ftrack')

    # Ensure the component name is 'main' rather than the name of the write
    # node as that can cause problems later.
    writeNode.addInputTextKnob('fcompname', 'componentName', value='main')

    ftrackPublishNode = nuke.GroupNode('ftrackPublish')
    inputNode = nuke.Node('Input', inputs=0)
    ftrackPublishNode.addNode(inputNode)

    outputNode = nuke.Node('Output', inputs=1)
    outputNode.setInputNode(0, inputNode)
    ftrackPublishNode.addNode(outputNode)

    ftrackPublishNode.addInputTextKnob('fpubinit', 'fpubinit', value='False')

    if nukeScript:
        nukeScript.addNode(ftrackPublishNode)

    ftrackPublishNode.setInputNode(0, writeNode)


def refsFromNukeNodes(bridge, nodes, entityRefSet):
    '''Add entity references discovered on *nodes* to *entityRefSet*.'''
    for node in nodes:
        for knob in node.knobs().values():
            # Currently, the reference is stored as componentId.
            if knob.name() != 'componentId':
                continue

            value = knob.getValue()
            if bridge.isEntityReference(value):
                entityRefSet.add(value)
