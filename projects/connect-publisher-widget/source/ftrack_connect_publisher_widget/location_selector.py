# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect.ui.widget import item_selector as _item_selector

import ftrack_connect.asynchronous

from ftrack_connect.qt import QtWidgets
from ftrack_connect.qt import QtCore
from ftrack_connect.qt import QtGui


class LocationSelector(_item_selector.ItemSelector):
    excluded_locations = ['ftrack.origin', 'ftrack.review']

    def _update_description(self, index):
        location = self.itemData(index)
        self.setItemData(
            index, location.get('description', 'No Description Provided'),
            QtCore.Qt.ToolTipRole
        )
    
    def reset(self):
        current_location = self.session.pick_location()
        current_location_index = self.findText(
            current_location.get('label', current_location['name'])
        )
        self.setCurrentIndex(current_location_index)
    
    @property
    def selected_location(self):
        return self.currentItem()
    
    def __init__(self, *args, **kwargs):
        '''Instantiate the asset type selector.'''
        self.default_icon = QtGui.QIcon(
            QtGui.QPixmap(':ftrack/image/light/object_type/info-outline')
        )
        super(LocationSelector, self).__init__(
            labelField='label',
            defaultLabel=None,
            emptyLabel=None,
            **kwargs
        )
        self.loadLocations()
        self.reset()

    @ftrack_connect.asynchronous.asynchronous
    def loadLocations(self):
        '''Load asset types and add to selector.'''
        locations = self.session.query('Location').all()
        sorted_locations = sorted(
            locations,
            key=lambda location: location.priority
        )
        filtered_locations = [
            location for location in sorted_locations if (
                (location.accessor and location.structure) and
                location['name'] not in self.excluded_locations)
        ]
        for index, location in enumerate(filtered_locations):
                self.insertItem(index, location.get('label', location['name']), location)
                self.setItemData(index, location.get('description', 'No Description Provided'),  QtCore.Qt.ToolTipRole)
                self.setItemIcon(index, self.default_icon)
                
        self.currentIndexChanged.connect(self._update_description)