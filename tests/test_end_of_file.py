import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
import kyo_qa_tool_app

def test_end_of_file_contains_main():
    text = Path(kyo_qa_tool_app.__file__).read_text().strip().splitlines()
    assert text[-3:] == [
        'if __name__ == "__main__":',
        '    app = QAApp()',
        '    app.mainloop()'
    ]
