# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMayaRender as OpenMayaRender

version = "1.0"
kPluginNodeTypeName = "ftrackAssetNode"
kPluginNodeId = OpenMaya.MTypeId(0x190319)

glRenderer = OpenMayaRender.MHardwareRenderer.theRenderer()
glFT = glRenderer.glFunctionTable()


# Node definition
class ftrackAssetNode(OpenMayaMPx.MPxNode):
    # class variables
    aLocked = OpenMaya.MObject()
    aAssetLink = OpenMaya.MObject()
    aAssetVersion = OpenMaya.MObject()
    aAssetId = OpenMaya.MObject()
    aAssetPath = OpenMaya.MObject()
    aAssetTake = OpenMaya.MObject()
    aAssetType = OpenMaya.MObject()
    aAssetComponentId = OpenMaya.MObject()

    def __init__(self):
        OpenMayaMPx.MPxNode.__init__(self)

    def compute(self, plug, data):
        try:
            return OpenMaya.kUnknownParameter
        except:
            OpenMaya.MGlobal.displayError("Compute failed")


def nodeCreator():
    return OpenMayaMPx.asMPxPtr(ftrackAssetNode())


# initializer
def nodeInitializer():
    nAttr = OpenMaya.MFnNumericAttribute()
    tAttr = OpenMaya.MFnTypedAttribute()
    mAttr = OpenMaya.MFnMessageAttribute()

    # boolean attr
    ftrackAssetNode.aLocked = nAttr.create(
        "locked", "lo", OpenMaya.MFnNumericData.kBoolean, False
    )
    nAttr.setHidden(True)
    nAttr.setStorable(True)

    ftrackAssetNode.aAssetLink = mAttr.create("assetLink", "al")
    mAttr.setStorable(True)

    ftrackAssetNode.aAssetTake = tAttr.create(
        "assetTake", "at", OpenMaya.MFnData.kString
    )
    tAttr.setStorable(True)

    ftrackAssetNode.aAssetType = tAttr.create(
        "assetType", "att", OpenMaya.MFnData.kString
    )
    tAttr.setStorable(True)

    ftrackAssetNode.aAssetComponentId = tAttr.create(
        "assetComponentId", "acit", OpenMaya.MFnData.kString
    )
    tAttr.setStorable(True)
    tAttr.setHidden(True)

    ftrackAssetNode.aAssetVersion = nAttr.create(
        "assetVersion", "av", OpenMaya.MFnNumericData.kInt, -1
    )
    nAttr.setStorable(True)

    ftrackAssetNode.aAssetId = tAttr.create(
        "assetId", "aid", OpenMaya.MFnData.kString
    )
    tAttr.setStorable(True)
    tAttr.setHidden(True)

    ftrackAssetNode.aAssetPath = tAttr.create(
        "assetPath", "ap", OpenMaya.MFnData.kString
    )
    tAttr.setStorable(True)

    # Add the attributes to the node
    ftrackAssetNode.addAttribute(ftrackAssetNode.aLocked)
    ftrackAssetNode.addAttribute(ftrackAssetNode.aAssetLink)
    ftrackAssetNode.addAttribute(ftrackAssetNode.aAssetTake)
    ftrackAssetNode.addAttribute(ftrackAssetNode.aAssetType)
    ftrackAssetNode.addAttribute(ftrackAssetNode.aAssetComponentId)
    ftrackAssetNode.addAttribute(ftrackAssetNode.aAssetVersion)
    ftrackAssetNode.addAttribute(ftrackAssetNode.aAssetId)
    ftrackAssetNode.addAttribute(ftrackAssetNode.aAssetPath)


def initializePlugin(mobject):
    print "Loading ftrack plugin - version {0}".format(version)
    mplugin = OpenMayaMPx.MFnPlugin(mobject, "ftrack", version, "Any")
    try:
        mplugin.registerNode(
            kPluginNodeTypeName, kPluginNodeId, nodeCreator, nodeInitializer
        )
    except:
        sys.stderr.write("Failed to register node: {0}".format(
            kPluginNodeTypeName
        ))
        raise


def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode(kPluginNodeId)
    except:
        sys.stderr.write("Failed to deregister node: {0}".format(
            kPluginNodeTypeName
        ))
        raise
