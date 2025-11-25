import os
import utils
from pathlib import Path
from typing import Dict, List
from configuration import Configuration as Config
from loggers.full_license_search_logger import full_license_search_logger as Logger



def load_licenses(license_dirs: List[Path]) -> Dict[Path, str]:
    licenses: Dict[Path, str] = {}

    for base_dir in license_dirs:
        if not os.path.isdir(base_dir):
            Logger.warning(print(f"Warning: pattern directory does not exist or is not a directory: {base_dir}"))
            continue

        for dirpath, dirnames, filenames in os.walk(base_dir):
            for filename in filenames:
                if not filename.lower().endswith(".txt"):
                    continue

                license_path = Path(dirpath, filename).resolve()

                try:
                    with open(license_path, "r", encoding="utf-8") as f:
                        raw_text = f.read()
                except Exception as e:
                    Logger.debug(print(f"Could not read pattern file {license_path}: {e}"))
                    continue

                license_text = raw_text.strip()  # ignore extra whitespace before/after

                if not license_text:
                    # Skip completely empty patterns
                    continue

                licenses[license_path] = license_text

    return licenses


def search_assessment_files_for_full_license_header():
    licenses = load_licenses([Config.license_headers_dir])
    #licenses = load_licenses([Config.licenses_normalized_dir])
    #licenses = load_licenses([Config.manual_licenses_dir])

    # Pre-normalize all patterns once
    license_headers: Dict[Path, str] = {
        path: utils.normalize_without_empty_lines_and_dates(text)
        for path, text in licenses.items()
    }

    #utils.compare_values_of_two_dict(licenses, normalized_licenses)

    # Iterate over all files you've already read into FileData
    for file_data in Config.file_data_manager.get_all_file_data():
        file_text = utils.to_text(file_data.file_content)
        file_text = utils.normalize_without_empty_lines_and_dates(file_text)
        license_matches = []
        for license_path, license_text in license_headers.items():
            if license_text and license_text in file_text:
                license_name = utils.get_file_name_from_path_without_extension(license_path)
                license_match = {"License_name": license_name, "License_text": license_text}
                license_matches.append(license_match)
        file_data.license_matches = license_matches
        if file_data.license_matches:
            file_data.license_match_strength = "EXACT"
            file_data.license_name = ",".join(d["License_name"] for d in file_data.license_matches)


def search_assessment_file_headers_for_full_license_header():
    #license_headers = load_licenses([Config.license_headers_dir])
    #license_headers = load_licenses([Config.license_headers_normalized_dir])
    license_headers = load_licenses([Config.manual_license_headers_dir])

    # Pre-normalize all patterns once
    license_headers: Dict[Path, str] = {
        path: utils.normalize_without_empty_lines_and_dates(text)
        for path, text in license_headers.items()
    }

    #utils.compare_values_of_two_dict(licenses, normalized_licenses)

    # Iterate over all files you've already read into FileData
    for file_data in Config.file_data_manager.get_all_file_data():
        if file_data.file_header:
            file_header = utils.to_text(file_data.file_header)
            file_header = utils.normalize_without_empty_lines_and_dates(file_header)
            license_matches = []
            for license_header_path, license_header_text in license_headers.items():
                if license_header_text and license_header_text in file_header:
                    license_header_name = utils.get_file_name_from_path_without_extension(license_header_path)
                    license_match = {"License_name": license_header_name, "License_text": license_header_text}
                    license_matches.append(license_match)
            file_data.license_matches = license_matches
            if file_data.license_matches:
                file_data.license_match_strength = "EXACT"
                file_data.license_name = ",".join(d["License_name"] for d in file_data.license_matches)


if __name__ == "__main__":
    #search_assessment_files_for_full_license_header()
    search_assessment_file_headers_for_full_license_header()