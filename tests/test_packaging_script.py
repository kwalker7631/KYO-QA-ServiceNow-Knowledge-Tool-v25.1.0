import zipfile

import packaging_script


def test_zip_project_creates_archive(tmp_path, monkeypatch):
    tmp_zip = tmp_path / 'test.zip'
    monkeypatch.setattr(packaging_script, 'out_zip', tmp_zip)
    monkeypatch.setattr(packaging_script, 'include', ['version.py'])
    packaging_script.zip_project()
    assert tmp_zip.exists()
    with zipfile.ZipFile(tmp_zip) as z:
        assert 'version.py' in z.namelist()
