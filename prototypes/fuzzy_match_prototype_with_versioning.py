import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Union, Optional, Tuple, List, Dict
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

    # Build DP table
    for i in range(1, m + 1):
        ai = a_seq[i - 1]
        for j in range(1, n + 1):
            if ai == b_seq[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = dp[i - 1][j] if dp[i - 1][j] >= dp[i][j - 1] else dp[i][j - 1]

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
        # check if this continues the contiguous run
        if not (bi == ai + 1 and bj == aj + 1):
            run_len = i - start
            if run_len > best_len:
                best_len = run_len
                best_start = start
                best_end = i - 1
            start = i

    # final run
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


STRONG_MATCH_THRESHOLD = 80.0  # percent


def fuzzy_match_in_file(pattern: str, file_text: str | Path) -> Optional[MatchResult]:
    """
    Fuzzy match `pattern` (license text, reference) against the contents of
    `file_path` (actual file text).

    Both pattern and file text should be normalized consistently *before*
    this (e.g. punctuation stripped, lowercased, etc.), as you are already doing.

    Primary metric:

        lcs_percent = LCS(pattern_words, text_words) / len(pattern_words) * 100

    - If lcs_percent >= STRONG_MATCH_THRESHOLD:
        match_percent = lcs_percent
        matched_substring = stitched from all LCS tokens (GPL cases)

    - Else (weak/medium match):
        match_percent = longest_contiguous_block_len / len(pattern_words) * 100
        matched_substring = that longest contiguous block only (short phrase)

    Version detection:
      - expected_version: from the pattern (license text)
      - found_version:    from the file text
    """

    if not pattern or not file_text:
        return None

    pattern_tokens = _tokenize(pattern)
    text_tokens = _tokenize(file_text)

    if not pattern_tokens or not text_tokens:
        return None

    pattern_seq = [t.norm for t in pattern_tokens]
    text_seq = [t.norm for t in text_tokens]

    # 1) LCS and alignment
    lcs_len, pairs = _lcs_dp_with_indices(pattern_seq, text_seq)
    if lcs_len == 0 or not pairs:
        return None

    lcs_percent = lcs_len / len(pattern_tokens) * 100.0

    # 2) Decide strong vs weak/medium
    if lcs_percent >= STRONG_MATCH_THRESHOLD:
        # Strong match: use full LCS coverage and all LCS tokens for substring
        match_percent = lcs_percent
        matched_text_indices = sorted({j for (_, j) in pairs})
    else:
        # Weak/medium: use only longest contiguous block both for substring
        # and for computing match_percent
        contiguous_pairs = _select_longest_contiguous_run(pairs)
        if not contiguous_pairs:
            return None
        block_len = len(contiguous_pairs)
        match_percent = block_len / len(pattern_tokens) * 100.0
        matched_text_indices = [j for (_, j) in contiguous_pairs]

    if not matched_text_indices:
        return None

    matched_substring = " ".join(text_tokens[i].raw for i in matched_text_indices)
    first_idx = matched_text_indices[0]
    last_idx = matched_text_indices[-1]

    start_index = text_tokens[first_idx].start
    end_index = text_tokens[last_idx].end

    expected_version = _extract_version(pattern)
    found_version = _extract_version(file_text)

    return MatchResult(
        matched_substring=matched_substring,
        match_percent=match_percent,
        start_index=start_index,
        end_index=end_index,
        expected_version=expected_version,
        found_version=found_version,
    )


def search_all_assessment_files_for_fuzzy_license_matches(license_dirs: List[Path]):
    licenses = utils.load_file_contents_from_directory(license_dirs)

    licenses: Dict[Path, str] = {
        path: utils.remove_punctuation_and_normalize_text(text)
        for path, text in licenses.items()
    }

    for file_data in Config.file_data_manager.get_all_file_data():
        file_content = utils.remove_punctuation_and_normalize_text(file_data.file_content)
        for license_path, license_content in licenses.items():
            if license_content and file_content:
                fuzzy_match_result = fuzzy_match_in_file(license_content, file_content)
                if fuzzy_match_result and fuzzy_match_result.match_percent > 50.0:
                    license_name = utils.get_file_name_from_path_without_extension(license_path)
                    fuzzy_license_match = {"License_name": license_name, "Fuzzy_license_match": fuzzy_match_result}
                    file_data.fuzzy_license_matches.append(fuzzy_license_match)
                    print(f"License name: {utils.get_file_name_from_path_without_extension(license_path)}")
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
            content: Union[str, bytes] = f.read()
    except UnicodeDecodeError:
        # Fallback to binary
        with open(lic_path, "rb") as f:
            content = f.read()
    except Exception as e:
        print(f"Could not read {lic_path}: {e}")

    result = fuzzy_match_in_file(content, file_path)

