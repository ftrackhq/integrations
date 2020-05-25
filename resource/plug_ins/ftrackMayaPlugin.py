# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMayaRender as OpenMayaRender
from ftrack_connect_pipeline_maya.constants import asset as asset_const

version = asset_const.VERSION
kPluginNodeTypeName = asset_const.FTRACK_PLUGIN_TYPE
kPluginNodeId = OpenMaya.MTypeId(asset_const.FTRACK_ASSET_CLASS_ID)

glRenderer = OpenMayaRender.MHardwareRenderer.theRenderer()
glFT = glRenderer.glFunctionTable()


# Node definition
class FtrackAssetNode(OpenMayaMPx.MPxNode):
    # class variables
    a_locked = OpenMaya.MObject()
    a_asset_link = OpenMaya.MObject()
    a_asset_id = OpenMaya.MObject()
    a_asset_name = OpenMaya.MObject()
    a_asset_type = OpenMaya.MObject()
    a_version_id = OpenMaya.MObject()
    a_version_number = OpenMaya.MObject()
    a_component_path = OpenMaya.MObject()
    a_component_name = OpenMaya.MObject()
    a_component_id = OpenMaya.MObject()
    a_asset_info_options = OpenMaya.MObject()

    def __init__(self):
        OpenMayaMPx.MPxNode.__init__(self)

    def compute(self, plug, data):
        try:
            return OpenMaya.kUnknownParameter
        except:
            OpenMaya.MGlobal.displayError('Compute failed')


def nodeCreator():
    return OpenMayaMPx.asMPxPtr(FtrackAssetNode())


# initializer
def nodeInitializer():
    n_attr = OpenMaya.MFnNumericAttribute()
    t_attr = OpenMaya.MFnTypedAttribute()
    m_attr = OpenMaya.MFnMessageAttribute()

    # boolean attr
    FtrackAssetNode.a_locked = n_attr.create(
        asset_const.LOCKED, 'lo', OpenMaya.MFnNumericData.kBoolean, False
    )
    n_attr.setHidden(True)
    n_attr.setStorable(True)

    FtrackAssetNode.a_asset_link = m_attr.create(asset_const.ASSET_LINK, 'al')
    m_attr.setStorable(True)

    FtrackAssetNode.a_asset_id = t_attr.create(
        asset_const.ASSET_ID, 'aid', OpenMaya.MFnData.kString
    )
    t_attr.setStorable(True)
    t_attr.setHidden(True)
    FtrackAssetNode.a_asset_name = t_attr.create(
        asset_const.ASSET_NAME, 'an', OpenMaya.MFnData.kString
    )
    t_attr.setStorable(True)
    FtrackAssetNode.a_asset_type = t_attr.create(
        asset_const.ASSET_TYPE, 'att', OpenMaya.MFnData.kString
    )
    t_attr.setStorable(True)
    FtrackAssetNode.a_version_id = t_attr.create(
        asset_const.VERSION_ID, 'vid', OpenMaya.MFnData.kString
    )
    t_attr.setStorable(True)
    t_attr.setHidden(True)
    FtrackAssetNode.a_version_number = n_attr.create(
        asset_const.VERSION_NUMBER, 'vn', OpenMaya.MFnNumericData.kInt, -1
    )
    n_attr.setStorable(True)
    FtrackAssetNode.a_component_path = t_attr.create(
        asset_const.COMPONENT_PATH, 'cp', OpenMaya.MFnData.kString
    )
    t_attr.setStorable(True)
    t_attr.setHidden(True)
    FtrackAssetNode.a_component_name = t_attr.create(
        asset_const.COMPONENT_NAME, 'cn', OpenMaya.MFnData.kString
    )
    t_attr.setStorable(True)
    FtrackAssetNode.a_component_id = t_attr.create(
        asset_const.COMPONENT_ID, 'cid', OpenMaya.MFnData.kString
    )
    t_attr.setStorable(True)
    t_attr.setHidden(True)
    FtrackAssetNode.a_asset_info_options = t_attr.create(
        asset_const.ASSET_INFO_OPTIONS, 'aio', OpenMaya.MFnData.kString
    )
    t_attr.setStorable(True)

    # Add the attributes to the node
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_locked)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_asset_link)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_asset_id)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_asset_name)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_asset_type)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_version_id)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_version_number)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_component_path)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_component_name)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_component_id)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_asset_info_options)


def initializePlugin(m_object):
    print 'Loading ftrack plugin - version {0}'.format(version)
    m_plugin = OpenMayaMPx.MFnPlugin(m_object, 'ftrack', version, 'Any')
    try:
        m_plugin.registerNode(
            kPluginNodeTypeName, kPluginNodeId, nodeCreator, nodeInitializer
        )
    except:
        sys.stderr.write('Failed to register node: {0}'.format(
            kPluginNodeTypeName
        ))
        raise


def uninitializePlugin(m_object):
    m_plugin = OpenMayaMPx.MFnPlugin(m_object)
    try:
        m_plugin.deregisterNode(kPluginNodeId)
    except:
        sys.stderr.write('Failed to deregister node: {0}'.format(
            kPluginNodeTypeName
        ))
        raise