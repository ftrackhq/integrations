# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.
import tempfile
import os
from hiero.exporters.FnShotProcessor import ShotProcessorPreset

from .ftrack_base import FtrackBase
from .ftrack_shot_processor import FtrackShotProcessor 


class FtrackShotProcessorPreset(ShotProcessorPreset, FtrackBase):

    def __init__(self, name, properties):
        super(FtrackShotProcessorPreset, self).__init__(
            name, properties
        )
        FtrackBase.__init__(self)
        self._parentType = FtrackShotProcessor
        self.set_export_root()
        self.set_ftrack_properties(properties)

    def set_ftrack_properties(self, properties):
        self.properties()['ftrack'] = {}
        ftrack_properties = self.properties()['ftrack']

        # add placeholders for default ftrack defaults
        ftrack_properties['project_schema'] = 'Film Pipeline'
        ftrack_properties['task_type'] = 'Compositing'
        ftrack_properties['shot_status'] = 'In progress'
        ftrack_properties['asset_version_status'] = 'WIP'
        # override properties from processor setup
        self.properties().update(properties)

    def set_export_root(self):
        self.properties()["exportRoot"] = self.session.server_url

    def resolve_ftrack_project(self, task):
        return task.projectName()

    def resolve_ftrack_sequence(self, task):
        trackItem = task._item
        return trackItem.name().split('_')[0]

    def resolve_ftrack_shot(self, task):
        trackItem = task._item
        return trackItem.name().split('_')[1]        
    
    def resolve_ftrack_task(self, task):
        # TODO: here we should really parse the task tags and use the ftrack task tag to define ?
        # let's stick to something basic for now
        return self.properties()['ftrack']['task_type']

    def resolve_ftrack_asset(self, task):
        # for now simply return the component
        return self.resolve_ftrack_component(task)

    def resolve_ftrack_component(self, task):
        # TODO: Check whether there's a better way to get this out !
        preset_name =  task._preset.name()
        return preset_name

    def resolve_ftrack_version(self, task):
        return "0" # here we can check if there's any tag with an id to check against, if not we can return 0 as first version        

    def addUserResolveEntries(self, resolver):
        
        resolver.addResolver(
            "{ftrack_project}",
            "Ftrack project path.",
            lambda keyword, task: self.resolve_ftrack_project(task)
        )

        resolver.addResolver(
            "{ftrack_sequence}",
            "Ftrack sequence path.",
            lambda keyword, task: self.resolve_ftrack_sequence(task)
        )

        resolver.addResolver(
            "{ftrack_shot}",
            "Ftrack shot path.",
            lambda keyword, task: self.resolve_ftrack_shot(task)
        )

        resolver.addResolver(
            "{ftrack_task}",
            "Ftrack task path.",
            lambda keyword, task: self.resolve_ftrack_task(task)
        )

        resolver.addResolver(
            "{ftrack_asset}",
            "Ftrack asset path.",
            lambda keyword, task: self.resolve_ftrack_asset(task)
        )

        resolver.addResolver(
            "{ftrack_version}",
            "Ftrack version.",
            lambda keyword, task: self.resolve_ftrack_version(task)
        )

        resolver.addResolver(
            "{ftrack_component}",
            "Ftrack component path.",
            lambda keyword, task: self.resolve_ftrack_component(task)
        )
