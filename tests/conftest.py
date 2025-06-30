import sys
import types

if 'PySide6' not in sys.modules:
    pyside6 = types.ModuleType('PySide6')
    qtwidgets = types.ModuleType('PySide6.QtWidgets')
    qtcore = types.ModuleType('PySide6.QtCore')
    qtgui = types.ModuleType('PySide6.QtGui')

    qtwidgets.QApplication = object
    qtwidgets.QMainWindow = object
    qtwidgets.QWidget = object
    qtwidgets.QVBoxLayout = object
    qtwidgets.QHBoxLayout = object
    qtwidgets.QLabel = object
    qtwidgets.QPushButton = object
    qtwidgets.QFileDialog = object
    qtwidgets.QProgressBar = object
    qtwidgets.QTextEdit = object
    qtwidgets.QMessageBox = object
    qtwidgets.QGroupBox = object

    class DummyButton:
        def __init__(self):
            self.enabled = False

        def setEnabled(self, val):
            self.enabled = val

        def isEnabled(self):
            return self.enabled

    import builtins
    builtins.DummyButton = DummyButton

    class Signal:
        def __init__(self, *a, **k):
            pass
        def connect(self, *a, **k):
            pass
    qtcore.Signal = Signal
    qtcore.QThread = object
    qtcore.QTimer = object
    qtcore.Qt = types.SimpleNamespace(ArrowCursor=0)

    class QCursor:
        def __init__(self, *args, **kwargs):
            pass
    qtgui.QCursor = QCursor

    sys.modules['PySide6'] = pyside6
    sys.modules['PySide6.QtWidgets'] = qtwidgets
    sys.modules['PySide6.QtCore'] = qtcore
    sys.modules['PySide6.QtGui'] = qtgui

if 'fitz' not in sys.modules:
    sys.modules['fitz'] = types.ModuleType('fitz')

if 'pandas' not in sys.modules:
    sys.modules['pandas'] = types.ModuleType('pandas')

if 'dateutil' not in sys.modules:
    dateutil = types.ModuleType('dateutil')
    sys.modules['dateutil'] = dateutil
if 'dateutil.relativedelta' not in sys.modules:
    rd = types.ModuleType('dateutil.relativedelta')
    rd.relativedelta = lambda **kw: None
    sys.modules['dateutil.relativedelta'] = rd

if 'openpyxl' not in sys.modules:
    openpyxl = types.ModuleType('openpyxl')

    class _DummyWB:
        def __init__(self):
            self.active = types.SimpleNamespace()

        def save(self, *a, **k):
            pass

    def Workbook():
        return _DummyWB()

    def load_workbook(*a, **k):
        return _DummyWB()

    styles = types.ModuleType('styles')
    styles.PatternFill = lambda *a, **k: None
    styles.Alignment = lambda *a, **k: None
    styles.Font = lambda *a, **k: None
    formatting = types.ModuleType('formatting')
    rule = types.ModuleType('rule')
    rule.FormulaRule = lambda *a, **k: None
    formatting.rule = rule
    utils = types.ModuleType('utils')
    utils.get_column_letter = lambda i: 'A'

    openpyxl.Workbook = Workbook
    openpyxl.load_workbook = load_workbook
    openpyxl.styles = styles
    openpyxl.formatting = formatting
    openpyxl.utils = utils
    sys.modules['openpyxl'] = openpyxl
    sys.modules['openpyxl.styles'] = styles
    sys.modules['openpyxl.formatting'] = formatting
    sys.modules['openpyxl.formatting.rule'] = rule
    sys.modules['openpyxl.utils'] = utils