from configuration import Configuration as Config
from search.fuzzy_license_search import MatchResult


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