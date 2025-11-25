from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Union
import re
from collections import Counter
import utils
from configuration import Configuration as Config


@dataclass
class MatchResult:
    matched_substring: str
    match_percent: float
    start_index: int   # char index in the file text where the match region starts
    end_index: int     # char index (exclusive) where the match region ends
    expected_version: Optional[str] = None  # version found in the pattern (license text)
    found_version: Optional[str] = None     # version found in the file text


WORD_RE = re.compile(r"\S+")


@dataclass
class Token:
    raw: str      # original token text
    norm: str     # normalized form for comparison (lowercased)
    start: int    # char start index in the original text
    end: int      # char end index (exclusive)


def _tokenize(text: str) -> List[Token]:
    """
    Tokenize on whitespace and record character positions.
    This assumes you've already done any punctuation stripping you want
    *before* calling this function.
    """
    tokens: List[Token] = []
    for m in WORD_RE.finditer(text):
        raw = m.group(0)
        start, end = m.span()
        norm = raw.lower()
        tokens.append(Token(raw=raw, norm=norm, start=start, end=end))
    return tokens


def _lcs_dp_with_indices(a_seq: List[str], b_seq: List[str]):
    """
    Compute LCS length and one concrete LCS alignment between
    sequences a_seq (pattern) and b_seq (text).

    Returns:
      lcs_len, pairs

      where pairs is a list of (i_in_a, j_in_b) for each matched token,
      in order.
    """
    m, n = len(a_seq), len(b_seq)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        ai = a_seq[i - 1]
        row = dp[i]
        prev_row = dp[i - 1]
        for j in range(1, n + 1):
            if ai == b_seq[j - 1]:
                row[j] = prev_row[j - 1] + 1
            else:
                # inline max(prev_row[j], row[j-1]) to avoid function call
                above = prev_row[j]
                left = row[j - 1]
                row[j] = above if above >= left else left

    # Backtrack to recover one LCS alignment
    i, j = m, n
    pairs: List[tuple[int, int]] = []
    while i > 0 and j > 0:
        if a_seq[i - 1] == b_seq[j - 1]:
            pairs.append((i - 1, j - 1))
            i -= 1
            j -= 1
        else:
            if dp[i - 1][j] >= dp[i][j - 1]:
                i -= 1
            else:
                j -= 1

    pairs.reverse()
    return dp[m][n], pairs


def _select_longest_contiguous_run(pairs: List[tuple[int, int]]) -> List[tuple[int, int]]:
    """
    From the list of LCS index pairs, select the longest run where both
    pattern and text indices increase by 1 on each step (true contiguous block).
    """
    if not pairs:
        return []

    best_start = 0
    best_end = 0
    best_len = 1

    start = 0
    for i in range(1, len(pairs)):
        ai, aj = pairs[i - 1]
        bi, bj = pairs[i]
        if not (bi == ai + 1 and bj == aj + 1):
            run_len = i - start
            if run_len > best_len:
                best_len = run_len
                best_start = start
                best_end = i - 1
            start = i

    run_len = len(pairs) - start
    if run_len > best_len:
        best_len = run_len
        best_start = start
        best_end = len(pairs) - 1

    return pairs[best_start:best_end + 1]


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


STRONG_MATCH_THRESHOLD = 80.0   # percent
MIN_KEEP_PERCENT = 50.0         # percent (your global threshold)

@dataclass
class PreparedText:
    raw_text: str
    tokens: List[Token]
    norms: List[str]
    freq: Dict[str, int]
    version: Optional[str]


def prepare_text(normalized_text: str) -> PreparedText:
    """
    normalized_text: *already* run through your
      utils.remove_punctuation_and_normalize_text(...) (lowercased, etc.)
    """
    tokens = _tokenize(normalized_text)
    norms = [t.norm for t in tokens]
    freq = Counter(norms)
    version = _extract_version(normalized_text)
    return PreparedText(
        raw_text=normalized_text,
        tokens=tokens,
        norms=norms,
        freq=freq,
        version=version,
    )


def fuzzy_match_prepared(
    pattern: PreparedText,   # license text (reference)
    text: PreparedText       # file text (actual)
) -> Optional[MatchResult]:
    """
    Fuzzy match `pattern` (license) against `text` (file), using the same
    logic as before, but assuming both are pre-tokenized and pre-counted.

    Returns None if:
      - there is no LCS, or
      - even in the best case the match cannot exceed MIN_KEEP_PERCENT.
    """
    pattern_tokens = pattern.tokens
    text_tokens = text.tokens

    if not pattern_tokens or not text_tokens:
        return None

    m = len(pattern_tokens)

    # --- 1) FAST UPPER-BOUND PRUNING ---
    # Max possible LCS <= multiset intersection size
    overlap = 0
    freq_pat = pattern.freq
    freq_txt = text.freq
    for w, c_pat in freq_pat.items():
        c_txt = freq_txt.get(w)
        if c_txt:
            overlap += c_txt if c_txt < c_pat else c_pat

    max_possible_percent = overlap / m * 100.0
    if max_possible_percent < MIN_KEEP_PERCENT:
        # Even in the best-case alignment, we'd never exceed your 50% threshold.
        # So skip the expensive DP entirely.
        return None

    # --- 2) FULL LCS DP (same logic as before) ---
    pattern_seq = pattern.norms
    text_seq = text.norms

    lcs_len, pairs = _lcs_dp_with_indices(pattern_seq, text_seq)
    if lcs_len == 0 or not pairs:
        return None

    lcs_percent = lcs_len / m * 100.0

    # --- 3) Strong vs weak match logic (unchanged) ---
    if lcs_percent >= STRONG_MATCH_THRESHOLD:
        # Strong match: match_percent uses full LCS; substring uses all LCS tokens.
        match_percent = lcs_percent
        matched_text_indices = sorted({j for (_, j) in pairs})
    else:
        # Weak/medium: only longest contiguous block and base percent on that.
        contiguous_pairs = _select_longest_contiguous_run(pairs)
        if not contiguous_pairs:
            return None
        block_len = len(contiguous_pairs)
        match_percent = block_len / m * 100.0
        matched_text_indices = [j for (_, j) in contiguous_pairs]

    if not matched_text_indices:
        return None

    # Build matched substring from file tokens
    t_tokens = text_tokens
    matched_substring = " ".join(t_tokens[i].raw for i in matched_text_indices)
    first_idx = matched_text_indices[0]
    last_idx = matched_text_indices[-1]
    start_index = t_tokens[first_idx].start
    end_index = t_tokens[last_idx].end

    return MatchResult(
        matched_substring=matched_substring,
        match_percent=match_percent,
        start_index=start_index,
        end_index=end_index,
        expected_version=pattern.version,
        found_version=text.version,
    )


def search_all_assessment_files_for_fuzzy_license_matches(license_dirs: List[Path]):
    # 1) Load and normalize license texts only once
    raw_licenses = utils.load_file_contents_from_directory(license_dirs)

    # Normalize license texts (you’re already doing this)
    normalized_licenses: Dict[Path, str] = {
        path: utils.remove_punctuation_and_normalize_text(text)
        for path, text in raw_licenses.items()
    }

    # 2) Pre-prepare all licenses (tokenize, freq, version) once
    prepared_licenses: Dict[Path, PreparedText] = {}
    for path, norm_text in normalized_licenses.items():
        if norm_text:  # skip empty license files
            prepared_licenses[path] = prepare_text(norm_text)

    # 3) Iterate files and compare against each prepared license
    for file_data in Config.file_data_manager.get_all_file_data():
        # Normalize file content once
        file_content_norm = utils.remove_punctuation_and_normalize_text(file_data.file_content)
        if not file_content_norm:
            continue

        # Prepare file text once
        prepared_file = prepare_text(file_content_norm)

        # 4) Nested loop: licenses × file (but now with pruning + cached prep)
        for license_path, prepared_license in prepared_licenses.items():
            # Fast fuzzy match using pre-tokenized/pre-counted data
            fuzzy_match_result = fuzzy_match_prepared(prepared_license, prepared_file)

            # Same threshold logic as before
            if fuzzy_match_result and fuzzy_match_result.match_percent > 50.0:
                license_name = utils.get_file_name_from_path_without_extension(license_path)
                fuzzy_license_match = {
                    "License_name": license_name,
                    "Fuzzy_license_match": fuzzy_match_result,
                }
                file_data.fuzzy_license_matches.append(fuzzy_license_match)

                # Logging / diagnostics
                print(f"File: {file_data.file_path}")
                print(f"License name: {license_name}")
                print(f"Match percent: {fuzzy_match_result.match_percent:.2f}%")
                print(f"Expected match version: {fuzzy_match_result.expected_version}")
                print(f"Found match version: {fuzzy_match_result.found_version}")
                print("Matched substring:")
                print(fuzzy_match_result.matched_substring)



# Example usage:
if __name__ == "__main__":

    file_path = "C:/license_assessments/my-ubi8-java8/blobs/sha256/8f42ad26ccdae7ec04dac9501e3c011a88c8663559699974ecf1697999914f0d_extracted/usr/share/licenses/libsigsegv/COPYING"
    lic_path = Path(Config.root_dir, "input/license_headers/GPL-2.0-or-later.txt")

    try:
        # Try reading as text
        with open(lic_path, "r", encoding="utf-8") as f:
            lic_content: Union[str, bytes] = f.read()
    except UnicodeDecodeError:
        # Fallback to binary
        with open(lic_path, "rb") as f:
            lic_content = f.read()
    except Exception as e:
        print(f"Could not read {lic_path}: {e}")

    try:
        # Try reading as text
        with open(file_path, "r", encoding="utf-8") as f:
            file_content: Union[str, bytes] = f.read()
    except UnicodeDecodeError:
        # Fallback to binary
        with open(file_path, "rb") as f:
            file_content = f.read()
    except Exception as e:
        print(f"Could not read {lic_path}: {e}")

    #result = fuzzy_match_prepared(lic_content, file_content)