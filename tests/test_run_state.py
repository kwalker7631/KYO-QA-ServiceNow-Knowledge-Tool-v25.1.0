import run_state


def test_increment_run_count(tmp_path, monkeypatch):
    temp_file = tmp_path / 'state.json'
    monkeypatch.setattr(run_state, 'STATE_FILE', temp_file)
    assert run_state.get_run_count() == 0
    run_state.increment_run_count()
    assert temp_file.exists()
    assert run_state.get_run_count() == 1

