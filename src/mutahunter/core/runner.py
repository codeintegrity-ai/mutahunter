import os
import shutil
import subprocess
from shlex import split


class TestRunner:
    def __init__(self, test_command):
        self.test_command = test_command

    def dry_run(self) -> None:
        """
        Performs a dry run of the tests to ensure they pass before mutation testing.

        Raises:
            Exception: If any tests fail during the dry run.
        """
        result = self._run_test_command(self.test_command)
        if result.returncode != 0:
            raise Exception(
                "Tests failed. Please ensure all tests pass before running mutation testing."
            )

    def _run_test_command(self, test_command: str) -> subprocess.CompletedProcess:
        """
        Runs a given test command in a subprocess.

        Args:
            test_command (str): The command to run.

        Returns:
            subprocess.CompletedProcess: The result of the command execution.
        """
        return subprocess.run(split(test_command), cwd=os.getcwd())

    def run_test(self, params: dict) -> subprocess.CompletedProcess:
        module_path = params["module_path"]
        replacement_module_path = params["replacement_module_path"]
        test_command = params["test_command"]
        backup_path = f"{module_path}.bak"
        try:
            self.replace_file(module_path, replacement_module_path, backup_path)
            result = subprocess.run(
                split(test_command),
                text=True,
                capture_output=True,
                cwd=os.getcwd(),
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            # Mutant Killed
            result = subprocess.CompletedProcess(
                test_command, 2, stdout="", stderr="TimeoutExpired"
            )
        finally:
            self.revert_file(module_path, backup_path)
        return result

    def replace_file(self, original, replacement, backup):
        """Backup original file and replace it with the replacement file."""
        if not os.path.exists(backup):
            shutil.copy2(original, backup)
        shutil.copy2(replacement, original)

    def revert_file(self, original, backup):
        """Revert the file to the original using the backup."""
        if os.path.exists(backup):
            shutil.copy2(backup, original)
            os.remove(backup)
