import os

def test_log_files_removed():
    root = os.path.dirname(os.path.dirname(__file__))
    assert not os.path.exists(os.path.join(root, 'New Text Document.txt'))
    assert not os.path.exists(os.path.join(root, 'error_log.txt'))
    assert not os.path.exists(os.path.join(root, 'startup_log.txt'))
