import logging
from pathlib import Path
from configuration import Configuration as Config

p = Path(__file__).resolve()

# Create a custom logger
print_utils_logger = logging.getLogger(__name__)
print_utils_logger.setLevel(logging.INFO)  # Set the minimum logging level

# Create handlers for file and console
file_handler_path = Path(Config.root_dir, "logs/print_utils.log")
file_handler = logging.FileHandler(file_handler_path, mode='w')
console_handler = logging.StreamHandler()

# Set the logging level for each handler
file_handler.setLevel(logging.INFO)
console_handler.setLevel(logging.INFO)

# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
print_utils_logger.addHandler(file_handler)
print_utils_logger.addHandler(console_handler)