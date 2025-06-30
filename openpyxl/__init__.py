import types

# Minimal stubs for tests when real openpyxl is unavailable
styles = types.ModuleType('styles')
PatternFill = type('PatternFill', (), {})
Alignment = type('Alignment', (), {})
Font = type('Font', (), {})
styles.PatternFill = PatternFill
styles.Alignment = Alignment
styles.Font = Font
formatting = types.ModuleType('formatting')
rule = types.ModuleType('rule')
rule.FormulaRule = type('FormulaRule', (), {})
formatting.rule = rule
utils = types.ModuleType('utils')
utils.get_column_letter = lambda x: str(x)
import builtins
builtins.rule_mod = rule

class Workbook:
    def __init__(self, *a, **k):
        self.active = types.SimpleNamespace()

def load_workbook(*a, **k):
    return Workbook()

__all__ = ['Workbook', 'load_workbook', 'styles', 'formatting', 'utils']
