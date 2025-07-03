import data_harvesters


def test_harvest_author_returns_string():
    text = "Author: John Doe"
    assert data_harvesters.harvest_author(text) == "John Doe"
