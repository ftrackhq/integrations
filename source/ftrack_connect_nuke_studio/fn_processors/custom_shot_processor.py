# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.


from hiero.exporters import FnShotProcessor


class BaseFtrackProcessorPreset(object):
    def __init__(self, options):
        options['publishThumbnail'] = True
        options['publishPlate'] = True
        options['publishProxy'] = False
        options['publishReview'] = False


class FtrackShotProcessor(FnShotProcessor.ShotProcessor):
    pass


class FtrackProcessorPreset(FnShotProcessor.ShotProcessorPreset):
    pass

