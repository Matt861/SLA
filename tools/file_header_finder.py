import csv
import re
from pathlib import Path
from typing import Optional, List
from configuration import Configuration as Config
from models.FileData import FileData
from input import header_types
from loggers import file_header_finder_logger as Logger


def detect_c_style_file_header(file_data: FileData) -> Optional[str]:
    """
    Return the top-of-file header comment for a C-style language source file,
    if present.

    C-style header = comment at the very top (after:
      - optional BOM,
      - optional blank lines,
      - optional shebang line),
    where the comment is either:
      - a block comment starting with /* or /**, or
      - one or more consecutive // line comments.

    :param file_data:
    :return: Header comment text (including comment markers) if present, else None.
    """
    lines = file_data.file_content.splitlines()
    n = len(lines)
    i = 0

    # Handle BOM on very first line if present
    if n > 0 and lines[0].startswith("\ufeff"):
        lines[0] = lines[0].lstrip("\ufeff")

    # 1) Skip leading blank lines
    while i < n and lines[i].strip() == "":
        i += 1

    if i >= n:
        return None

    # 2) Skip shebang (e.g. "#!/usr/bin/env node")
    if lines[i].lstrip().startswith("#!"):
        i += 1
        # Skip any blank lines after shebang
        while i < n and lines[i].strip() == "":
            i += 1
        if i >= n:
            return None

    if i >= n:
        return None

    first = lines[i].lstrip()

    # 3) Block comment header: /* ... */ or /** ... */
    if first.startswith("/*"):
        header_lines = []
        while i < n:
            header_lines.append(lines[i])
            if "*/" in lines[i]:
                break
            i += 1
        # Even if "*/" is never found, treat gathered lines as header
        file_data.file_header = "\n".join(header_lines)
        return "\n".join(header_lines)

    # 4) Line comment header: one or more // lines at the top
    if first.startswith("//"):
        header_lines = []
        while i < n and lines[i].lstrip().startswith("//"):
            header_lines.append(lines[i])
            i += 1
        if header_lines:
            file_data.file_header = "\n".join(header_lines)
            return "\n".join(header_lines)

    # 5) Anything else at the top = no header
    return None


def detect_xml_style_file_header(file_data: FileData) -> Optional[str]:
    """
    Return the top-of-file header comment for an XML or HTML file, if present.

    A header is defined as a <!-- ... --> comment block that appears
    before any non-declaration, non-DOCTYPE element, ignoring:
      - leading blank lines
      - BOM
      - XML declaration (<?xml ...?>)
      - DOCTYPE (<!DOCTYPE ...>)

    :param file_data:
    :return: The header comment (including <!-- and -->) if present, otherwise None.
    """
    lines = file_data.file_content.splitlines()
    n = len(lines)
    i = 0

    while i < n:
        line = lines[i]
        stripped = line.lstrip()

        # Strip BOM if present
        if stripped.startswith("\ufeff"):
            stripped = stripped.lstrip("\ufeff")

        # Skip blank lines
        if not stripped:
            i += 1
            continue

        # Skip XML declaration
        if stripped.startswith("<?xml"):
            i += 1
            continue

        # Skip DOCTYPE
        if stripped.lower().startswith("<!doctype"):
            i += 1
            continue

        # Header comment at/near the top
        if stripped.startswith("<!--"):
            header_lines = [lines[i]]

            # If the closing --> is on the same line, we’re done
            if "-->" in stripped:
                file_data.file_header = "\n".join(header_lines)
                return "\n".join(header_lines)

            # Otherwise, gather subsequent lines until we find -->
            i += 1
            while i < n:
                header_lines.append(lines[i])
                if "-->" in lines[i]:
                    break
                i += 1

            file_data.file_header = "\n".join(header_lines)
            return "\n".join(header_lines)

        # If we reach any other tag/content before a comment, no header
        if stripped.startswith("<"):
            return None

        # Any non-tag, non-comment content before a header => no header
        return None

    # Reached end of file with no header at top
    return None


def detect_python_style_file_header(file_data: FileData) -> Optional[str]:
    """
    Return the top-of-file header for a Python-style file, if present.

    Python-style header:
      - Optional UTF-8 BOM on first line.
      - Optional shebang line: #!...
      - Optional blank lines.
      - Then one or more consecutive lines starting with '#' (after stripping leading whitespace).

    The block of '#' lines is returned as the header.

    :param file_data:
    :return: Header text (including '#' markers) if present, otherwise None.
    """
    lines = file_data.file_content.splitlines()
    n = len(lines)
    i = 0

    if n == 0:
        return None

    # Strip BOM from first line if present
    if lines[0].startswith("\ufeff"):
        lines[0] = lines[0].lstrip("\ufeff")

    # 1) Optional shebang line (e.g., #!/usr/bin/env python)
    if lines[i].lstrip().startswith("#!"):
        i += 1

    # 2) Skip blank lines after shebang
    while i < n and lines[i].strip() == "":
        i += 1

    if i >= n:
        return None

    # 3) Collect contiguous lines starting with '#'
    stripped = lines[i].lstrip()
    if not stripped.startswith("#"):
        # First non-blank, non-shebang line is not a comment -> no header
        return None

    header_lines = []
    while i < n and lines[i].lstrip().startswith("#"):
        header_lines.append(lines[i])
        i += 1

    if not header_lines:
        return None

    file_data.file_header = "\n".join(header_lines)
    return "\n".join(header_lines)


def detect_csv_style_file_header(file_data: FileData) -> Optional[str]:
    """
    Detect and return the header line for a CSV-style text file, if present.

    Heuristic:
      - Look at up to the first 10 non-empty lines as a sample.
      - Use csv.Sniffer to guess the dialect and whether there is a header.
      - If csv.Sniffer thinks there *is* a header, return the first non-empty line
        as it appears in the original content.

    :param file_data:
    :return: Header line text if a header is likely present, otherwise None.
    """
    # Split into lines and remove leading BOM from very first line if present
    lines = file_data.file_content.splitlines()
    if not lines:
        return None

    if lines[0].startswith("\ufeff"):
        lines[0] = lines[0].lstrip("\ufeff")

    # Keep only non-empty lines for detection purposes
    non_empty_lines = [ln for ln in lines if ln.strip() != ""]
    if not non_empty_lines:
        return None

    # Sample up to first 10 non-empty lines for the sniffer
    sample = "\n".join(non_empty_lines[:10])

    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(sample)
    except csv.Error:
        # Fallback: assume standard CSV
        dialect = csv.excel

    try:
        has_header = sniffer.has_header(sample)
    except csv.Error:
        # If the sniffer can't decide, assume no header
        has_header = False

    if not has_header:
        return None

    # If we reach here, Sniffer thinks there is a header.
    # Return the first non-empty line exactly as it appears in the file.
    file_data.file_header = non_empty_lines[0]
    return non_empty_lines[0]


def detect_txt_style_file_header(file_data: FileData, min_header_lines: int = 2) -> Optional[str]:
    """
    Return the top-of-file header for a txt-style file, if present.

    Heuristic:
      - Strip optional BOM from first line.
      - Skip leading blank lines.
      - Collect the first contiguous block of *non-blank* lines.
      - If that block has at least `min_header_lines` lines, treat it as the header.

    :param file_data:
    :param min_header_lines: Minimum number of lines required to consider it a header.
    :return: Header text (joined with '\n') if present, otherwise None.
    """
    lines: List[str] = file_data.file_content.splitlines()
    if not lines:
        return None

    # Strip BOM from first line if present
    if lines[0].startswith("\ufeff"):
        lines[0] = lines[0].lstrip("\ufeff")

    n = len(lines)
    i = 0

    # 1) Skip leading blank lines
    while i < n and lines[i].strip() == "":
        i += 1

    if i >= n:
        return None

    # 2) Collect contiguous non-blank lines as candidate header block
    header_lines: List[str] = []
    while i < n and lines[i].strip() != "":
        header_lines.append(lines[i])
        i += 1

    # 3) Decide if this block counts as a header
    if len(header_lines) >= min_header_lines:
        file_data.file_header = "\n".join(header_lines)
        return "\n".join(header_lines)

    return None


def detect_sh_style_file_header(file_data: FileData) -> Optional[str]:
    """
    Return the top-of-file header for a sh-style script, if present.

    sh-style header:
      - Optional UTF-8 BOM on first line.
      - Optional shebang line: #!...
      - Optional blank lines.
      - Then one or more consecutive lines starting with '#' (after stripping leading whitespace).

    The block of '#' lines is returned as the header.

    :param file_data:
    :return: Header text (including '#' markers) if present, otherwise None.
    """
    lines: List[str] = file_data.file_content.splitlines()
    if not lines:
        return None

    # Strip BOM from first line if present
    if lines[0].startswith("\ufeff"):
        lines[0] = lines[0].lstrip("\ufeff")

    n = len(lines)
    i = 0

    # 1) Optional shebang line (e.g., #!/usr/bin/env bash)
    if i < n and lines[i].lstrip().startswith("#!"):
        i += 1

    # 2) Skip blank lines after shebang
    while i < n and lines[i].strip() == "":
        i += 1

    if i >= n:
        return None

    # 3) Collect contiguous lines starting with '#'
    if not lines[i].lstrip().startswith("#"):
        # First non-blank, non-shebang line is not a comment -> no header
        return None

    header_lines: List[str] = []
    while i < n and lines[i].lstrip().startswith("#"):
        header_lines.append(lines[i])
        i += 1

    if not header_lines:
        return None

    file_data.file_header = "\n".join(header_lines)
    return "\n".join(header_lines)


def search_all_assessment_files_for_headers():
    for file_data in Config.file_data_manager.get_all_file_data():
        file_path = Path(file_data.file_path)
        if file_data and file_data.file_content:
            file_extension = file_data.file_extension.lower()
            if file_extension in header_types.C_STYLE_HEADER_EXTENSIONS:
                detect_c_style_file_header(file_data)
            elif file_extension in header_types.XML_STYLE_HEADER_EXTENSIONS:
                detect_xml_style_file_header(file_data)
            elif file_extension in header_types.PYTHON_STYLE_HEADER_EXTENSIONS:
                detect_python_style_file_header(file_data)
            elif file_path.name in header_types.PYTHON_STYLE_HEADER_BASENAMES:
                detect_python_style_file_header(file_data)
            elif file_extension in header_types.CSV_STYLE_HEADER_EXTENSIONS:
                detect_csv_style_file_header(file_data)
            elif file_extension in header_types.TXT_STYLE_HEADER_EXTENSIONS:
                detect_txt_style_file_header(file_data)
            elif file_path.name in header_types.TXT_STYLE_HEADER_BASENAMES:
                detect_txt_style_file_header(file_data)
            elif file_extension in header_types.SH_STYLE_HEADER_EXTENSIONS:
                detect_sh_style_file_header(file_data)
            elif file_path.name in header_types.SH_STYLE_HEADER_BASENAMES:
                detect_sh_style_file_header(file_data)


if __name__ == "__main__":
    search_all_assessment_files_for_headers()