from pathlib import Path

import print_utils
from models.FileData import FileDataManager
from prototypes import fuzzy_match_prototype_with_versioning, fuzzy_match_prototype_optimized
from timer import Timer
from search import full_license_search, full_license_header_search, fuzzy_license_search2, fuzzy_license_header_search
from tools import assessment_reader, file_release_assessor, file_hash_assessor, file_header_finder, \
    fuzzy_matches_evaluator
from configuration import Configuration as Config

p = Path(__file__).resolve()

timer = Timer()
timer.start()

# Global instance of file data manager
Config.file_data_manager = FileDataManager()

def main() -> None:
    # LOAD PRE-EXISTING FILE DATA FROM JSON
    #Config.file_data_manager = FileDataManager.load_from_json()

    # CREATES A FILE DATA OBJECT FOR EACH FILE IN THE ASSESSMENT
    assessment_reader.read_all_assessment_files(Path(Config.assessments_dir, Config.assessment_name))
    # DETERMINE IF A FILE IS PART OF THE RELEASE
    file_release_assessor.set_file_release_status()
    # GET/SET SHA256 HASH VALUE FOR EACH FILE
    file_hash_assessor.compute_file_hashes_for_assessment()
    # FIND HEADERS IN ASSESSMENT FILES
    file_header_finder.search_all_assessment_files_for_headers()
    # SCAN ALL ASSESSMENT FILES FOR FULL LICENSE TEXT
    #full_license_search.search_assessment_files_for_full_license()
    # SCAN ALL ASSESSMENT FILES FOR FULL LICENSE HEADER TEXT
    #full_license_header_search.search_assessment_files_for_full_license_header()
    #full_license_header_search.search_assessment_file_headers_for_full_license_header()
    # SCAN ALL ASSESSMENT FILES FOR PARTIAL MATCHING HEADERS
    # SCAN ALL ASSESSMENT FILES FOR FUZZY MATCHES OF LICENSE HEADERS
    #fuzzy_match_prototype_with_versioning.search_all_assessment_files_for_fuzzy_license_matches([Config.license_headers_dir])
    fuzzy_license_header_search.search_assessment_files_for_fuzzy_license_header_match([Config.license_headers_dir, Config.manual_license_headers_dir])
    #fuzzy_match_prototype_optimized.search_all_assessment_files_for_fuzzy_license_matches([Config.license_headers_dir])
    # SCAN ALL ASSESSMENT FILES TO DETERMINE THE BEST FUZZY MATCH FOUND
    fuzzy_matches_evaluator.determine_best_fuzzy_match_from_file_data()


    # SAVE FILE DATA TO JSON
    #Config.file_data_manager.save_to_json()


if __name__ == "__main__":
    main()

    print_utils.print_files_with_full_license_match()
    print_utils.print_files_with_fuzzy_license_matches()

    timer.stop()
    print(timer.elapsed())
