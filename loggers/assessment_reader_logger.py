import logging
from pathlib import Path
from configuration import Configuration as Config

p = Path(__file__).resolve()

# Create a custom logger
assessment_reader_logger = logging.getLogger(__name__)
assessment_reader_logger.setLevel(logging.DEBUG)  # Set the minimum logging level

# Create handlers for file and console
file_handler_path = Path(Config.root_dir, "logs/assessment_reader.log")
file_handler = logging.FileHandler(file_handler_path, mode='w')
console_handler = logging.StreamHandler()

# Set the logging level for each handler
file_handler.setLevel(logging.INFO)
console_handler.setLevel(logging.DEBUG)

# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
assessment_reader_logger.addHandler(file_handler)
assessment_reader_logger.addHandler(console_handler)