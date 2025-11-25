import unittest
from pathlib import Path
from typing import Union

import print_utils
import utils
from configuration import Configuration as Config
from models.FileData import FileDataManager, FileData
from search.fuzzy_license_header_search import search_assessment_files_for_fuzzy_license_header_match, MatchResult
from tools import fuzzy_matches_evaluator
from tools.assessment_reader import read_all_assessment_files
from tools.print_statements_to_file_output import tee_stdout

p = Path(__file__).resolve()

class TestKeywordCombinationMatches(unittest.TestCase):

    def test_fuzzy_license_header_matching(self):
        Config.file_data_manager = FileDataManager()
        read_all_assessment_files(Path("input/licenses").resolve())
        search_assessment_files_for_fuzzy_license_header_match()
        fuzzy_matches_evaluator.determine_best_fuzzy_match_from_file_data()
        for file_data in Config.file_data_manager.get_all_file_data():
            print(f"File path: {file_data.file_path}")
            if file_data.fuzzy_license_matches:
                for entry in file_data.fuzzy_license_matches:
                    fuzzy_match: MatchResult = entry["Fuzzy_result"]
                    print(f"Fuzzy license: {entry["License_name"]}")
                    print(f"Fuzzy match %: {fuzzy_match.match_percent}")
                    print(f"Fuzzy match text: {fuzzy_match.matched_substring}")


    def test_fuzzy_license_mismatches(self):
        # mismatch_assessment_files = [
        #     "C:/license_assessments/my-ubi8-java8/blobs/sha256/8f42ad26ccdae7ec04dac9501e3c011a88c8663559699974ecf1697999914f0d_extracted/usr/share/licenses/libcap-ng/COPYING.LIB",
        #     "C:/license_assessments/my-ubi8-java8/blobs/sha256/8f42ad26ccdae7ec04dac9501e3c011a88c8663559699974ecf1697999914f0d_extracted/usr/share/licenses/libsigsegv/COPYING",
        #     "C:/license_assessments/my-ubi8-java8/blobs/sha256/8f42ad26ccdae7ec04dac9501e3c011a88c8663559699974ecf1697999914f0d_extracted/usr/share/licenses/rpm/COPYING",
        #     "C:/license_assessments/my-ubi8-java8/blobs/sha256/ae25f9cb21ba728b911953a0e3b3e04889240cbe64143cce215621094e690eaa_extracted/usr/share/doc/diffutils/README",
        #     "C:/license_assessments/my-ubi8-java8/blobs/sha256/ae25f9cb21ba728b911953a0e3b3e04889240cbe64143cce215621094e690eaa_extracted/usr/share/doc/gzip/NEWS",
        #     "C:/license_assessments/my-ubi8-java8/blobs/sha256/ae25f9cb21ba728b911953a0e3b3e04889240cbe64143cce215621094e690eaa_extracted/usr/share/doc/gzip/README",
        #     "C:/license_assessments/my-ubi8-java8/blobs/sha256/ae25f9cb21ba728b911953a0e3b3e04889240cbe64143cce215621094e690eaa_extracted/usr/share/doc/gzip/TODO",
        #     "C:/license_assessments/my-ubi8-java8/blobs/sha256/ae25f9cb21ba728b911953a0e3b3e04889240cbe64143cce215621094e690eaa_extracted/usr/share/doc/java-1.8.0-openjdk-1.8.0.472.b08-1.el8/java-1.8.0-openjdk-portable.specfile",
        #     "C:/license_assessments/my-ubi8-java8/blobs/sha256/ae25f9cb21ba728b911953a0e3b3e04889240cbe64143cce215621094e690eaa_extracted/usr/share/doc/lksctp-tools/COPYING",
        #     "C:/license_assessments/my-ubi8-java8/blobs/sha256/ae25f9cb21ba728b911953a0e3b3e04889240cbe64143cce215621094e690eaa_extracted/usr/share/licenses/cracklib/COPYING.LIB",
        #     "C:/license_assessments/my-ubi8-java8/blobs/sha256/ae25f9cb21ba728b911953a0e3b3e04889240cbe64143cce215621094e690eaa_extracted/usr/share/licenses/cups-libs/LICENSE.txt",
        #     "C:/license_assessments/my-ubi8-java8/blobs/sha256/ae25f9cb21ba728b911953a0e3b3e04889240cbe64143cce215621094e690eaa_extracted/usr/share/licenses/glibc/LICENSES",
        #     "C:/license_assessments/my-ubi8-java8/blobs/sha256/ae25f9cb21ba728b911953a0e3b3e04889240cbe64143cce215621094e690eaa_extracted/usr/share/licenses/rpm/COPYING"
        # ]

        mismatch_assessment_files = [
            "C:/license_assessments/my-ubi8-java8/blobs/sha256/8f42ad26ccdae7ec04dac9501e3c011a88c8663559699974ecf1697999914f0d_extracted/usr/share/licenses/libsigsegv/COPYING"
        ]

        Config.file_data_manager = FileDataManager()

        for mismatch_assessment_file in mismatch_assessment_files:
            try:
                # Try reading as text
                with open(mismatch_assessment_file, "r", encoding="utf-8") as f:
                    content: Union[str, bytes] = f.read()
            except UnicodeDecodeError:
                # Fallback to binary
                with open(mismatch_assessment_file, "rb") as f:
                    content = f.read()
            except Exception as e:
                print(f"Could not read {mismatch_assessment_file}: {e}")
                continue

            file_data = FileData(mismatch_assessment_file, content)
            file_extension = utils.get_file_extension(mismatch_assessment_file)
            file_data.file_extension = file_extension
            Config.file_data_manager.add_file_data(file_data)

        search_assessment_files_for_fuzzy_license_header_match()
        for file_data in Config.file_data_manager.get_all_file_data():
            if file_data.fuzzy_license_matches:
                print(f"File path: {file_data.file_path}")
                for entry in file_data.fuzzy_license_matches:
                    fuzzy_match: MatchResult = entry["Fuzzy_result"]
                    print(f"Fuzzy license: {entry["License_name"]}")
                    print(f"Fuzzy match %: {fuzzy_match.match_percent}")
                    print(f"Fuzzy match text: {fuzzy_match.matched_substring}")
        fuzzy_matches_evaluator.determine_best_fuzzy_match_from_file_data()
        with tee_stdout(Path(Config.root_dir) / "output/test_fuzzy_license_matches.txt"):
            for file_data in Config.file_data_manager.get_all_file_data():
                if file_data.fuzzy_license_match:
                    print(f"File path: {file_data.file_path}")
                    best_match: MatchResult = file_data.fuzzy_license_match["Fuzzy_result"]
                    print(f"Fuzzy license: {file_data.fuzzy_license_match["License_name"]}")
                    print(f"Fuzzy match %: {best_match.match_percent}")
                    print(f"Fuzzy match text: {best_match.matched_substring}")



if __name__ == "__main__":
    unittest.main()