import re
from dataclasses import dataclass
import os
import utils
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional, Union
from configuration import Configuration as Config
from loggers.fuzzy_license_header_search_logger import fuzzy_license_header_search_logger as Logger
from tools.index_file_content import FileIndex, PatternIndex, MatchResult, build_file_indexes, \
    build_pattern_indexes_from_dict


# WORD_RE = re.compile(r"\S+")


# def _ensure_text(value: Union[str, bytes]) -> str:
#     if isinstance(value, bytes):
#         return value.decode("utf-8", errors="ignore")
#     return value


# def _tokenize_with_spans(text: str):
#     tokens = []
#     for m in WORD_RE.finditer(text):
#         word = m.group(0)
#         tokens.append(
#             {
#                 "word": word,
#                 "norm": word.lower(),
#                 "start": m.start(),
#                 "end": m.end(),
#             }
#         )
#     return tokens


# @dataclass
# class FileIndex:
#     source_obj: Any  # your model instance for stringA
#     text: str
#     tokens: List[Dict]
#     trigram_positions: Dict[Tuple[str, str, str], List[int]]


# @dataclass
# class PatternIndex:
#     source_path: Path  # the key from Dict[Path, str]
#     text: str          # the pattern string (stringB)
#     tokens: List[str]
#     anchor_positions: Dict[Tuple[str, str, str], List[int]]
#     anchor_keys: set


# @dataclass
# class MatchResult:
#     matched_substring: str
#     match_percent: float
#     start_index: int
#     end_index: int
#     expected_version: Optional[str] = None  # version found in the pattern (license text)
#     found_version: Optional[str] = None     # version found in the file text
#     license_name: Optional[str] = None


# def build_file_indexes(
#     model_objects,          # e.g. List[FileData]
#     anchor_size: int = 3,
# ) -> List[FileIndex]:
#     file_indexes: List[FileIndex] = []
#
#     for obj in model_objects:
#         # Adjust property name as needed (e.g. obj.file_content)
#         text = _ensure_text(obj.file_content)
#         text = utils.remove_punctuation_and_normalize_text(text)
#         #text = utils.placeholder_to_regex(text)
#         tokens = _tokenize_with_spans(text)
#
#         trigram_positions: Dict[Tuple[str, str, str], List[int]] = {}
#         for i in range(len(tokens) - anchor_size + 1):
#             anchor = tuple(tokens[i + k]["norm"] for k in range(anchor_size))
#             trigram_positions.setdefault(anchor, []).append(i)
#
#         file_indexes.append(
#             FileIndex(
#                 source_obj=obj,
#                 text=text,
#                 tokens=tokens,
#                 trigram_positions=trigram_positions,
#             )
#         )
#
#     return file_indexes



# def build_pattern_indexes_from_dict(
#     patterns: Dict[Path, Union[str, bytes]],
#     anchor_size: int = 3,
# ) -> List[PatternIndex]:
#     pattern_indexes: List[PatternIndex] = []
#
#     for path, content in patterns.items():
#         text = _ensure_text(content)
#         raw_tokens = [m.group(0) for m in WORD_RE.finditer(text)]
#         tokens = [w.lower() for w in raw_tokens]
#
#         if len(tokens) < anchor_size:
#             pattern_indexes.append(
#                 PatternIndex(
#                     source_path=path,
#                     text=text,
#                     tokens=tokens,
#                     anchor_positions={},
#                     anchor_keys=set(),
#                 )
#             )
#             continue
#
#         anchor_positions: Dict[Tuple[str, str, str], List[int]] = {}
#         for j in range(len(tokens) - anchor_size + 1):
#             anchor = tuple(tokens[j + k] for k in range(anchor_size))
#             anchor_positions.setdefault(anchor, []).append(j)
#
#         pattern_indexes.append(
#             PatternIndex(
#                 source_path=path,
#                 text=text,
#                 tokens=tokens,
#                 anchor_positions=anchor_positions,
#                 anchor_keys=set(anchor_positions.keys()),
#             )
#         )
#
#     return pattern_indexes


def _align_with_gaps(
    file_tokens: List[Dict],
    pattern_tokens: List[str],
    fi_start: int,
    pj_start: int,
    gap_lookahead: int = 5,
) -> Tuple[int, int]:
    """
    Greedy alignment that allows small insertions/deletions on either side.

    Returns:
        (extra_matches, last_match_file_idx)

    - extra_matches: number of matches *after* the starting indices
    - last_match_file_idx: index in file_tokens of the last matched word
                           (or fi_start-1 if none matched).
    """
    n_file = len(file_tokens)
    n_pattern = len(pattern_tokens)

    fi = fi_start
    pj = pj_start
    matches = 0
    last_match_file_idx = fi_start - 1

    while fi < n_file and pj < n_pattern:
        if file_tokens[fi]["norm"] == pattern_tokens[pj]:
            matches += 1
            last_match_file_idx = fi
            fi += 1
            pj += 1
        else:
            # Try to re-sync by looking ahead in file for pattern_tokens[pj]
            found_in_file = None
            for k in range(1, gap_lookahead + 1):
                if fi + k >= n_file:
                    break
                if file_tokens[fi + k]["norm"] == pattern_tokens[pj]:
                    found_in_file = fi + k
                    break

            # Try to re-sync by looking ahead in pattern for file_tokens[fi]
            found_in_pattern = None
            for k in range(1, gap_lookahead + 1):
                if pj + k >= n_pattern:
                    break
                if pattern_tokens[pj + k] == file_tokens[fi]["norm"]:
                    found_in_pattern = pj + k
                    break

            if found_in_file is not None and (
                found_in_pattern is None
                or (found_in_file - fi) <= (found_in_pattern - pj)
            ):
                # Treat as insertion(s) in file: skip a few file tokens
                fi = found_in_file
            elif found_in_pattern is not None:
                # Treat as insertion(s) in pattern: skip a few pattern tokens
                pj = found_in_pattern
            else:
                # Can't re-sync locally, just advance both
                fi += 1
                pj += 1

    return matches, last_match_file_idx


def best_match_indexed(
    f: FileIndex,
    p: PatternIndex,
    anchor_size: int = 3,
    gap_lookahead: int = 5,
) -> Optional[MatchResult]:
    file_tokens = f.tokens
    pattern_tokens = p.tokens
    n_file = len(file_tokens)
    n_pattern = len(pattern_tokens)

    if not file_tokens or n_pattern < anchor_size:
        return None

    # Fast skip: if no shared anchor, no need to align
    common_anchors = f.trigram_positions.keys() & p.anchor_keys
    if not common_anchors:
        return None

    best_result: Optional[MatchResult] = None

    for anchor in common_anchors:
        file_positions = f.trigram_positions[anchor]
        pattern_positions = p.anchor_positions[anchor]

        for i in file_positions:
            for j0 in pattern_positions:
                # We already know the first `anchor_size` words match
                matches = anchor_size
                last_match_file_idx = i + anchor_size - 1

                fi_start = i + anchor_size
                pj_start = j0 + anchor_size

                extra_matches, extra_last_idx = _align_with_gaps(
                    file_tokens,
                    pattern_tokens,
                    fi_start,
                    pj_start,
                    gap_lookahead=gap_lookahead,
                )

                matches += extra_matches
                if extra_matches > 0:
                    last_match_file_idx = extra_last_idx

                start_char = file_tokens[i]["start"]
                end_char = file_tokens[last_match_file_idx]["end"]
                substring = f.text[start_char:end_char]

                match_percent = (matches / n_pattern) * 100.0

                if best_result is None or match_percent > best_result.match_percent:
                    best_result = MatchResult(
                        matched_substring=substring,
                        match_percent=match_percent,
                        start_index=start_char,
                        end_index=end_char,
                    )

    return best_result


_VERSION_RE = re.compile(
    r"""
    \bversion\s+(\d+(?:\.\d+)?)   # "version" <num>
      |\bv\.?\s*(\d+(?:\.\d+)?)     # "v" or "v." <num>
      |\blicense\s+(\d+(?:\.\d+)?)
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _extract_version(text: str) -> Optional[str]:
    """
    Extract the first version number indicated by one of:
      - "version" <number>
      - "v" or "v." <number>
      - "license" <number>

    Returns just the numeric part as a string (e.g. "2", "3.0"), or None if not found.
    """
    m = _VERSION_RE.search(text)
    if not m:
        return None
    for g in m.groups():
        if g is not None:
            return g
    return None


def _extract_versions(text: str) -> Optional[List[str]]:
    """
    Extract all version numbers indicated by one of:
      - "version" <number>
      - "v" or "v." <number>
      - "license" <number>

    Returns a list of numeric parts as strings (e.g. ["2", "3.0"]), or None if none found.
    """
    if not text:
        return None

    versions: List[str] = []

    # Use finditer instead of search to get all matches
    for match in _VERSION_RE.finditer(text):
        # Keep the same "first non-None group" logic per match
        for g in match.groups():
            if g is not None:
                # Only add if it's not already in the list (distinct versions)
                if g not in versions:
                    versions.append(g)
                break  # move to the next match

    return versions or None


def fuzzy_match_assessment_files_for_licenses(pattern_indexes):
    # license_headers = utils.load_file_contents_from_directory(license_dirs)
    #
    # # Pre-normalize all patterns once
    # license_headers: Dict[Path, str] = {
    #     path: utils.remove_punctuation_and_normalize_text(text)
    #     for path, text in license_headers.items()
    # }

    #utils.compare_values_of_two_dict(licenses, normalized_licenses)
    # file_indexes = build_file_indexes(Config.file_data_manager.get_all_file_data(), anchor_size=3)
    # pattern_indexes = build_pattern_indexes_from_dict(license_headers, anchor_size=3)
    for f_idx in Config.file_indexes:
        file_model = f_idx.source_obj  # original model instance
        for p_idx in pattern_indexes:
            pattern_path = p_idx.source_path  # the Path key from Dict[Path, str]
            fuzzy_match_result = best_match_indexed(f_idx, p_idx, anchor_size=3)
            if fuzzy_match_result and fuzzy_match_result.match_percent > 50.0:
                license_name = utils.get_file_name_from_path_without_extension(pattern_path)
                fuzzy_match_result.license_name = license_name
                fuzzy_match_result.expected_version = utils.extract_version_from_name(license_name)
                found_version = _extract_versions(fuzzy_match_result.matched_substring)
                #found_version = _extract_version(fuzzy_match_result.matched_substring)
                fuzzy_match_result.found_version = utils.normalize_number_string(found_version)
                file_model.fuzzy_license_matches.append(fuzzy_match_result)
                # print(f"License name: {license_name}")
                # print(f"Match percent: {fuzzy_match_result.match_percent:.2f}%")
                # print(f"Expected match version: {fuzzy_match_result.expected_version}")
                # print(f"Found match version: {fuzzy_match_result.found_version}")
                # print("Matched substring:")
                # print(fuzzy_match_result.matched_substring)







if __name__ == "__main__":
    fuzzy_match_assessment_files_for_licenses()
