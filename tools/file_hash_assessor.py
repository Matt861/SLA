#!/usr/bin/env python3
import hashlib
import os
from pathlib import Path
from configuration import Configuration as Config
from models.FileData import FileData

CHUNK_SIZE = 1024 * 1024  # 1 MB


def hash_file(file_path: Path, algo: str = Config.file_hash_algorithm) -> str:
    """
    Compute the hash of a single file using the given algorithm.
    """
    h = hashlib.new(algo)
    with file_path.open("rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def hash_folder(folder_path: Path, algo: str = Config.file_hash_algorithm) -> str:
    """
    Compute a deterministic hash of all files in a folder (recursively).

    It walks the directory tree, sorts paths, and feeds both the
    relative file path and file contents into the hash.
    """
    h = hashlib.new(algo)
    folder_path = folder_path.resolve()

    for root, dirs, files in os.walk(folder_path):
        # Ensure deterministic order
        dirs.sort()
        files.sort()

        for name in files:
            file_path = Path(root) / name
            rel_path = file_path.relative_to(folder_path).as_posix()

            # Include the relative path in the hash so identical contents
            # in different locations produce different folder hashes
            h.update(rel_path.encode("utf-8"))
            h.update(b"\0")

            # Include file content
            with file_path.open("rb") as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    h.update(chunk)

    return h.hexdigest()


def compute_hash(file_data: FileData, algo: str = "sha256") -> str:
    path = file_data.file_path
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    if path.is_file():
        file_data.file_hash = hash_file(path, algo)
    elif path.is_dir():
        return hash_folder(path, algo)
    else:
        raise ValueError(f"Path is neither file nor directory: {path}")


def compute_file_hashes_for_assessment():

    for file_data in Config.file_data_manager.get_all_file_data():
        try:
            digest = compute_hash(file_data, Config.file_hash_algorithm)
            # print(f"Algorithm: {algorithm}")
            # print(f"Path:      {file_data.file_path}")
            # print(f"Hash:      {digest}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    compute_file_hashes_for_assessment()
