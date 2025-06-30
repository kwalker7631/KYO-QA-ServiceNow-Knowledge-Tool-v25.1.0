import importlib
import unittest

import custom_patterns
from data_harvesters import get_combined_patterns
from config import MODEL_PATTERNS as DEFAULT_MODEL_PATTERNS

class PatternLoadingTests(unittest.TestCase):
    def test_loader_returns_unique_patterns(self):
        # Reload to ensure latest version is used
        importlib.reload(custom_patterns)
        patterns = get_combined_patterns("MODEL_PATTERNS", DEFAULT_MODEL_PATTERNS)
        self.assertEqual(
            patterns[:len(custom_patterns.MODEL_PATTERNS)],
            custom_patterns.MODEL_PATTERNS,
        )
        self.assertEqual(len(patterns), len(set(patterns)))

if __name__ == "__main__":
    unittest.main()
