import inspect
from pathlib import Path
import kyo_qa_tool_app


def test_single_QAApp_definition():
    classes = [obj for name, obj in inspect.getmembers(kyo_qa_tool_app, inspect.isclass) if name == "QAApp"]
    assert len(classes) == 1


def test_main_references_QAApp():
    source = Path(kyo_qa_tool_app.__file__).read_text()
    assert "if __name__ == \"__main__\"" in source
    assert "QAApp()" in source
