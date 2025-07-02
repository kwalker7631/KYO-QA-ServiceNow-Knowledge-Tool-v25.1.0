import update_version

def test_files_to_update_contains_run():
    assert 'run.py' in update_version.FILES_TO_UPDATE
