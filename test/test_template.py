import unittest
from configuration import Configuration as Config
from models.FileData import FileDataManager
from pathlib import Path

p = Path(__file__).resolve()

class TestTemplate(unittest.TestCase):


    def test_test(self):
        Config.file_data_manager = FileDataManager()



if __name__ == "__main__":
    unittest.main()