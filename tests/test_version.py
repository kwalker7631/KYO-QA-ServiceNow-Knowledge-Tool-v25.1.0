import version

def test_get_version():
    assert version.get_version() == version.VERSION
