import logging
from qtpy import QtWidgets, QtCore


class AssetComboBox(QtWidgets.QComboBox):
    context_changed = QtCore.Signal(object)

    def __init__(self, session, asset_type, parent=None):
        super(AssetComboBox, self).__init__(parent=parent)
        self.session = session
        self.asset_type = asset_type
        self.context_changed.connect(self._on_context_changed)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def _on_context_changed(self, context):
        self.clear()
        assets = self.session.query(
            'select name from Asset where type.id is {} and parent.id is {}'.format(
                self.asset_type['id'], context['id'])
        ).all()

        self.addItems(assets)

class AssetSelector(QtWidgets.QWidget):

    def __init__(self, session, asset_type, parent=None):
        super(AssetSelector, self).__init__(parent=parent)
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        self.session = session
        self.asset_type = self.session.query(
            'AssetType where short is "{}"'.format(asset_type)
        ).one()

        self.radioButtonFrame = QtWidgets.QFrame()
        self.radioButtonFrame.setLayout(QtWidgets.QHBoxLayout())
        self.radioButtonFrame.layout().setContentsMargins(5, 5, 5, 5)

        self.asset_combobox = AssetComboBox(self.session, self.asset_type)

    def set_context(self, context):
        self.asset_combobox.context_changed.emit(context)
