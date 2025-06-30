import os
import sys

# Ensure the repository root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import data_harvesters


def test_harvest_models_standardization():
    text = "Model TASKalfa-2552ci found"
    filename = "doc.pdf"
    models = data_harvesters.harvest_models(text, filename)
    assert models == ["TASKalfa 2552ci"]
