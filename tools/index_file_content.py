import re
from pathlib import Path
from typing import List, Dict, Tuple, Any, Union, Optional
from dataclasses import dataclass
import utils


WORD_RE = re.compile(r"\S+")


@dataclass
class FileIndex:
    source_obj: Any  # your model instance for stringA
    text: str
    tokens: List[Dict]
    trigram_positions: Dict[Tuple[str, str, str], List[int]]


@dataclass
class PatternIndex:
    source_path: Path  # the key from Dict[Path, str]
    text: str          # the pattern string (stringB)
    tokens: List[str]
    anchor_positions: Dict[Tuple[str, str, str], List[int]]
    anchor_keys: set


@dataclass
class MatchResult:
    matched_substring: str
    match_percent: float
    start_index: int
    end_index: int
    expected_versions: Optional[List[str]] = None  # version found in the pattern (license text)
    found_versions: Optional[List[str]] = None     # version found in the file text
    license_name: Optional[str] = None


def _ensure_text(value: Union[str, bytes]) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return value


def _tokenize_with_spans(text: str):
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


def build_file_indexes(
    model_objects,          # e.g. List[FileData]
    anchor_size: int = 3,
) -> List[FileIndex]:
    file_indexes: List[FileIndex] = []

    for obj in model_objects:
        # Adjust property name as needed (e.g. obj.file_content)
        text = _ensure_text(obj.file_content)
        text = utils.remove_punctuation_and_normalize_text(text)
        #text = utils.placeholder_to_regex(text)
        tokens = _tokenize_with_spans(text)

        trigram_positions: Dict[Tuple[str, str, str], List[int]] = {}
        for i in range(len(tokens) - anchor_size + 1):
            anchor = tuple(tokens[i + k]["norm"] for k in range(anchor_size))
            trigram_positions.setdefault(anchor, []).append(i)

        file_indexes.append(
            FileIndex(
                source_obj=obj,
                text=text,
                tokens=tokens,
                trigram_positions=trigram_positions,
            )
        )

    return file_indexes


def build_pattern_indexes_from_dict(
    patterns: Dict[Path, Union[str, bytes]],
    anchor_size: int = 3,
) -> List[PatternIndex]:
    pattern_indexes: List[PatternIndex] = []

    for path, content in patterns.items():
        text = _ensure_text(content)
        raw_tokens = [m.group(0) for m in WORD_RE.finditer(text)]
        tokens = [w.lower() for w in raw_tokens]

        if len(tokens) < anchor_size:
            pattern_indexes.append(
                PatternIndex(
                    source_path=path,
                    text=text,
                    tokens=tokens,
                    anchor_positions={},
                    anchor_keys=set(),
                )
            )
            continue

        anchor_positions: Dict[Tuple[str, str, str], List[int]] = {}
        for j in range(len(tokens) - anchor_size + 1):
            anchor = tuple(tokens[j + k] for k in range(anchor_size))
            anchor_positions.setdefault(anchor, []).append(j)

        pattern_indexes.append(
            PatternIndex(
                source_path=path,
                text=text,
                tokens=tokens,
                anchor_positions=anchor_positions,
                anchor_keys=set(anchor_positions.keys()),
            )
        )

    return pattern_indexes
