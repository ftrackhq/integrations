# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.


from hiero.exporters import FnShotProcessor


class BaseFtrackProcessorPreset(object):
    def __init__(self, options):
        options['publishThumbnail'] = True
        options['publishPlate'] = True
        options['publishProxy'] = False
        options['publishReview'] = False


class BaseFtrackProcessor(object):

    def publish_thumbnail(self, thumbnail):
        pass

    def publish_plate(self, plate):
        pass

    def publish_proxy(self, proxy):
        pass

    def publish_review(self, review):
        pass


class FtrackShotProcessor(FnShotProcessor.ShotProcessor):
    pass



class FtrackProcessorPreset(FnShotProcessor.ShotProcessorPreset, BaseFtrackProcessorPreset):
    pass

