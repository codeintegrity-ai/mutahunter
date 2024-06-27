import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from mutahunter.core.runner import TestRunner


@pytest.fixture
def test_runner():
    return TestRunner()


def test_run_test_success(test_runner):
    params = {
        "module_path": "original_module.py",
        "replacement_module_path": "replacement_module.py",
        "test_command": "echo 'test'",
    }

    with (
        patch("subprocess.run") as mock_run,
        patch.object(test_runner, "create_symlink") as mock_create_symlink,
        patch.object(test_runner, "revert_symlink") as mock_revert_symlink,
    ):
        mock_run.return_value = subprocess.CompletedProcess(
            params["test_command"], 0, stdout="test", stderr=""
        )
        result = test_runner.run_test(params)

        mock_create_symlink.assert_called_once_with(
            params["module_path"], params["replacement_module_path"]
        )
        mock_run.assert_called_once_with(
            params["test_command"],
            text=True,
            capture_output=True,
            shell=True,
            cwd=os.getcwd(),
            timeout=30,
        )
        mock_revert_symlink.assert_called_once_with(params["module_path"])

        assert result.returncode == 0
        assert result.stdout == "test"
        assert result.stderr == ""


def test_revert_symlink(test_runner):
    original = "original_module.py"
    backup = original + ".bak"

    with (
        patch("os.path.islink", return_value=True) as mock_islink,
        patch("os.unlink") as mock_unlink,
        patch("os.path.exists", return_value=True) as mock_exists,
        patch("os.rename") as mock_rename,
    ):
        test_runner.revert_symlink(original)

        mock_islink.assert_called_once_with(original)
        mock_unlink.assert_called_once_with(original)
        mock_exists.assert_called_once_with(backup)
        mock_rename.assert_called_once_with(backup, original)


def test_create_symlink(test_runner):
    original = "original_module.py"
    replacement = "replacement_module.py"
    backup = original + ".bak"

    with (
        patch("os.path.exists", return_value=False) as mock_exists,
        patch("os.rename") as mock_rename,
        patch("os.symlink") as mock_symlink,
    ):
        test_runner.create_symlink(original, replacement)

        mock_exists.assert_called_once_with(backup)
        mock_rename.assert_called_once_with(original, backup)
        mock_symlink.assert_called_once_with(replacement, original)


def test_run_test_timeout(test_runner):
    params = {
        "module_path": "original_module.py",
        "replacement_module_path": "replacement_module.py",
        "test_command": "echo 'test'",
    }

    with (
        patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(
                cmd=params["test_command"], timeout=30
            ),
        ) as mock_run,
        patch.object(test_runner, "create_symlink") as mock_create_symlink,
        patch.object(test_runner, "revert_symlink") as mock_revert_symlink,
    ):
        result = test_runner.run_test(params)

        mock_create_symlink.assert_called_once_with(
            params["module_path"], params["replacement_module_path"]
        )
        mock_run.assert_called_once_with(
            params["test_command"],
            text=True,
            capture_output=True,
            shell=True,
            cwd=os.getcwd(),
            timeout=30,
        )
        mock_revert_symlink.assert_called_once_with(params["module_path"])

        assert result.returncode == 1
        assert result.stdout == ""
        assert result.stderr == "TimeoutExpired"
