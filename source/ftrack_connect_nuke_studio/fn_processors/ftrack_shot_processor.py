# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.
import tempfile
import types
import os
from .ftrack_base import FtrackBase
from hiero.exporters.FnShotProcessor import ShotProcessor
from hiero.exporters.FnShotProcessor import buildTagsData, findTrackItemExportTag, getShotNameIndex
from hiero.exporters.FnEffectHelpers import ensureEffectsNodesCreated

from hiero.core.FnProcessor import _expandTaskGroup

from hiero import core
import hiero
import time

class FtrackShotProcessor(ShotProcessor, FtrackBase):

    def __init__(self, preset, submission, synchronous=False):
        ShotProcessor.__init__(self, preset, submission, synchronous=synchronous)
        FtrackBase.__init__(self)
        self.ftrack_properties = self._preset.properties()['ftrack']

        # note we do resolve {ftrack_version} as part of the {ftrack_asset} function
        self.fn_mapping = {
            '{ftrack_project}': self._create_project_fragment,
            '{ftrack_sequence}': self._create_sequence_fragment,
            '{ftrack_shot}': self._create_shot_fragment,
            '{ftrack_task}': self._create_task_fragment,
            '{ftrack_asset}': self._create_asset_fragment,
            '{ftrack_component}': self._create_component_fragment
        }

    def timeStampString(self, localtime):
        """timeStampString(localtime)
        Convert a tuple or struct_time representing a time as returned by gmtime() or localtime() to a string formated YEAR/MONTH/DAY TIME."""
        return time.strftime("%Y/%m/%d %X", localtime)

    def updateItem(self, originalItem, localtime):
        self.logger.info('Updating Item {0}'.format(originalItem))
        super(FtrackShotProcessor, self).updateItem(originalItem, localtime)

    @property
    def schema(self):
        project_schema_name = self.ftrack_properties['project_schema']
        project_schema = self.session.query(
            'ProjectSchema where name is "{0}"'.format(project_schema_name)
        ).one()
        self.logger.info('project_schema: %s' % project_schema)
        return project_schema

    @property
    def task_type(self):
        task_type_name = self.ftrack_properties['task_type']
        task_types =  self.schema.get_types('Task')
        task_type = [t for t in task_types if t['name'] == task_type_name][0]
        self.logger.info('task_type: %s' % task_type)
        return task_type

    @property
    def task_status(self):
        task_status_name = self.ftrack_properties['task_status']
        task_statuses =  self.schema.get_statuses('Task', self.task_type['id'])
        task_status = [t for t in task_statuses if t['name'] == task_status_name][0]
        self.logger.info('task_status: %s' % task_status)
        return task_status

    @property
    def shot_status(self):
        shot_status_name = self.ftrack_properties['shot_status']
        shot_statuses =  self.schema.get_statuses('Shot')
        shot_status = [t for t in shot_statuses if t['name'] == shot_status_name][0]
        self.logger.info('shot_status: %s' % shot_status)
        return shot_status

    @property
    def asset_version_status(self):
        asset_status_name = self.ftrack_properties['asset_version_status']
        asset_statuses =  self.schema.get_statuses('AssetVersion')
        asset_status = [t for t in asset_statuses if t['name'] == asset_status_name][0]
        self.logger.info('asset_version_status: %s' % asset_status)
        return asset_status

    def asset_type_per_task(self, task):
        asset_type = task._preset.properties()['ftrack']['asset_type_code']
        result = self.session.query(
            'AssetType where short is "{}"'.format(asset_type)
        ).one()

        return result

    def _create_project_fragment(self, name, parent, task):
        project = self.session.query(
            'Project where name is "{}"'.format(name)
        ).first()
        if not project:
            project = self.session.create('Project', {
                'name': name,
                'full_name': name + '_full',
                'project_schema': self.schema
            })
        return project

    def _create_sequence_fragment(self, name, parent, task):
        sequence = self.session.query(
            'Sequence where name is "{}" and parent.id is "{}"'.format(name, parent['id'])
        ).first()
        if not sequence:
            sequence = self.session.create('Sequence', {
                'name': name,
                'parent': parent
            })          
        return sequence

    def _create_shot_fragment(self, name, parent, task):
        shot = self.session.query(
            'Shot where name is "{}" and parent.id is "{}"'.format(name, parent['id'])
        ).first()
        if not shot:
            shot = self.session.create('Shot', {
                'name': name,
                'parent': parent,
                'status': self.shot_status
            })
        return shot

    def _create_asset_fragment(self, name, parent, task):
        asset = self.session.query(
            'Asset where name is "{}" and parent.id is "{}"'.format(name, parent['parent']['id'])
        ).first()
        if not asset:
            asset = self.session.create('Asset', {
                'name': name,
                'parent': parent['parent'],
                'type': self.asset_type_per_task(task)
            })
        
        comment = 'Published from Nuke Studio : {}.{}.{}'.format(*self.hiero_version_touple)

        version = self.session.create('AssetVersion', {
            'asset': asset,
            'status': self.asset_version_status,
            'comment': comment,
            'task': parent
        })

        return version

    def _create_task_fragment(self, name, parent, task):
        task = self.session.query(
            'Task where name is "{}" and parent.id is "{}"'.format(name, parent['id'])
        ).first()
        if not task:
            task = self.session.create('Task', {
                'name': name,
                'parent': parent,
                'status': self.task_status,
                'type': self.task_type
            })                    
        return task

    def _create_component_fragment(self, name, parent, task):
        asset_type = task._preset.properties()['ftrack']['asset_type_code']
        component = parent.create_component('/', {
            'name': name
        }, location=None)

        return component

    def _skip_fragment(self, name, parent):
        self.logger.warning('Skpping : {}'.format(name))
        
    def create_project_structure(self, task, trackItem):
        file_name = task._preset.properties()['ftrack']['component_pattern']

        preset_name = task._preset.name()
        resolved_file_name = task.resolvePath(file_name)
        path = task.resolvePath(task._shotPath)
        export_path = task._shotPath
        parent = None # after the loop this will be containing the component object

        for template, token in zip(export_path.split(os.path.sep), path.split(os.path.sep)):
            fragment_fn = self.fn_mapping.get(template, self._skip_fragment)
            parent = fragment_fn(token, parent, task)

        self.session.commit()

        # extract ftrack path from structure and accessors
        ftrack_shot_path = self.ftrack_location.structure.get_resource_identifier(parent)
        ftrack_path = os.path.join(self.ftrack_location.accessor.prefix, ftrack_shot_path, resolved_file_name)

        # assign result path back to the tasks, so it knows where to render stuff out.

        task._exportPath = ftrack_path
        task._exportRoot = self.ftrack_location.accessor.prefix
        task._export_template = os.path.join(task._shotPath, file_name)

        return parent # return component

    def startProcessing(self, exportItems, preview=False):

        self.logger.debug( "ShotProcessor::startProcessing(" + str(exportItems) + ")" )

        sequences = []
        selectedTrackItems = set()
        selectedSubTrackItems = set()
        ignoredTrackItems = set()
        excludedTracks = []
        
        # Build Tags data from selection
        self._tags = buildTagsData(exportItems)
        
        # Filter the include/exclude tags incase the previous tag selection is not included in the current selection
        included_tag_names = [ tag.name() for tag, objectType in self._tags if tag.name() in self._preset.properties()["includeTags"] ]
        excluded_tag_names = [ tag.name() for tag, objectType in self._tags if tag.name() in self._preset.properties()["excludeTags"] ]

        # This flag controls whether items which havent been explicitly included in the export, 
        # should be removed from the copied sequence. This primarily affects the collate functionality in nuke script generation.
        exclusiveCopy = False


        if exportItems[0].trackItem():
            sequences.append( exportItems[0].trackItem().parent().parent() )
    
            for item in exportItems:
                trackItem = item.trackItem()
                if isinstance(trackItem, hiero.core.TrackItem):
                    selectedTrackItems.add( trackItem )
                if item.ignore():
                    ignoredTrackItems.add( trackItem )
                elif isinstance(trackItem, hiero.core.SubTrackItem):
                    selectedSubTrackItems.add( trackItem )
        else:
            sequences = [ item.sequence() for item in exportItems ]
        
        if ignoredTrackItems:
            # A set of track items have been explicitly marked as ignored. 
            # This track items are to be included in the copy, but not exported.
            # Thus any shot which isnt in the selected list, should be excluded from the copy.
            exclusiveCopy = True

        for sequence in sequences:
            excludedTracks.extend( [track for track in sequence if track.guid() in self._preset._excludedTrackIDs] )
        
        localtime = time.localtime(time.time())

        path = self._exportTemplate.exportRootPath()
        versionIndex = self._preset.properties()["versionIndex"]
        versionPadding = self._preset.properties()["versionPadding"]
        retime = self._preset.properties()["includeRetimes"]

        cutHandles = None
        startFrame = None

        if self._preset.properties()["startFrameSource"] == ShotProcessor.kStartFrameCustom:
            startFrame = self._preset.properties()["startFrameIndex"]

        # If we are exporting the shot using the cut length (rather than the (shared) clip length)
        if self._preset.properties()["cutLength"]:
            # Either use the specified number of handles or zero
            if self._preset.properties()["cutUseHandles"]:
                cutHandles = int(self._preset.properties()["cutHandles"])
            else:
                cutHandles = 0


        # Create a resolver from the preset (specific to this type of processor)
        resolver = self._preset.createResolver()

        self._submission.setFormatDescription( self._preset.name() )

        exportTrackItems = []

        copiedSequences = []

        project = None

        for sequence in sequences:
            sequenceCopy = sequence.copy()
            copiedSequences.append( sequenceCopy )
            self._tagCopiedSequence(sequence, sequenceCopy)

            # Copied effect items create their nodes lazily, but this has to happen on
            # the main thread, force it to be done here.
            ensureEffectsNodesCreated(sequenceCopy)

            # The export items should all come from the same project
            if not project:
                project = sequence.project()

            if not preview:
                presetId = hiero.core.taskRegistry.addPresetToProjectExportHistory(project, self._preset)
            else:
                presetId = None

            # For each video track
            for track, trackCopy in zip(sequence.videoTracks(), sequenceCopy.videoTracks()) + zip(sequence.audioTracks(), sequenceCopy.audioTracks()):

                # Unlock copied track so that items may be removed
                trackCopy.setLocked(False)

                if track in excludedTracks or not track.isEnabled():
                    # remove unselected track from copied sequence
                    sequenceCopy.removeTrack(trackCopy)
                    continue

                # Used to store the track items to be removed from trackCopy, this is to
                # avoid removing items whilst we are iterating over them.
                trackItemsToRemove = []

                # For each track item on track
                for trackitem, trackitemCopy in zip(track.items(), trackCopy.items()):

                    trackitemCopy.unlinkAll() # Unlink to prevent accidental removal of items we want to keep

                    # If we're processing the whole sequence, or this shot has been selected
                    if not selectedTrackItems or trackitem in selectedTrackItems:

                        if trackitem in ignoredTrackItems:
                            self.logger.debug( "%s marked as ignore, skipping. Selection : %s" % (str(trackitemCopy), str(exportTrackItems)) )
                            continue
                        
                        # Check tags for excluded tags
                        excludedTags = [tag for tag in trackitem.tags() if tag.name() in excluded_tag_names]
                        includedTags = [tag for tag in trackitem.tags() if tag.name() in included_tag_names]

                        if included_tag_names:
                            # If not included, or explictly excluded
                            if not includedTags or excludedTags:
                                self.logger.debug( "%s does not contain include tag %s, skipping." % (str(trackitemCopy), str(included_tag_names)) )
                                ignoredTrackItems.add(trackitem)
                                continue
                            else:
                                self.logger.debug( "%s has include tag %s." % (str(trackitemCopy), str(included_tag_names)) )
                            
                        elif excludedTags:
                            self.logger.debug( "%s contains excluded tag %s, skipping." % (str(trackitemCopy), str(excluded_tag_names)) )
                            ignoredTrackItems.add(trackitem)
                            continue

                        if trackitem.isMediaPresent() or not self.skipOffline():
                            exportTrackItems.append((trackitem, trackitemCopy))  

                        else:
                            self.logger.debug( "%s is offline. Removing." % str(trackitem) )
                            trackItemsToRemove.append(trackitemCopy)
                    else:
                        # Either remove the track item entirely, or mark it as ignored, so that no tasks are spawned to export it.
                        if exclusiveCopy:
                            self.logger.debug( "%s is not selected. Removing." % str(trackitem) )
                            trackItemsToRemove.append(trackitemCopy)
                        else:
                            self.logger.debug( "%s is not selected. Ignoring." % str(trackitem) )
                            ignoredTrackItems.add(trackitem)


                for item in trackItemsToRemove:
                    trackCopy.removeItem(item)


        allTasks = []

        for trackitem, trackitemCopy in exportTrackItems:
        
            if trackitem in ignoredTrackItems:
                continue

            # Check if a task is already exporting this item and if so, skip it.
            # This is primarily to handle the case of collating shots by name, where we only 
            # want one script containing all the items with that name.
            createTasks = True
            for existingTask in allTasks:

                if existingTask.isExportingItem(trackitemCopy):
                    createTasks = False
                    break

            if not createTasks:
                continue
        
            taskGroup = hiero.core.TaskGroup()
            taskGroup.setTaskDescription( trackitem.name() )

            # Track items may end up with different versions if they're being re-exported.  Determine
            # the version for each item.
            trackItemVersionIndex = self._getTrackItemExportVersionIndex(trackitem, versionIndex, findTrackItemExportTag(self._preset, trackitem))
            trackItemVersion = "v%s" % format(int(trackItemVersionIndex), "0%id" % int(versionPadding))

            # If processor is flagged as Synchronous, flag tasks too
            if self._synchronous:
                self._submission.setSynchronous()

            # For each entry in the shot template
            for (exportPath, preset) in self._exportTemplate.flatten():

                # Build TaskData seed
                taskData = hiero.core.TaskData( preset,
                                                trackitemCopy,
                                                path,
                                                exportPath,
                                                trackItemVersion,
                                                self._exportTemplate,
                                                project=project,
                                                cutHandles=cutHandles,
                                                retime=retime,
                                                startFrame=startFrame,
                                                startFrameSource = self._preset.properties()["startFrameSource"],
                                                resolver=resolver,
                                                submission=self._submission,
                                                skipOffline=self.skipOffline(),
                                                presetId=presetId,
                                                shotNameIndex = getShotNameIndex(trackitem) )

                # Spawn task
                task = hiero.core.taskRegistry.createTaskFromPreset(preset, taskData)

                # Add task to export queue
                if task and task.hasValidItem():

                    # Give the task an opportunity to modify the original (not the copy) track item
                    if not task.error() and not preview:
                        task.updateItem(trackitem, localtime)

                    taskGroup.addChild(task)
                    allTasks.append(task)
                    self.logger.debug( "Added to Queue " + trackitem.name() )
            
            if preview:
                # If previewing only generate tasks for the first item, otherwise it
                # can slow down the UI
                if allTasks:
                    break
            else:
                # Dont add empty groups
                if len(taskGroup.children()) > 0:
                    self._submission.addChild( taskGroup )

        if not preview:
            # If processor is flagged as Synchronous, flag tasks too
            if self._synchronous:
                self._submission.setSynchronous()

            if self._submission.children():

                # Detect any duplicates
                self.processTaskPreQueue()
                component = self.create_project_structure(task, trackItem)
                asset_version = component['version']

                localtime = time.localtime(time.time())
                timestamp = self.timeStampString(localtime)
                ftag = core.Tag('AssetVersion {0}'.format(timestamp))
                ftag.setIcon(':ftrack/image/integration/version')
    
                meta = ftag.metadata()
                meta.setValue('type', 'ftrack')
                meta.setValue('ftrack.type', 'version')
                meta.setValue('ftrack.id', str(component['version']['id']))
                meta.setValue('tag.value', str(component['version']['version']))

                self.logger.info('Adding Tag: {0} to {1}'.format(ftag, trackItem))
                trackItem.addTag(ftag)

                # Start the submission queue
                self._submission.addToQueue()

            ShotProcessor._versionUpPreviousExports = False # Reset this after export
        return allTasks