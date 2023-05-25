# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import logging

from ftrack_connect.qt import QtWidgets
from ftrack_connect.qt import QtCore
from ftrack_connect.qt import QtGui

from ftrack_api import exception
from ftrack_api import event


from ftrack_connect.ui.widget import data_drop_zone as _data_drop_zone
from ftrack_connect.ui.widget import components_list as _components_list
from ftrack_connect.ui.widget import item_selector as _item_selector
from ftrack_connect.ui.widget import (
    thumbnail_drop_zone as _thumbnail_drop_zone,
)
from ftrack_connect.ui.widget import asset_options as _asset_options
from ftrack_connect.ui.widget import entity_selector

import ftrack_connect.asynchronous
import ftrack_connect.error


class EntitySelector(entity_selector.EntitySelector):
    '''Local representation of EntitySelector to support custom behaviour.'''

    def isValidBrowseSelection(self, entity):
        '''Overriden method to validate the selected *entity*.'''
        # Prevent selecting projects.
        return entity.entity_type != 'Project'


class Publisher(QtWidgets.QWidget):
    '''Publish widget for ftrack connect Publisher.'''

    publishStarted = QtCore.Signal()
    publishFinished = QtCore.Signal(bool)

    #: Signal to emit when an asset is created.
    assetCreated = QtCore.Signal(object)

    @property
    def session(self):
        '''Return current session.'''
        return self._session

    def __init__(self, session, parent=None):
        '''Initiate a publish view.'''
        super(Publisher, self).__init__(parent)

        self._session = session
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._entity = None

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.browser = _data_drop_zone.DataDropZone()
        layout.addWidget(self.browser)
        self.browser.dataSelected.connect(self._onDataSelected)

        # Create a components list widget.
        self.componentsList = _components_list.ComponentsList()
        self.componentsList.setObjectName('publisher-componentlist')
        self.componentsList.itemsChanged.connect(
            self._onComponentListItemsChanged
        )
        verticalSpacer = QtWidgets.QSpacerItem(
            0,
            0,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        layout.addItem(verticalSpacer)

        layout.addWidget(self.componentsList, stretch=1)
        self.componentsList.hide()

        # Create form layout to keep track of publish form items.
        formLayout = QtWidgets.QFormLayout()
        layout.addLayout(formLayout, stretch=0)

        # Add entity selector.
        self.entitySelector = EntitySelector(self.session)
        formLayout.addRow('Linked to', self.entitySelector)

        # Add asset options.
        self.assetOptions = _asset_options.AssetOptions(session=self.session)
        self.entitySelector.entityChanged.connect(self.assetOptions.setEntity)
        self.assetCreated.connect(self.assetOptions.setAsset)
        formLayout.addRow('Asset', self.assetOptions.radioButtonFrame)
        formLayout.addRow(
            'Existing asset', self.assetOptions.existingAssetSelector
        )
        formLayout.addRow('Type', self.assetOptions.assetTypeSelector)
        formLayout.addRow('Name', self.assetOptions.assetNameLineEdit)
        self.assetOptions.initializeFieldLabels(formLayout)

        # Add preview selector.
        self.previewSelector = _item_selector.ItemSelector(
            session=self.session,
            idField='resourceIdentifier',
            labelField='componentName',
            defaultLabel='Unnamed component',
            emptyLabel='Select component to use',
        )
        formLayout.addRow('Web playable', self.previewSelector)

        self.thumbnailDropZone = _thumbnail_drop_zone.ThumbnailDropZone()
        formLayout.addRow('Thumbnail', self.thumbnailDropZone)

        # Add version description component.
        self.versionDescription = QtWidgets.QTextEdit()
        formLayout.addRow('Description', self.versionDescription)

        publishButton = QtWidgets.QPushButton(text='Publish')
        publishButton.setObjectName('primary')
        publishButton.clicked.connect(self.publish)

        layout.addWidget(
            publishButton, alignment=QtCore.Qt.AlignCenter, stretch=0
        )

    def setEntity(self, entity):
        '''Set current entity.'''
        self.entitySelector.setEntity(entity)

    def _onComponentListItemsChanged(self):
        '''Callback for component changed signal.'''
        self.previewSelector.setItems(self.componentsList.items())
        if self.componentsList.count():
            self.componentsList.show()
        else:
            self.componentsList.hide()

    def _onDataSelected(self, filePath):
        '''Callback for Browser file selected signal.'''
        self.componentsList.addItem({'resourceIdentifier': filePath})

    def clear(self):
        '''Clear the publish view to it's initial state.'''
        self.assetOptions.clear()
        self.versionDescription.clear()
        self.componentsList.clearItems()
        self.thumbnailDropZone.clear()
        self.entitySelector.setEntity(None)

    def publish(self):
        '''Gather all data in publisher and publish version with components.'''
        # TODO: Proper validation.
        entity = self.entitySelector.getEntity()
        if entity is None:
            raise ftrack_connect.error.ConnectError(
                'No linked entity selected to publish against!'
            )

        taskId = None

        asset = self.assetOptions.getAsset()
        assetType = self.assetOptions.getAssetType()
        assetName = self.assetOptions.getAssetName()

        versionDescription = self.versionDescription.toPlainText()

        previewPath = self.previewSelector.currentItem()

        # ftrack does not support having Tasks as parent for Assets.
        # Therefore get parent shot/sequence etc.
        if entity.entity_type == 'Task':
            taskId = entity['id']
            entity = entity['parent']

        componentLocation = self.session.pick_location()

        components = []
        for component in self.componentsList.items():
            components.append(
                {
                    'locations': [componentLocation],
                    'name': component['componentName'],
                    'filePath': component['resourceIdentifier'],
                }
            )

        thumbnailFilePath = self.thumbnailDropZone.getFilePath()

        self._publish(
            entity=entity,
            asset=asset,
            assetName=assetName,
            assetType=assetType,
            versionDescription=versionDescription,
            taskId=taskId,
            components=components,
            previewPath=previewPath,
            thumbnailFilePath=thumbnailFilePath,
        )

    def _cleanupFailedPublish(self, version=None):
        '''Clean up after a failed publish.'''
        try:
            if version:
                self.session.delete(version)
                self.session.commit()

        except exception.OperationError:
            self.logger.exception(
                'Failed to delete version, probably due to a permission error.'
            )
        except Exception:
            self.logger.exception(
                'Failed to clean up version after failed publish'
            )

    @ftrack_connect.asynchronous.asynchronous
    def _publish(
        self,
        entity=None,
        assetName=None,
        assetType=None,
        versionDescription='',
        taskId=None,
        components=None,
        previewPath=None,
        thumbnailFilePath=None,
        asset=None,
    ):
        '''If *asset* is specified, publish a new version of it. Otherwise, get
        or create an asset of *assetType* on *entity*.

        *taskId*, *versionDescription*, *components*, *previewPath* and
        *thumbnailFilePath* are optional.

        Each component in *components* should be represented by a dictionary
        containing name, filepath and a list of locations.

        '''
        version = None

        self.publishStarted.emit()

        try:
            if not (asset or assetType):
                self.publishFinished.emit(False)
                raise ftrack_connect.error.ConnectError(
                    'No asset type selected.'
                )

            if not entity:
                self.publishFinished.emit(False)
                raise ftrack_connect.error.ConnectError('No entity found')

            if components is None:
                components = []

            task = None
            if taskId:
                task = self.session.get('Context', taskId)

            new_entity = self.session.get('Context', entity['id'])

            if not asset:
                asset_type = self.session.get('AssetType', assetType)
                if assetName is None:
                    assetName = asset_type['name']

                asset = self.session.create(
                    'Asset',
                    {
                        'name': assetName,
                        'type': asset_type,
                        'parent': new_entity,
                    },
                )

                self.session.commit()
                self.assetCreated.emit(asset)

            else:
                asset = self.session.get('Asset', asset)

            version = self.session.create(
                'AssetVersion',
                {
                    'asset': asset,
                    'comment': versionDescription,
                    'task': task,
                },
            )
            self.session.commit()

            origin_location = self.session.query(
                'Location where name is "ftrack.origin"'
            )

            for componentData in components:
                component = version.create_component(
                    componentData.get('filePath'),
                    {'name': componentData.get('name', None)},
                    location=None,
                )

                for location in componentData.get('locations', []):
                    new_location = self.session.get('Location', location['id'])
                    new_location.add_component(
                        component, source=origin_location
                    )
                    self.logger.info(
                        u'Publish {0!r} to location: {1!r}.'.format(
                            component, new_location['name']
                        )
                    )

            if previewPath:
                self.session.event_hub.publish(
                    event.base.Event(
                        'ftrack.connect.publish.make-web-playable',
                        data=dict(versionId=version['id'], path=previewPath),
                    ),
                    synchronous=True,
                )

            if thumbnailFilePath:
                version.create_thumbnail(thumbnailFilePath)

            self.session.commit()

            self.publishFinished.emit(True)

        # Catch any errors, emit *publishFinished*, clean up and re-raise.
        except Exception as error:
            self.logger.exception(u'Failed to publish: {0}'.format(error))
            self.publishFinished.emit(False)
            self._cleanupFailedPublish(version=version)
            self.session.rollback()
            raise
