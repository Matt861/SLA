from collections import defaultdict
from typing import Dict, List

from configuration import Configuration as Config
from search.fuzzy_license_search import MatchResult


def is_match_percent_greater_than_all(fuzzy_license_match, best_fuzzy_matches):
    match_percent_is_greater_than_all = all(
        fuzzy_license_match.match_percent > result.match_percent
        for result in best_fuzzy_matches
    )

    return match_percent_is_greater_than_all

def determine_best_fuzzy_matches_from_file_data():
    for file_data in Config.file_data_manager.get_all_file_data():
        best_fuzzy_matches = []
        all_version_matches = []
        common_version_matches = []
        no_version_matches = []
        best_all_version_match_percent = 0.0
        best_all_version_match = None
        best_common_version_matches = []
        common_versions_found = []
        best_no_version_match_percent = 0.0
        best_no_version_match = None
        if file_data.fuzzy_license_matches:
            for fuzzy_license_match in file_data.fuzzy_license_matches:
                expected_versions = fuzzy_license_match.expected_versions
                found_versions = fuzzy_license_match.found_versions
                common_versions = [x for x in expected_versions if x in found_versions]
                if expected_versions == found_versions:
                    all_version_matches.append(fuzzy_license_match)
                elif common_versions:
                    common_version_matches.append(fuzzy_license_match)
                else:
                    no_version_matches.append(fuzzy_license_match)
            if all_version_matches:
                for all_version_match in all_version_matches:
                    if all_version_match.match_percent > best_all_version_match_percent:
                        best_all_version_match_percent = all_version_match.match_percent
                        best_all_version_match = all_version_match
                #best_fuzzy_matches.append(best_all_version_match)
            elif common_version_matches:
                by_found_version: Dict[str, List[MatchResult]] = defaultdict(list)
                for match in common_version_matches:
                    # Skip if no versions were found
                    if not match.found_versions:
                        continue

                    # If an object has multiple found_versions, it will appear in each group
                    for version in match.found_versions:
                        by_found_version[version].append(match)

                for common_version_match in common_version_matches:
                    for common_version in common_version_match.found_versions:
                        if not common_version in common_versions_found:
                            if not common_version_match in best_common_version_matches:
                                best_common_version_matches.append(common_version_match)
                                common_versions_found.append(common_version)
                        elif common_version in common_versions_found:
                            same_version_matches = by_found_version.get(common_version, [])
                            if is_match_percent_greater_than_all(common_version, same_version_matches):
                                #remove already matching version of lower percentage
                                best_common_version_matches = [
                                    match
                                    for match in best_common_version_matches
                                    if not (match.found_versions and common_version in match.found_versions)
                                ]
                                common_versions_found.append(common_version)
            elif no_version_matches:
                for no_version_match in no_version_matches:
                    if no_version_match.match_percent > best_no_version_match_percent:
                        best_no_version_match_percent = no_version_match.match_percent
                        best_no_version_match = no_version_match
        if best_all_version_match:
            file_data.license_names.append(best_all_version_match.license_name)
            file_data.fuzzy_license_match.append(best_all_version_match)
        elif best_common_version_matches:
            for best_common_version_match in best_common_version_matches:
                file_data.license_names.append(best_common_version_match.license_name)
                file_data.fuzzy_license_match.append(best_common_version_match)
        elif best_no_version_match:
            file_data.license_names.append(best_no_version_match.license_name)
            file_data.fuzzy_license_match.append(best_no_version_match)





def determine_best_fuzzy_match_from_file_data():
    for file_data in Config.file_data_manager.get_all_file_data():
        if file_data.fuzzy_license_matches:
            best_match_percent = 0.0
            best_exact_match_percent = 0.0
            best_fuzzy_match = None
            prior_match_version_was_exact = False
            for fuzzy_license_match in file_data.fuzzy_license_matches:
                expected_versions = fuzzy_license_match.expected_versions
                found_versions = fuzzy_license_match.found_versions
                if expected_versions == found_versions:
                    if fuzzy_license_match.match_percent > best_exact_match_percent:
                        best_match_percent = fuzzy_license_match.match_percent
                        best_exact_match_percent = fuzzy_license_match.match_percent
                        best_fuzzy_match = fuzzy_license_match
                        prior_match_version_was_exact = True
                elif not prior_match_version_was_exact and fuzzy_license_match.match_percent > best_match_percent:
                    best_match_percent = fuzzy_license_match.match_percent
                    best_fuzzy_match = fuzzy_license_match
                else:
                    if not expected_versions:
                        if fuzzy_license_match.match_percent > best_exact_match_percent:
                            best_match_percent = fuzzy_license_match.match_percent
                            best_exact_match_percent = fuzzy_license_match.match_percent
                            best_fuzzy_match = fuzzy_license_match
                            prior_match_version_was_exact = True
                    elif not prior_match_version_was_exact and fuzzy_license_match.match_percent > best_match_percent:
                        best_match_percent = fuzzy_license_match.match_percent
                        best_fuzzy_match = fuzzy_license_match
            file_data.license_names.append(best_fuzzy_match.license_name)
            file_data.fuzzy_license_match = best_fuzzy_match



# def determine_best_fuzzy_match_from_file_data():
#     for file_data in Config.file_data_manager.get_all_file_data():
#         if file_data.fuzzy_license_matches:
#             best_match_percent = 0.0
#             best_exact_match_percent = 0.0
#             best_fuzzy_match = None
#             prior_match_version_was_exact = False
#             for fuzzy_license_match in file_data.fuzzy_license_matches:
#                 expected_versions = fuzzy_license_match.expected_versions
#                 found_versions = fuzzy_license_match.found_versions
#                 if expected_versions == found_versions:
#                     if fuzzy_license_match.match_percent > best_exact_match_percent:
#                         best_match_percent = fuzzy_license_match.match_percent
#                         best_exact_match_percent = fuzzy_license_match.match_percent
#                         best_fuzzy_match = fuzzy_license_match
#                         prior_match_version_was_exact = True
#                 elif not prior_match_version_was_exact and fuzzy_license_match.match_percent > best_match_percent:
#                     best_match_percent = fuzzy_license_match.match_percent
#                     best_fuzzy_match = fuzzy_license_match
#             if file_data.license_name is None:
#                 file_data.license_name = best_fuzzy_match.license_name
#                 file_data.fuzzy_license_match = best_fuzzy_match




if __name__ == "__main__":
    determine_best_fuzzy_match_from_file_data()