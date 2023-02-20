# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMayaRender as OpenMayaRender
from ftrack_connect_pipeline_maya.constants import asset as asset_const

version = asset_const.VERSION
kPluginNodeTypeName = asset_const.FTRACK_PLUGIN_TYPE
kPluginNodeId = OpenMaya.MTypeId(asset_const.FTRACK_PLUGIN_ID)

glRenderer = OpenMayaRender.MHardwareRenderer.theRenderer()
glFT = glRenderer.glFunctionTable()


# Node definition
class FtrackAssetNode(OpenMayaMPx.MPxNode):
    # class variables
    a_locked = OpenMaya.MObject()
    a_asset_link = OpenMaya.MObject()
    a_asset_id = OpenMaya.MObject()
    a_asset_name = OpenMaya.MObject()
    a_context_path = OpenMaya.MObject()
    a_asset_type = OpenMaya.MObject()
    a_version_id = OpenMaya.MObject()
    a_version_number = OpenMaya.MObject()
    a_component_path = OpenMaya.MObject()
    a_component_name = OpenMaya.MObject()
    a_component_id = OpenMaya.MObject()
    a_load_mode = OpenMaya.MObject()
    a_asset_info_options = OpenMaya.MObject()
    a_reference_node = OpenMaya.MObject()
    a_is_latest_version = OpenMaya.MObject()
    a_asset_info_id = OpenMaya.MObject()
    a_dependency_ids = OpenMaya.MObject()
    a_is_loaded = OpenMaya.MObject()

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
    booleanAttr = OpenMaya.MFnNumericAttribute()

    # boolean attr
    FtrackAssetNode.a_locked = n_attr.create(
        asset_const.LOCKED, 'lo', OpenMaya.MFnNumericData.kBoolean, False
    )
    n_attr.setHidden(True)
    n_attr.setStorable(True)

    FtrackAssetNode.a_asset_link = m_attr.create(asset_const.ASSET_LINK, 'al')
    m_attr.setHidden(False)
    m_attr.setStorable(True)

    FtrackAssetNode.a_dependency_ids = t_attr.create(
        asset_const.DEPENDENCY_IDS, 'depid', OpenMaya.MFnData.kStringArray
    )
    t_attr.setHidden(False)
    t_attr.setStorable(True)

    FtrackAssetNode.a_asset_id = t_attr.create(
        asset_const.ASSET_ID, 'aid', OpenMaya.MFnData.kString
    )
    t_attr.setStorable(True)
    t_attr.setHidden(False)

    FtrackAssetNode.a_context_path = t_attr.create(
        asset_const.CONTEXT_PATH, 'cop', OpenMaya.MFnData.kString
    )
    t_attr.setHidden(False)
    t_attr.setStorable(True)

    FtrackAssetNode.a_asset_name = t_attr.create(
        asset_const.ASSET_NAME, 'an', OpenMaya.MFnData.kString
    )
    t_attr.setHidden(False)
    t_attr.setStorable(True)

    FtrackAssetNode.a_asset_type = t_attr.create(
        asset_const.ASSET_TYPE_NAME, 'att', OpenMaya.MFnData.kString
    )
    t_attr.setHidden(False)
    t_attr.setStorable(True)

    FtrackAssetNode.a_version_id = t_attr.create(
        asset_const.VERSION_ID, 'vid', OpenMaya.MFnData.kString
    )
    t_attr.setStorable(True)
    t_attr.setHidden(False)

    FtrackAssetNode.a_version_number = n_attr.create(
        asset_const.VERSION_NUMBER, 'vn', OpenMaya.MFnNumericData.kInt, -1
    )
    n_attr.setHidden(False)
    n_attr.setStorable(True)

    FtrackAssetNode.a_component_path = t_attr.create(
        asset_const.COMPONENT_PATH, 'cp', OpenMaya.MFnData.kString
    )
    t_attr.setStorable(True)
    t_attr.setHidden(False)

    FtrackAssetNode.a_component_name = t_attr.create(
        asset_const.COMPONENT_NAME, 'cn', OpenMaya.MFnData.kString
    )
    t_attr.setHidden(False)
    t_attr.setStorable(True)

    FtrackAssetNode.a_component_id = t_attr.create(
        asset_const.COMPONENT_ID, 'cid', OpenMaya.MFnData.kString
    )
    t_attr.setStorable(True)
    t_attr.setHidden(False)

    FtrackAssetNode.a_load_mode = t_attr.create(
        asset_const.LOAD_MODE, 'alm', OpenMaya.MFnData.kString
    )
    t_attr.setHidden(False)
    t_attr.setStorable(True)

    FtrackAssetNode.a_asset_info_options = t_attr.create(
        asset_const.ASSET_INFO_OPTIONS, 'aio', OpenMaya.MFnData.kString
    )
    t_attr.setHidden(False)
    t_attr.setStorable(True)

    FtrackAssetNode.a_reference_node = t_attr.create(
        asset_const.REFERENCE_OBJECT, 'rfn', OpenMaya.MFnData.kString
    )
    t_attr.setHidden(False)
    t_attr.setStorable(True)

    FtrackAssetNode.a_is_latest_version = booleanAttr.create(
        asset_const.IS_LATEST_VERSION,
        'ilv',
        OpenMaya.MFnNumericData.kBoolean,
        False,
    )
    booleanAttr.setHidden(False)
    booleanAttr.setStorable(True)

    FtrackAssetNode.a_asset_info_id = t_attr.create(
        asset_const.ASSET_INFO_ID, 'aiid', OpenMaya.MFnData.kString
    )
    t_attr.setHidden(False)
    t_attr.setStorable(True)

    FtrackAssetNode.a_is_loaded = t_attr.create(
        asset_const.OBJECTS_LOADED, 'il', OpenMaya.MFnData.kString
    )
    t_attr.setHidden(False)
    t_attr.setStorable(True)

    # Add the attributes to the dcc_object
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_locked)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_asset_link)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_asset_id)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_asset_name)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_context_path)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_asset_type)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_version_id)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_version_number)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_component_path)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_component_name)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_component_id)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_load_mode)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_asset_info_options)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_reference_node)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_is_latest_version)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_asset_info_id)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_dependency_ids)
    FtrackAssetNode.addAttribute(FtrackAssetNode.a_is_loaded)


def initializePlugin(m_object):
    print('Loading ftrack plugin - version {0}'.format(version))
    m_plugin = OpenMayaMPx.MFnPlugin(m_object, 'ftrack', version, 'Any')
    try:
        m_plugin.registerNode(
            kPluginNodeTypeName, kPluginNodeId, nodeCreator, nodeInitializer
        )
    except:
        sys.stderr.write(
            'Failed to register dcc_object: {0}'.format(kPluginNodeTypeName)
        )
        raise


def uninitializePlugin(m_object):
    m_plugin = OpenMayaMPx.MFnPlugin(m_object)
    try:
        m_plugin.deregisterNode(kPluginNodeId)
    except:
        sys.stderr.write(
            'Failed to deregister dcc_object: {0}'.format(kPluginNodeTypeName)
        )
        raise
