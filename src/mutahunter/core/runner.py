import os
import shutil
import subprocess


class TestRunner:
    def __init__(self):
        pass

    def run_test(self, params: dict) -> subprocess.CompletedProcess:
        module_path = params["module_path"]
        replacement_module_path = params["replacement_module_path"]
        cmd = params["test_command"]
        backup_path = module_path + ".bak"
        try:
            self.replace_file(module_path, replacement_module_path, backup_path)
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
