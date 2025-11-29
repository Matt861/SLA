import os
import re
import string
from pathlib import Path
from typing import Union, List, Dict, Optional

import unicodedata

_YEAR_OR_RANGE_RE = re.compile(
    r"\b(19|20)\d{2}(?:\s*[-–]\s*(19|20)\d{2})?\b"
)


def find_project_root(start: str | Path, markers=None) -> Path:
    """
    Walks up from `start` until it finds a directory containing
    one of the `markers` (e.g. pyproject.toml, .git, etc.).
    Returns the directory path as a Path.
    """
    # Usage inside any module/file
    # PROJECT_ROOT = find_project_root(__file__)

    if markers is None:
        markers = ("pyproject.toml", "setup.cfg", "setup.py", ".git", "requirements.txt", ".git", ".env")

    path = Path(start).resolve()
    if path.is_file():
        path = path.parent

    for parent in [path, *path.parents]:
        if any((parent / marker).exists() for marker in markers):
            return parent

    raise FileNotFoundError(f"Could not find project root starting from {start!r}")


def get_file_extension(path_or_filename):
    base = os.path.basename(path_or_filename)
    if base.startswith('.') and base.count('.') == 1:
        return base.lower()
    ext = os.path.splitext(base)[1]
    return ext.lower() if ext else base.lower()


def to_text(content: Union[str, bytes]) -> str:
    """
    Ensure we are working with a text string.
    If content is bytes, decode as UTF-8 (ignoring errors).
    """
    if isinstance(content, str):
        return content
    return content.decode("utf-8", errors="ignore")


def get_file_name_from_path_without_extension(path: Path) -> str:
    """
    Strip everything before the last path separator and remove the file extension.
    Works with both '\\' and '/' as separators.
    """
    # Get the last part after any slash or backslash
    filename = re.split(r"[\\/]", str(path))[-1]

    # Strip the extension
    name_without_ext, _ = os.path.splitext(filename)

    return name_without_ext


def normalize_without_empty_lines_and_dates(text: str) -> str:
    """
    Normalize text for matching by:
      - Stripping leading/trailing whitespace
      - Removing completely empty lines
      - Removing 4-digit years and year ranges (e.g., 1999-2024)
      - Collapsing multiple spaces
      - Collapsing multiple newlines
    """
    # Strip outer whitespace
    text = text.strip()

    # Remove empty lines
    lines = text.splitlines()
    non_empty_lines = [line for line in lines if line.strip() != ""]
    text = "\n".join(non_empty_lines)

    # Remove years and year ranges
    text = _YEAR_OR_RANGE_RE.sub("", text)

    # Collapse multiple spaces/tabs into a single space
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse multiple newlines into a single newline
    text = re.sub(r"\n+", "\n", text)

    # Final strip
    return text.strip()


def compare_values_of_two_dict(d1, d2):
    keys1 = set(d1.keys())
    keys2 = set(d2.keys())
    in_both = keys1 & keys2

    # Find keys where values differ
    keys_with_different_values = [
        k for k in in_both
        if d1[k] != d2[k]
    ]

    # Print values from both dicts for each differing key
    for key in keys_with_different_values:
        print(f"Key: {key}")
        print(f"  d1 value: {d1[key]!r}")
        print(f"  d2 value: {d2[key]!r}")
        print("-" * 40)


def placeholder_to_regex(text: str) -> str:
    """
    Converts placeholders in license_text to regex patterns.
    Recognizes placeholders like [yyyy], [year], [name of copyright owner], <year>, <name of author>, etc.
    """
    text = normalize_without_empty_lines_and_dates(text)
    # Replace [yyyy], [year], <year> with a year pattern (4 digits)
    text = re.sub(r"(\[yyyy\]|\[year\]|<year>)", r"\\d{4}", text)
    # Replace [name of copyright owner], <name of copyright owner>, <name of author>, etc. with any non-newline pattern
    text = re.sub(r"(\[name of copyright owner\]|<name of copyright owner>|<name of author>)", r".+?", text)
    # Remove the literal strings <!-- and -->
    text = re.sub(r'<!--|-->', '', text)
    # Replace generic bracket or angle placeholders: [.*?] or <.*?>
    text = re.sub(r"\[[^\[\]]+?\]", r".+?", text)
    text = re.sub(r"<[^<>]+?>", r".+?", text)
    # Escape special regex characters except for our replacements
    text = re.escape(text)
    # Unescape the regex patterns we inserted
    text = text.replace(r"\d{4}", r"\d{4}").replace(r"\.\+\?", r".+?")

    text = normalize_without_empty_lines_and_dates(text)

    return text


def remove_punctuation_from_text(text: str) -> str:
    """
    Normalize text by removing all ASCII punctuation characters.
    """
    # Create a translation table that maps each punctuation character to None
    translator = str.maketrans('', '', string.punctuation)
    # Remove punctuation and strip leading/trailing whitespace
    return text.translate(translator).strip()


def normalize_for_compare(value: Union[str, bytes, None]) -> str:
    """
    Normalize a string for comparison:
      - Handles None and bytes
      - Unicode normalizes (NFKC)
      - Strips accents/diacritics
      - Case-insensitive (casefold)
      - Collapses whitespace to single spaces
    Returns a normalized string.
    """
    if value is None:
        return ""

    # Decode bytes if needed
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")

    # Ensure it's a string
    value = str(value)

    # Normalize Unicode (compatibility decomposition + recomposition)
    value = unicodedata.normalize("NFKC", value)

    # Remove diacritics (accents)
    # e.g., "café" → "cafe"
    value = "".join(
        ch for ch in value
        if not unicodedata.category(ch).startswith("M")
    )

    # Case-insensitive
    value = value.casefold()

    # Collapse any whitespace (spaces, tabs, newlines) into a single space
    value = re.sub(r"\s+", " ", value)

    # Strip leading/trailing spaces
    return value.strip()



def remove_punctuation_keep_decimal_dots(text: str) -> str:
    """
    Remove all punctuation from `text`, except for '.' characters that are part
    of numbers or version-like tokens (i.e., a '.' with digits on both sides,
    such as in '1.0' or '1.0.0').

    Also handles LaTeX-style escaped sequences like '\&.' so that
    '2\\&.0\\&.' becomes '2.0'.
    """
    # Normalize '\&.' sequences to a plain dot
    # "v\\&. 2\\&.0\\&." -> "v. 2.0."
    text = re.sub(r'\\&\.', '.', text)

    punctuation = set(string.punctuation)
    result_chars = []
    n = len(text)

    for i, ch in enumerate(text):
        # Not punctuation? Always keep it.
        if ch not in punctuation:
            result_chars.append(ch)
            continue

        # Special handling for dots
        if ch == '.':
            prev_ch = text[i - 1] if i > 0 else ''
            next_ch = text[i + 1] if i + 1 < n else ''

            # Keep '.' only if it's between digits (e.g., 1.0, 1.0.0)
            if prev_ch.isdigit() and next_ch.isdigit():
                result_chars.append(ch)
            # else: skip this dot
            continue

        # Any other punctuation: remove it (skip)
        continue

    return ''.join(result_chars)


# def remove_punctuation_keep_decimal_dots(text: str) -> str:
#     """
#     Remove all punctuation from `text`, except for '.' characters that are part
#     of numbers or version-like tokens (i.e., a '.' with digits on both sides,
#     such as in '1.0' or '1.0.0').
#     """
#     punctuation = set(string.punctuation)
#     result_chars = []
#     n = len(text)
#
#     for i, ch in enumerate(text):
#         # Not punctuation? Always keep it.
#         if ch not in punctuation:
#             result_chars.append(ch)
#             continue
#
#         # Special handling for dots
#         if ch == '.':
#             prev_ch = text[i - 1] if i > 0 else ''
#             next_ch = text[i + 1] if i + 1 < n else ''
#
#             # Keep '.' only if it's between digits (e.g., 1.0, 1.0.0)
#             if prev_ch.isdigit() and next_ch.isdigit():
#                 result_chars.append(ch)
#             # else: skip this dot
#             continue
#
#         # Any other punctuation: remove it (skip)
#         # e.g. ',', '!', '?', '-', '$', etc.
#         continue
#
#     return ''.join(result_chars)


# def remove_punctuation_keep_decimal_dots(text: str) -> str:
#     """
#     Remove all punctuation from `text`, except for '.' characters that are part
#     of numbers or version-like tokens (i.e., a '.' with digits on both sides,
#     such as in '1.0' or '1.0.0').
#     """
#     # Placeholder that is NOT punctuation, so it survives the strip step
#     DECIMAL_DOT = "DECIMAL_DOT"
#
#     # 1) Protect decimal/version dots: 1.0, 1.0.0, 2.10, etc.
#     protected = re.sub(r'(?<=\d)\.(?=\d)', DECIMAL_DOT, text)
#
#     # 2) Remove all punctuation (including dots)
#     no_punct = ''.join(ch for ch in protected if ch not in string.punctuation)
#
#     # 3) Restore the protected decimal dots
#     result = no_punct.replace(DECIMAL_DOT, '.')
#
#     return result


def remove_punctuation_and_normalize_text(value: Union[str, bytes, None]) -> str:
    """
    Normalize a string for comparison:
      - Handles None and bytes
      - Unicode normalizes (NFKC)
      - Strips accents/diacritics
      - Case-insensitive (casefold)
      - Collapses whitespace to single spaces
    Returns a normalized string.
    """
    if value is None:
        return ""

    # Decode bytes if needed
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")

    # Ensure it's a string
    value = str(value)

    value = remove_punctuation_keep_decimal_dots(value)

    # Normalize Unicode (compatibility decomposition + recomposition)
    value = unicodedata.normalize("NFKC", value)

    # Remove diacritics (accents)
    # e.g., "café" → "cafe"
    value = "".join(
        ch for ch in value
        if not unicodedata.category(ch).startswith("M")
    )

    # Case-insensitive
    value = value.casefold()

    # Collapse any whitespace (spaces, tabs, newlines) into a single space
    value = re.sub(r"\s+", " ", value)

    # Strip leading/trailing spaces
    return value.strip()


def strip_bracketed_text(normalized: str) -> str:
    """
    Takes a normalized string and strips any text found within
    angle brackets <> or square brackets [] (including the brackets).
    Also re-collapses whitespace afterward.
    """
    if normalized is None:
        return ""

    text = str(normalized)

    # Remove <...> sections
    text = re.sub(r"<[^>]*>", "", text)
    # Remove [...] sections
    text = re.sub(r"\[[^\]]*\]", "", text)

    # Clean up extra whitespace that might be left behind
    text = re.sub(r"\s+", " ", text).strip()

    text = normalize_for_compare(text)

    return text


def load_file_contents_from_directory(license_dirs: List[Path]) -> Dict[Path, str]:
    licenses: Dict[Path, str] = {}

    for base_dir in license_dirs:
        if not os.path.isdir(base_dir):
            print(f"Warning: pattern directory does not exist or is not a directory: {base_dir}")
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
                    print(f"Could not read pattern file {license_path}: {e}")
                    continue

                license_text = raw_text.strip()  # ignore extra whitespace before/after

                if not license_text:
                    # Skip completely empty patterns
                    continue

                licenses[license_path] = license_text

    return licenses


def extract_version_from_name(filename: str) -> Optional[str]:
    """
    Extract the first number (like 2, 2.0, 2.1) from a file name.

    Examples:
        "ECL-2.0.txt"           -> "2.0"
        "ECL-2.1.txt"           -> "2.1"
        "ECL-2.txt"             -> "2"
        "LGPL-2.0-or-later.txt" -> "2.0"
    """
    # Ensure we're only working with the file name (no directories)
    name = Path(filename).name

    # Match a sequence of digits, optionally followed by a dot and more digits
    match = re.search(r'(\d+(?:\.\d+)?)', name)
    if match:
        return match.group(1)
    return None


def normalize_number_string(value: Optional[str]) -> Optional[str]:
    """
    Take a numeric string like "2", "2.1", "10", "-3", etc.

    - If it's an int (e.g. "2", "3", "10", "-3"), return it as "<int>.0"
      e.g. "2" -> "2.0", "-3" -> "-3.0"
    - Otherwise, return the original string unchanged
      e.g. "2.1" -> "2.1", "2.0" -> "2.0"
    - If value is None, return None
    """
    if value is None:
        return None

    s = value.strip()

    # Match an optional sign followed by digits only (no decimal point)
    if re.fullmatch(r'[+-]?\d+', s):
        return f"{int(s)}.0"
    else:
        return s