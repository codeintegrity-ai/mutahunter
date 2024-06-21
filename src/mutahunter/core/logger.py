import logging
import os
import warnings

# Suppress specific FutureWarnings from tree_sitter
warnings.filterwarnings("ignore", category=FutureWarning, module="tree_sitter")


def setup_logger(name):
    os.makedirs("logs/_latest/mutants", exist_ok=True)
    # Create a custom format for your logs
    log_format = "%(asctime)s %(levelname)s: %(message)s"

    # Create a log handler for file output
    file_handler = logging.FileHandler(
        filename=os.path.join("logs", "_latest", "debug.log"),
        mode="w",
        encoding="utf-8",
    )
    stream_handler = logging.StreamHandler()

    # Apply the custom format to the handler
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # Create a logger and add the handler
    logger = logging.getLogger(name)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.setLevel(logging.INFO)

    return logger


logger = setup_logger("mutahunter")
