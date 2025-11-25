from pathlib import Path
from configuration import Configuration as Config


def is_ignored_dir(src_dir: Path) -> bool:
    src_dir_str = str(src_dir)
    for ignore_dir in Config.ignore_dirs:
        if ignore_dir in str(src_dir_str):
            return True
    return False


def set_file_release_status():
    for file_data in Config.file_data_manager.get_all_file_data():
        if file_data and file_data.file_path:
            if is_ignored_dir(file_data.file_path):
                file_data.is_released = False
            else:
                file_data.is_released = True


if __name__ == "__main__":
    set_file_release_status()