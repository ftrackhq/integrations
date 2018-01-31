import hiero.core
import hiero.core.util
import hiero.core.nuke as nuke
import hiero.exporters
import _nuke # import _nuke so it does not conflict with hiero.core.nuke

from hiero.exporters.FnNukeShotExporter import NukeShotExporter
from hiero.exporters.FnNukeShotExporterUI import NukeShotExporterUI

from hiero.exporters import FnShotExporter
from hiero.exporters import FnExternalRender
from hiero.exporters import FnScriptLayout



from ftrack_base import FtrackBase

class FtrackNukeShotExporter(NukeShotExporter, FtrackBase):
  def __init__(self, initDict):
    super(FtrackNukeShotExporter, self).__init__(initDict)


class FtrackNukeShotExporterPreset(hiero.core.TaskPresetBase, FtrackBase):
    def __init__(self, name, properties, task=FtrackNukeShotExporter):
        super(FtrackNukeShotExporterPreset, self).__init__(task, name)


class FtrackNukeShotExporterUI(NukeShotExporterUI, FtrackBase):
    pass

hiero.core.taskRegistry.registerTask(FtrackNukeShotExporterPreset, FtrackNukeShotExporter)
hiero.ui.taskUIRegistry.registerProcessorUI(FtrackNukeShotExporterPreset, FtrackNukeShotExporterUI)
