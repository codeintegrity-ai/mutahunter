import os
import shutil

from mutahunter.core.logger import logger


class FileUtils:
    @staticmethod
    def read_file(path: str) -> str:
        try:
            with open(path, "r") as file:
                return file.read()
        except FileNotFoundError:
            logger.info(f"File not found: {path}")
        except Exception as e:
            logger.info(f"Error reading file {path}: {e}")
            raise

    @staticmethod
    def number_lines(code: str) -> str:
        return "\n".join(f"{i + 1} {line}" for i, line in enumerate(code.splitlines()))

    @staticmethod
    def backup_code(file_path: str) -> None:
        backup_path = f"{file_path}.bak"
        try:
            shutil.copyfile(file_path, backup_path)
        except Exception as e:
            logger.info(f"Failed to create backup file for {file_path}: {e}")
            raise

    @staticmethod
    def revert(file_path: str) -> None:
        backup_path = f"{file_path}.bak"
        try:
            if os.path.exists(backup_path):
                shutil.copyfile(backup_path, file_path)
            else:
                logger.info(f"No backup file found for {file_path}")
                raise FileNotFoundError(f"No backup file found for {file_path}")
        except Exception as e:
            logger.info(f"Failed to revert file {file_path}: {e}")
            raise
