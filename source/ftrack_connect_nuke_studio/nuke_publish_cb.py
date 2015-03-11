# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import threading

import nuke
import ftrack_legacy as ftrack
from clique import Collection


def createComponent():
    ''' Create component callback for nuke write nodes.

    This callback relies on two custom knobs:
        * asset_version_id , which refers to the parent Asset.
        * component_name, the component which will contain the node result.

    '''
    ftrack.setup()

    # Get the current node.
    node = nuke.thisNode()

    asset_id = node['asset_version_id'].value()
    version = ftrack.AssetVersion(id=asset_id)

    # Create the component and copy data to the most likely store
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
    component = version.createComponent(component, str(collection))
    component.setMeta('img_main', True)


def publishReviewableComponent(version_id, component, out):
    '''Publish a reviewable component to *version_id*'''
    version = ftrack.AssetVersion(id=version_id)
    version.createComponent(component, out)

    ftrack.Review.makeReviewable(version=version, filePath=out)


def createReview():
    ''' Create component callback for nuke write nodes.

    This callback relies on two custom knobs:
        * asset_version_id , which refers to the parent Asset.
        * component_name, the component which will contain the node result.

    This callback will also trigger the upload and encoding of the generated
    quicktime.

    '''
    ftrack.setup()
    node = nuke.thisNode()
    version_id = node['asset_version_id'].value()
    out = str(node['file'].value())
    component = node['component_name'].value()

    # Create component in a separate thread. If this is done in the main thread
    # the file is not properly written to disk.
    _thread = threading.Thread(
        target=publishReviewableComponent,
        kwargs={
        'version_id': version_id,
        'component': component,
        'out': out
        }
    )
    _thread.start()


def createThumbnail():
    ''' Create component callback for nuke write nodes.

    This callback relies on two custom knobs:
        * asset_version_id , which refers to the parent Asset.
        * component_name, the component which will contain the node result.

    This callback will also trigger upload of the thumbnail on the server.

    '''
    ftrack.setup()
    node = nuke.thisNode()

    asset_id = node['asset_version_id'].value()
    version = ftrack.AssetVersion(id=asset_id)
    out = node['file'].value()
    version.createThumbnail(out)
