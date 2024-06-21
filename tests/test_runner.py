import pytest
from unittest.mock import patch, MagicMock
import subprocess
import os
from mutahunter.core.runner import TestRunner


@pytest.fixture
def runner():
    return TestRunner()


@pytest.fixture
def params():
    return {
        "module_path": "path/to/original_module.py",
        "replacement_module_path": "path/to/replacement_module.py",
        "test_command": "pytest tests/",
    }


@patch("mutahunter.core.runner.os.path.exists")
@patch("mutahunter.core.runner.os.rename")
@patch("mutahunter.core.runner.os.symlink")
@patch("mutahunter.core.runner.os.remove")
@patch("mutahunter.core.runner.subprocess.run")
def test_run_test(
    mock_subprocess_run,
    mock_os_remove,
    mock_os_symlink,
    mock_os_rename,
    mock_os_path_exists,
    runner,
    params,
):
    mock_os_path_exists.side_effect = [False, True]
    mock_subprocess_run.return_value = subprocess.CompletedProcess(
        args=params["test_command"], returncode=0, stdout="Test passed", stderr=""
    )

    result = runner.run_test(params)

    # Ensure symlink creation calls
    mock_os_rename.assert_any_call(
        params["module_path"], params["module_path"] + ".bak"
    )
    mock_os_symlink.assert_called_with(
        params["replacement_module_path"], params["module_path"]
    )

    # Ensure subprocess run call
    mock_subprocess_run.assert_called_with(
        params["test_command"],
        text=True,
        capture_output=True,
        shell=True,
        cwd=os.getcwd(),
    )

    # Ensure symlink reversion calls
    mock_os_remove.assert_called_with(params["module_path"])
    mock_os_rename.assert_any_call(
        params["module_path"] + ".bak", params["module_path"]
    )

    assert result.returncode == 0
    assert result.stdout == "Test passed"
    assert result.stderr == ""


@patch("mutahunter.core.runner.os.path.exists")
@patch("mutahunter.core.runner.os.rename")
@patch("mutahunter.core.runner.os.symlink")
@patch("mutahunter.core.runner.os.remove")
def test_create_symlink(
    mock_os_remove, mock_os_symlink, mock_os_rename, mock_os_path_exists, runner
):
    original = "path/to/original_module.py"
    replacement = "path/to/replacement_module.py"
    backup = original + ".bak"

    mock_os_path_exists.return_value = False

    runner.create_symlink(original, replacement)

    mock_os_rename.assert_called_with(original, backup)
    mock_os_symlink.assert_called_with(replacement, original)


@patch("mutahunter.core.runner.os.path.exists")
@patch("mutahunter.core.runner.os.rename")
@patch("mutahunter.core.runner.os.remove")
def test_revert_symlink(mock_os_remove, mock_os_rename, mock_os_path_exists, runner):
    original = "path/to/original_module.py"
    backup = original + ".bak"

    mock_os_path_exists.return_value = True

    runner.revert_symlink(original)

    mock_os_remove.assert_called_with(original)
    mock_os_rename.assert_called_with(backup, original)
