import unittest
from typing import Union

import utils
from configuration import Configuration as Config
from models.FileData import FileDataManager
from pathlib import Path

from tools.assessment_reader import read_all_assessment_files

p = Path(__file__).resolve()

class TestTextNormalization(unittest.TestCase):

    def test_file_text_normalization(self):
        Config.file_data_manager = FileDataManager()
        dir_path = Path("input/normalization").resolve()
        for path in dir_path.rglob("*"):
            if path.is_file():
                try:
                    # Try reading as text
                    with open(path, "r", encoding="utf-8") as f:
                        content: Union[str, bytes] = f.read()
                except UnicodeDecodeError:
                    # Fallback to binary
                    with open(path, "rb") as f:
                        content = f.read()
                except Exception as e:
                    print(f"Could not read {path}: {e}")
                    continue

                if content:
                    print(f"File: {path}")
                    content = utils.remove_punctuation_and_normalize_text(content)
                    print(content)




if __name__ == "__main__":
    unittest.main()