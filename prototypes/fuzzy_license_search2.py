import re
from dataclasses import dataclass
from typing import Optional, Tuple, Union
import os
import utils
from pathlib import Path
from typing import Dict, List
from configuration import Configuration as Config
from loggers.full_license_search_logger import full_license_search_logger as Logger

WORD_RE = re.compile(r'\S+')


@dataclass
class MatchResult:
    matched_substring: str
    match_percent: float
    start_index: int
    end_index: int


def _ensure_text(value: Union[str, bytes]) -> str:
    """
    Ensure we are working with a str. If bytes, decode as UTF-8 (ignoring errors).
    """
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return value


def _tokenize_with_spans(text: str):
    """
    Split text into 'words' using whitespace, returning a list of:
        {
          'word': original_word_text,
          'norm': lowercased_word_for_matching,
          'start': start_char_index,
          'end': end_char_index
        }
    """
    tokens = []
    for m in WORD_RE.finditer(text):
        word = m.group(0)
        tokens.append(
            {
                "word": word,
                "norm": word.lower(),
                "start": m.start(),
                "end": m.end(),
            }
        )
    return tokens


def best_fuzzy_substring_match(
    file_content: Union[str, bytes],
    pattern_content: Union[str, bytes],
    anchor_size: int = 3,
) -> Optional[MatchResult]:
    """
    Compare a large file string (A) against a potentially noisy substring (B).

    - file_content (A): full content of the file
    - pattern_content (B): text/bytes that may be in the file, but may contain
      extra words, characters, spaces, and newlines.
    - anchor_size: number of consecutive words that must match to start a recording
      (default = 3).

    Returns:
        MatchResult with the substring of A that best matches B and the
        percentage of words from B that were matched, or None if no anchors found.
    """
    # Normalize inputs to strings
    file_text = _ensure_text(file_content)
    pattern_text = _ensure_text(pattern_content)

    # Tokenize both strings into words
    file_tokens = _tokenize_with_spans(file_text)
    pattern_tokens_raw = [m.group(0) for m in WORD_RE.finditer(pattern_text)]
    pattern_tokens = [w.lower() for w in pattern_tokens_raw]

    if not file_tokens or len(pattern_tokens) < anchor_size:
        return None

    # Build lookup: anchor (tuple of N words) -> list of positions in pattern_tokens
    anchor_to_pattern_positions = {}
    for j in range(len(pattern_tokens) - anchor_size + 1):
        anchor = tuple(pattern_tokens[j : j + anchor_size])
        anchor_to_pattern_positions.setdefault(anchor, []).append(j)

    best_result: Optional[MatchResult] = None
    n_file = len(file_tokens)
    n_pattern = len(pattern_tokens)

    # Slide over file tokens and look for any anchor that appears in the pattern
    for i in range(n_file - anchor_size + 1):
        anchor = tuple(t["norm"] for t in file_tokens[i : i + anchor_size])
        pattern_positions = anchor_to_pattern_positions.get(anchor)
        if not pattern_positions:
            continue  # this 3-word sequence from A is not in B

        # For each position in B where this anchor appears, start a recording
        for j0 in pattern_positions:
            # We already know that the next anchor_size words match starting at i and j0
            matches = anchor_size
            last_match_file_idx = i + anchor_size - 1

            fi = i + anchor_size  # file index after the anchor
            pj = j0 + anchor_size  # pattern index after the anchor

            # Walk forward through both token streams until one ends,
            # counting matching words and keeping track of the last matching file index.
            while fi < n_file and pj < n_pattern:
                if file_tokens[fi]["norm"] == pattern_tokens[pj]:
                    matches += 1
                    last_match_file_idx = fi
                # Move both forwards; this is a simple 1:1 alignment
                fi += 1
                pj += 1

            # "Remove text after the last full word match":
            # we cut the recording at the end of last_match_file_idx.
            start_char = file_tokens[i]["start"]
            end_char = file_tokens[last_match_file_idx]["end"]
            substring = file_text[start_char:end_char]

            match_percent = (matches / n_pattern) * 100.0

            if best_result is None or match_percent > best_result.match_percent:
                best_result = MatchResult(
                    matched_substring=substring,
                    match_percent=match_percent,
                    start_index=start_char,
                    end_index=end_char,
                )

    return best_result


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


def search_assessment_files_for_fuzzy_license_header_match():
    license_headers = load_licenses([Config.license_headers_dir])
    #license_headers = load_licenses([Config.licenses_normalized_dir])
    #license_headers = load_licenses([Config.manual_licenses_dir])

    # Pre-normalize all patterns once
    license_headers: Dict[Path, str] = {
        path: utils.normalize_without_empty_lines_and_dates(text)
        for path, text in license_headers.items()
    }

    #utils.compare_values_of_two_dict(licenses, normalized_licenses)

    # Iterate over all files you've already read into FileData
    for file_data in Config.file_data_manager.get_all_file_data():
        file_text = utils.to_text(file_data.file_content)
        file_text = utils.normalize_without_empty_lines_and_dates(file_text)
        license_matches = []
        for license_path, license_text in license_headers.items():
            if license_text and file_text:
                result = best_fuzzy_substring_match(file_text, license_text, anchor_size=3)
                if result and result.match_percent > 50.0:
                    license_name = utils.get_file_name_from_path_without_extension(license_path)
                    license_match = {"License_name": license_name, "License_text": license_text}
                    license_matches.append(license_match)
                    print(f"Fuzzy matched file: {Path(file_data.file_path).relative_to(Config.assessments_dir)}")
                    print(f"Fuzzy match percent: {result.match_percent:.2f}%")
                    print("Fuzzy match result:")
                    print(result.matched_substring)
        file_data.license_matches = license_matches
        if file_data.license_matches:
            file_data.license_match_strength = "STRONG"
            file_data.license_name = ",".join(d["License_name"] for d in file_data.license_matches)


if __name__ == "__main__":
    search_assessment_files_for_fuzzy_license_header_match()


# Example usage:
# if __name__ == "__main__":
#     A = """
#     This program and the accompanying materials are dual-licensed under
#     either the terms of the Eclipse Public License v1.0 as published by
#     the Eclipse Foundation or, per the licensee's choosing, under the
#     terms of the GNU Lesser General Public License version 2.1.
#     """
#
#     B = """
#     the accompanying materials are dual licensed under either the terms of
#     the Eclipse Public License v1.0 as published by the Eclipse Foundation
#     or (per the licensee's choosing) under the terms of the GNU Lesser
#     General Public License version 2.1 as published by the Free Software Foundation
#     """
#
#     result = best_fuzzy_substring_match(A, B, anchor_size=3)
#     if result:
#         print("Best matched substring:")
#         print(result.matched_substring)
#         print(f"\nMatch percent: {result.match_percent:.2f}%")
#     else:
#         print("No suitable match found.")
