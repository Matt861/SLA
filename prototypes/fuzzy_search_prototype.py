import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Union, Optional, Tuple, List
import utils
from configuration import Configuration as Config


@dataclass
class MatchResult:
    matched_substring: str
    match_percent: float
    start_index: int   # char index in the file text where the match region starts
    end_index: int     # char index (exclusive) where the match region ends


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
    pairs = []
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


def fuzzy_match_in_file(pattern: str, file_path: str | Path) -> Optional[MatchResult]:
    """
    Fuzzy match `pattern` (string A) against the contents of `file_path`
    (string B or C).

    Both pattern and file text should be normalized consistently before
    calling this (e.g. punctuation stripped, lowercased, etc., as you’re
    already doing).

    match_percent is:

        LCS(pattern_words, text_words) / len(pattern_words) * 100

    i.e., *what percent of the words in pattern A appear in order in the file*.
    """
    file_path = Path(file_path)
    file_text = file_path.read_text(encoding="utf-8", errors="ignore")
    file_text = utils.remove_punctuation_from_text(file_text)
    file_text = utils.normalize_for_compare(file_text)

    if not pattern or not file_text:
        return None

    # Tokenize pattern (A) and text (B/C)
    pattern_tokens = _tokenize(pattern)
    text_tokens = _tokenize(file_text)

    if not pattern_tokens or not text_tokens:
        return None

    pattern_seq = [t.norm for t in pattern_tokens]
    text_seq = [t.norm for t in text_tokens]

    # Compute true LCS between pattern and text at word level
    lcs_len, pairs = _lcs_dp_with_indices(pattern_seq, text_seq)

    if lcs_len == 0 or not pairs:
        return None

    # === 1) Percentage: how much of A is found in the file? ===
    match_percent = lcs_len / len(pattern_tokens) * 100.0

    # === 2) Matched substring: ONLY include matched tokens, not the whole span ===
    # Collect the text indices that participate in the LCS
    matched_text_indices = [j for (_, j) in pairs]

    # Build the substring from the original file text using only matched tokens
    # (this removes everything like "brief"/"year"/address parts that don't match)
    matched_substring = " ".join(text_tokens[i].raw for i in matched_text_indices)

    # Character span in the original file text from first to last matched token
    first_text_idx = matched_text_indices[0]
    last_text_idx = matched_text_indices[-1]
    start_index = text_tokens[first_text_idx].start
    end_index = text_tokens[last_text_idx].end

    return MatchResult(
        matched_substring=matched_substring,
        match_percent=match_percent,
        start_index=start_index,
        end_index=end_index,
    )


# Example usage:
if __name__ == "__main__":
    #pattern = "This program is free software; you can redistribute it and/or modify it"
    #result = fuzzy_match_in_file(pattern, "example.txt")

    file_path=Path(Config.root_dir, "input/license_headers/GPL-3.0-or-later.txt")
    #file_path = Path(Config.root_dir, "input/license_headers/GPL-2.0-or-later.txt")
    #file_path = Path(Config.root_dir, "input/licenses/GPL-2.0-or-later.txt")

    test_string = """    <one line to give the program's name and a brief idea of what it does.>
    Copyright (C) <year>  <name of author>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA."""

    test_string = utils.remove_punctuation_from_text(test_string)
    test_string = utils.normalize_for_compare(test_string)
    print("Text to match in file: ")
    print(test_string)

    try:
        # Try reading as text
        with open(file_path, "r", encoding="utf-8") as f:
            content: Union[str, bytes] = f.read()
    except UnicodeDecodeError:
        # Fallback to binary
        with open(file_path, "rb") as f:
            content = f.read()
    except Exception as e:
        print(f"Could not read {file_path}: {e}")

    content = utils.remove_punctuation_from_text(content)
    content = utils.normalize_for_compare(content)
    print("License text: ")
    print(content)
    result = fuzzy_match_in_file(content, "C:/license_assessments/my-ubi8-java8/blobs/sha256/8f42ad26ccdae7ec04dac9501e3c011a88c8663559699974ecf1697999914f0d_extracted/usr/share/licenses/libsigsegv/COPYING")

    if result:
        print(f"Match percent: {result.match_percent:.2f}%")
        print(f"Match starts at index: {result.start_index}")
        print("Matched substring:")
        print(result.matched_substring)
    else:
        print("No good match found.")
