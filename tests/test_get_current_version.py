import update_version
import version


def test_get_current_version_matches_version_py():
    assert update_version.get_current_version() == version.VERSION
