import json
import zlib
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Union

from configuration import Configuration as Config



def compress_to_b64(data: Union[str, bytes]) -> str:
    """Compress bytes or text and encode as base64 string."""
    if not data:
        return ""

    if isinstance(data, str):
        data = data.encode("utf-8")  # convert text -> bytes

    compressed = zlib.compress(data)
    return base64.b64encode(compressed).decode("ascii")


def decompress_from_b64(
    data_b64: str,
    *,
    as_text: bool,
    encoding: str = "utf-8",
) -> Union[str, bytes]:
    """Decode base64 string and decompress, returning str or bytes."""
    if not data_b64:
        return "" if as_text else b""

    compressed = base64.b64decode(data_b64.encode("ascii"))
    raw = zlib.decompress(compressed)

    if as_text:
        return raw.decode(encoding)
    return raw


@dataclass
class FileData:
    def __init__(self, file_path, file_content):
        self._file_path = file_path
        self._file_content = file_content
        self._file_extension = None
        self._file_header = None
        self._keyword_matches = None
        self._license_matches = []
        self._license_names = []
        self._is_released = False
        self._file_hash = None
        self._license_match_strength = None
        self._keyword_combination_matches = None
        self._fuzzy_license_matches = []
        self.fuzzy_license_match = None
        # self._header_data = header_data if header_data is not None else []
        # self._file_entry = file_entry if file_entry is not None else []
        # self._file_search_data = file_search_data if file_search_data is not None else []
        # self._file_assessment = file_assessment
        # self._is_archive = is_archive
        # self._could_read = could_read
        # self._has_license = has_license
        # self._is_license = is_license
        # self._license_data = license_data if license_data is not None else []

    @property
    def file_path(self):
        return self._file_path

    @file_path.setter
    def file_path(self, file_path):
        self._file_path = file_path

    @property
    def file_content(self):
        return self._file_content

    @file_content.setter
    def file_content(self, file_content):
        self._file_content = file_content

    @property
    def file_extension(self):
        return self._file_extension

    @file_extension.setter
    def file_extension(self, file_extension):
        self._file_extension = file_extension

    @property
    def file_header(self):
        return self._file_header

    @file_header.setter
    def file_header(self, file_header):
        self._file_header = file_header

    @property
    def keyword_matches(self):
        return self._keyword_matches

    @keyword_matches.setter
    def keyword_matches(self, keyword_matches):
        self._keyword_matches = keyword_matches

    @property
    def license_matches(self):
        return self._license_matches

    @license_matches.setter
    def license_matches(self, license_matches):
        self._license_matches = license_matches

    @property
    def license_names(self):
        return self._license_names

    @license_names.setter
    def license_names(self, license_names):
        self._license_names = license_names

    @property
    def is_released(self):
        return self._is_released

    @is_released.setter
    def is_released(self, is_released):
        self._is_released = is_released

    @property
    def file_hash(self):
        return self._file_hash

    @file_hash.setter
    def file_hash(self, file_hash):
        self._file_hash = file_hash

    @property
    def license_match_strength(self):
        return self._license_match_strength

    @license_match_strength.setter
    def license_match_strength(self, license_match_strength):
        self._license_match_strength = license_match_strength

    @property
    def keyword_combination_matches(self):
        return self._keyword_combination_matches

    @keyword_combination_matches.setter
    def keyword_combination_matches(self, keyword_combination_matches):
        self._keyword_combination_matches = keyword_combination_matches

    @property
    def fuzzy_license_matches(self):
        return self._fuzzy_license_matches

    @fuzzy_license_matches.setter
    def fuzzy_license_matches(self, fuzzy_license_matches):
        self._fuzzy_license_matches = fuzzy_license_matches

    @property
    def fuzzy_license_match(self):
        return self._fuzzy_license_match

    @fuzzy_license_match.setter
    def fuzzy_license_match(self, fuzzy_license_match):
        self._fuzzy_license_match = fuzzy_license_match
    #
    # @property
    # def header_data(self):
    #     return self._header_data
    #
    # @header_data.setter
    # def header_data(self, header_data):
    #     self._header_data = header_data
    #
    # @property
    # def file_entry(self):
    #     return self._file_entry
    #
    # @file_entry.setter
    # def file_entry(self, file_entry):
    #     self._file_entry = file_entry
    #
    # @property
    # def file_search_data(self):
    #     return self._file_search_data
    #
    # @file_search_data.setter
    # def file_search_data(self, file_search_data):
    #     self._file_search_data = file_search_data
    #
    # @property
    # def file_assessment(self):
    #     return self._file_assessment
    #
    # @file_assessment.setter
    # def file_assessment(self, file_assessment):
    #     self._file_assessment = file_assessment
    #
    # @property
    # def is_archive(self):
    #     return self._is_archive
    #
    # @is_archive.setter
    # def is_archive(self, is_archive):
    #     self._is_archive = is_archive
    #
    # @property
    # def could_read(self):
    #     return self._could_read
    #
    # @could_read.setter
    # def could_read(self, could_read):
    #     self._could_read = could_read
    #
    # @property
    # def has_license(self):
    #     return self._has_license
    #
    # @has_license.setter
    # def has_license(self, has_license):
    #     self._has_license = has_license
    #
    # @property
    # def is_license(self):
    #     return self._is_license
    #
    # @is_license.setter
    # def is_license(self, is_license):
    #     self._is_license = is_license
    #
    # @property
    # def license_data(self):
    #     return self._license_data
    #
    # @license_data.setter
    # def license_data(self, license_data):
    #     self._license_data = license_data

    def to_persisted_dict(self) -> dict:
        is_text = isinstance(self.file_content, str)
        # Choose what to save.
        return {
            "file_path": str(Path(self.file_path).relative_to(Config.assessments_dir)),
            "file_hash": self.file_hash,
            "license": self.license_names,
            "file_content_b64": compress_to_b64(self.file_content),
            "file_content_is_text": is_text,
            # add "file_extension": self.file_extension if you want it too
        }

    @classmethod
    def from_persisted_dict(cls, data: dict) -> "FileData":
        """
        Recreate FileData from a JSON dict produced by to_persisted_dict().
        """
        file_path = Path(data["file_path"])
        file_hash = data.get("file_hash")
        license_name = data.get("license")
        is_text = data.get("file_content_is_text", False)

        file_content = decompress_from_b64(
            data.get("file_content_b64", ""),
            as_text=is_text,
        )

        obj = cls(
            file_path=file_path,
            file_content=file_content,
        )
        obj.file_hash = file_hash
        obj.license_names = license_name
        return obj


    # @classmethod
    # def from_persisted_dict(
    #     cls,
    #     data: dict,
    #     *,
    #     default_content: bytes = b"",
    #     default_extension: str = "",
    # ) -> "FileData":
    #     obj = cls(
    #         file_path=Path(data["file_path"]),
    #         file_content=default_content,
    #         file_extension=data.get("file_extension", default_extension),
    #     )
    #     obj.file_header = data.get("file_header")
    #     return obj


class FileDataManager:
    def __init__(self):
        self.file_data_dict: Dict[Path, FileData] = {}

    def add_file_data(self, file_info: FileData):
        """Adds a File instance to the manager."""
        self.file_data_dict[file_info.file_path] = file_info

    def get_file_data(self, file_path: Path) -> Optional[FileData]:
        """Retrieves a FileData instance by file path."""
        return self.file_data_dict.get(file_path)

    def get_all_file_data(self) -> List[FileData]:
        """Returns a list of all FileData instances."""
        return list(self.file_data_dict.values())

    # ---------- JSON persistence ----------

    def save_to_json(self, path: Path = Path(Config.data_dir).resolve()) -> None:
        path = Path(path, Config.assessment_name).resolve()
        path = Path(path).with_suffix(".json")
        data = [fd.to_persisted_dict() for fd in self.get_all_file_data()]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


    @classmethod
    def load_from_json(cls, path: Path = Path(Config.data_dir, Config.assessment_name).resolve()) -> "FileDataManager":
        manager = cls()

        path = Path(path).with_suffix(".json")
        if not path.exists():
            return manager

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            fd = FileData.from_persisted_dict(item)
            manager.add_file_data(fd)

        return manager

    # @classmethod
    # def load_from_json(
    #     cls,
    #     path: Path = Path(Config.data_dir, Config.assessment_name).resolve(),
    #     *,
    #     default_content: bytes = b"",
    #     default_extension: str = "",
    # ) -> "FileDataManager":
    #     manager = cls()
    #
    #     path = Path(path).with_suffix(".json")
    #     if not path.exists():
    #         return manager
    #
    #     with open(path, "r", encoding="utf-8") as f:
    #         data = json.load(f)
    #
    #     for item in data:
    #         fd = FileData.from_persisted_dict(
    #             item,
    #             default_content=default_content,
    #             default_extension=default_extension,
    #         )
    #         manager.add_file_data(fd)
    #
    #     return manager
