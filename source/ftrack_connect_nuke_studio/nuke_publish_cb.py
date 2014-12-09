# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import nuke
import ftrack
from clique import Collection

def createComponent():
    ''' Create component callback for nuke write nodes.
    This callback relies on two custom knobs:
    asset_version_id , which refers to the asset id which this version belongs to
    component_name, the component which will contain the node result.
    '''
    ftrack.setup()

    # get the current node.
    node = nuke.thisNode()

    asset_id = node['asset_version_id'].value()
    version = ftrack.AssetVersion(id=asset_id)

    # create the component and copy data to the most likely store
    component = node['component_name'].value()
    out = node['file'].value()

    prefix = out.split('.')[0] + '.'
    ext = os.path.splitext(out)[-1]
    start_frame = int(node['first'].value())
    end_frame = int(node['last'].value())
    collection = Collection(
        head=prefix,
        tail=ext,
        padding=len(str(end_frame)),
        indexes=set(range(start_frame, end_frame+1))
    )
    version.createComponent(component, str(collection))


def createReview():
    ''' Create component callback for nuke write nodes.
    This callback relies on two custom knobs:
    asset_version_id , which refers to the asset id which this version belongs to
    component_name, the component which will contain the node result.
    This callback will also trigger the upload and encoding of the generated quicktime.
    '''
    ftrack.setup()
    node = nuke.thisNode()
    asset_id = node['asset_version_id'].value()
    version = ftrack.AssetVersion(id=asset_id)
    out = str(node['file'].value())
    component = node['component_name'].value()
    version.createComponent(component, out)

    # this seems to be failing when called from wihtin the callback
    # timeout doesn't seems to help
    # ftrack.Review.makeReviewable(version=version, filePath=out)


def createThumbnail():
    ''' Create component callback for nuke write nodes.
    This callback relies on two custom knobs:
    asset_version_id , which refers to the asset id which this version belongs to
    component_name, the component which will contain the node result.
    This callback will also trigger upload of the thumbnail on the server.
    '''
    ftrack.setup()
    node = nuke.thisNode()

    asset_id = node['asset_version_id'].value()
    version = ftrack.AssetVersion(id=asset_id)
    out = node['file'].value()
    version.createThumbnail(out)