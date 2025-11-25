from pathlib import Path
from loggers.print_utils_logger import print_utils_logger as logger
from configuration import Configuration as Config
from search.fuzzy_license_header_search import MatchResult
from tools.print_statements_to_file_output import tee_stdout


def print_files_with_full_license_match():
    full_license_match_count = 0
    for file_data in Config.file_data_manager.get_all_file_data():
        if file_data.license_matches:
            full_license_match_count += 1
            print(f"{"File: "}{Path(file_data.file_path).relative_to(Config.assessments_dir)}")
            print(f"{"License name: "}{file_data.license_name}")
    print(f"{"Total files with full license match: "}{full_license_match_count}")


def get_best_match_percent(file_data) -> float:
    """
    Returns the highest match_percent in file_data.fuzzy_license_match.
    If there are no matches, returns 0.0.
    """
    if not getattr(file_data, "fuzzy_license_match", None):
        return 0.0

    # file_data.fuzzy_license_match is assumed to be a list of dicts:
    # {"License_name": ..., "Fuzzy_license_match": MatchResult}
    best = 0.0
    fuzzy: MatchResult = file_data.fuzzy_license_match["Fuzzy_license_match"]
    if fuzzy is not None and fuzzy.match_percent is not None:
        if fuzzy.match_percent > best:
            best = fuzzy.match_percent
    return best


def print_files_with_fuzzy_license_matches(file_path="output/fuzzy_license_matches.txt"):
    fuzzy_license_match_count = 0
    with tee_stdout(Path(Config.root_dir) / file_path):
        sorted_list = sorted(
            Config.file_data_manager.get_all_file_data(),
            key=lambda f: (
                f.fuzzy_license_match.match_percent
                if f.fuzzy_license_match is not None
                else 0.0
            ),
            reverse=True,
        )
        for file_data in sorted_list:
            if file_data.fuzzy_license_match:
                fuzzy_license_match = file_data.fuzzy_license_match
                fuzzy_license_match_count += 1
                print(f"{"File: "}{Path(file_data.file_path).relative_to(Config.assessments_dir)}")
                #print(f"File: {Path(file_data.file_path)}")
                print(f"{"License name: "}{fuzzy_license_match.license_name}")
                print(f"Match percent: {fuzzy_license_match.match_percent:.2f}%")
                print(f"Expected match version: {fuzzy_license_match.expected_version}")
                print(f"Found match version: {fuzzy_license_match.found_version}")
                if fuzzy_license_match.found_version != fuzzy_license_match.expected_version:
                    print("Version mismatch")
                print("Matched substring:")
                print(fuzzy_license_match.matched_substring)

        print(f"{"Total files with fuzzy license match: "}{fuzzy_license_match_count}")


def merge_sort(arr):
    arr = Config.file_data_manager.get_all_file_data()

    if len(arr) > 1:
        mid = len(arr) // 2
        L = arr[:mid]
        R = arr[mid:]

        merge_sort(L)
        merge_sort(R)

        i = j = k = 0

        while i < len(L) and j < len(R):
            if L[i] > R[j]:  # Descending
                arr[k] = L[i]
                i += 1
            else:
                arr[k] = R[j]
                j += 1
            k += 1

        while i < len(L):
            arr[k] = L[i]
            i += 1
            k += 1

        while j < len(R):
            arr[k] = R[j]
            j += 1
            k += 1