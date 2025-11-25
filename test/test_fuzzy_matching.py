import unittest
from typing import Union

import print_utils
import utils
from configuration import Configuration as Config
from models.FileData import FileDataManager
from pathlib import Path

from prototypes import fuzzy_match_prototype_optimized
from prototypes.fuzzy_match_prototype_with_versioning import fuzzy_match_in_file
from search import fuzzy_license_header_search
from tools import assessment_reader, fuzzy_matches_evaluator

p = Path(__file__).resolve()


class TestTemplate(unittest.TestCase):

    def test_fuzzy_matching_license_headers_to_file_text2(self):
        Config.file_data_manager = FileDataManager()
        assessment_reader.read_all_assessment_files(Path("input/fuzzy_matching").resolve())
        licenses_dir = Path("input/fuzzy_matching_licenses").resolve()
        fuzzy_license_header_search.search_assessment_files_for_fuzzy_license_header_match([licenses_dir])
        fuzzy_matches_evaluator.determine_best_fuzzy_match_from_file_data()
        print_utils.print_files_with_fuzzy_license_matches()


    def test_fuzzy_matching_license_headers_to_file_text_optimized(self):
        Config.file_data_manager = FileDataManager()
        assessment_reader.read_all_assessment_files(Path("input/fuzzy_matching").resolve())
        licenses_dir = Path("input/fuzzy_matching_licenses").resolve()
        fuzzy_match_prototype_optimized.search_all_assessment_files_for_fuzzy_license_matches([licenses_dir])


    def test_fuzzy_matching_license_headers_to_file_text(self):
        Config.file_data_manager = FileDataManager()
        license_paths = [
            Path(Config.root_dir, "input/license_headers/GPL-3.0-or-later.txt"),
            Path(Config.root_dir, "input/license_headers/GPL-2.0-or-later.txt"),
            Path(Config.root_dir, "input/license_headers/MulanPSL-2.0.txt"),
            Path(Config.root_dir, "input/license_headers/OSL-1.0.txt")
        ]
        # license_path=Path(Config.root_dir, "input/license_headers/GPL-3.0-or-later.txt")
        #license_path = Path(Config.root_dir, "input/license_headers/GPL-2.0-or-later.txt")
        # license_path = Path(Config.root_dir, "input/license_headers/GPL-1.0-or-later.txt")
        # license_path = Path(Config.root_dir, "input/license_headers/MulanPSL-2.0.txt")
        file_path = "C:/license_assessments/my-ubi8-java8/blobs/sha256/8f42ad26ccdae7ec04dac9501e3c011a88c8663559699974ecf1697999914f0d_extracted/usr/share/licenses/libsigsegv/COPYING"

        try:
            # Try reading as text
            with open(file_path, "r", encoding="utf-8") as f:
                file_content: Union[str, bytes] = f.read()
        except UnicodeDecodeError:
            # Fallback to binary
            with open(file_path, "rb") as f:
                file_content = f.read()
        except Exception as e:
            print(f"Could not read {file_path}: {e}")

        file_content = utils.remove_punctuation_and_normalize_text(file_content)
        print("File text: ")
        print(file_content)

        for license_path in license_paths:
            try:
                # Try reading as text
                with open(license_path, "r", encoding="utf-8") as f:
                    license_content: Union[str, bytes] = f.read()
            except UnicodeDecodeError:
                # Fallback to binary
                with open(license_path, "rb") as f:
                    license_content = f.read()
            except Exception as e:
                print(f"Could not read {license_path}: {e}")

            print(f"License name: {utils.get_file_name_from_path_without_extension(license_path)}")
            license_content = utils.remove_punctuation_and_normalize_text(license_content)
            print("License text: ")
            print(license_content)

            result = fuzzy_match_in_file(license_content, file_content)

            if result:
                print(f"Match percent: {result.match_percent:.2f}%")
                print(f"Match starts at index: {result.start_index}")
                print(f"Expected match version: {result.expected_version}")
                print(f"Found match version: {result.found_version}")
                print("Matched substring:")
                print(result.matched_substring)
            else:
                print("No good match found.")



if __name__ == "__main__":
    unittest.main()