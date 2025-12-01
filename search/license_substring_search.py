import utils
from input.license_substrings import license_substrings
from configuration import Configuration as Config


def search_assessment_files_for_license_substrings():
    for file_data in Config.file_data_manager.get_all_file_data():
        file_content = utils.remove_punctuation_and_normalize_text(file_data.file_content)
        license_matches = []
        for lic_name, lic_substrings in license_substrings.items():
            for lic_substring in lic_substrings:
                lic_substring_normalized = utils.remove_punctuation_and_normalize_text(lic_substring)
                if lic_substring_normalized and lic_substring_normalized in file_content:
                    license_match = {"License_name": lic_name, "License_text": lic_substring_normalized}
                    license_matches.append(license_match)
        if license_matches:
            file_data.license_matches.append(license_matches)
            file_data.license_match_strength = "STRONG"
            lic_match_names = [item["License_name"] for item in license_matches]
            for lic_match_name in lic_match_names:
                file_data.license_names.append(lic_match_name)
            #file_data.license_names.append([item["License_name"] for item in license_matches])


if __name__ == "__main__":
    search_assessment_files_for_license_substrings()