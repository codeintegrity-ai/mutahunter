import subprocess
from typing import Any, Dict, List, Optional

from mutahunter.core.logger import logger


class GitCommandError(Exception):
    """Custom exception for Git command errors."""

    pass


class GitHandler:
    @staticmethod
    def get_modified_files(covered_files) -> List[str]:
        try:
            modified_files = GitHandler.run_git_command(
                ["git", "diff", "--name-only", "HEAD"]
            )
            return [
                file_path for file_path in modified_files if file_path in covered_files
            ]
        except GitCommandError as e:
            logger.error(f"Error identifying modified files: {e}")
            return []

    @staticmethod
    def get_modified_lines(self, file_path: str) -> List[int]:
        try:
            diff_output = GitHandler.run_git_command(
                ["git", "diff", "-U0", "HEAD", file_path]
            )
            return self._parse_diff_output(diff_output)
        except GitCommandError as e:
            logger.error(f"Error identifying modified lines in {file_path}: {e}")
            return []

    @staticmethod
    def run_git_command(command: List[str]) -> List[str]:
        try:
            output = subprocess.check_output(command, stderr=subprocess.PIPE)
            return output.decode("utf-8").splitlines()
        except subprocess.CalledProcessError as e:
            raise GitCommandError(f"Git command failed: {e.stderr.decode('utf-8')}")
