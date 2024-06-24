import os
import subprocess


class TestRunner:
    def __init__(self):
        pass

    def run_test(self, params: dict) -> subprocess.CompletedProcess:
        module_path = params["module_path"]
        replacement_module_path = params["replacement_module_path"]
        cmd = params["test_command"]
        try:
            self.create_symlink(module_path, replacement_module_path)
            result = subprocess.run(
                cmd,
                text=True,
                capture_output=True,
                shell=True,
                cwd=os.getcwd(),
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            # Mutant Killed
            result = subprocess.CompletedProcess(
                cmd, 1, stdout="", stderr="TimeoutExpired"
            )
        finally:
            self.revert_symlink(module_path)
        return result

    def create_symlink(self, original, replacement):
        """Backup original file and create a symlink to the replacement file."""
        backup = original + ".bak"
        if not os.path.exists(backup):
            os.rename(original, backup)
        os.symlink(replacement, original)

    def revert_symlink(self, original):
        """Revert the symlink to the original file using the backup."""
        backup = original + ".bak"
        if os.path.islink(original):
            os.unlink(original)
        if os.path.exists(backup):
            os.rename(backup, original)
