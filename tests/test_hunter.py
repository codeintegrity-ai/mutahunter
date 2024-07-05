import os
import subprocess
from unittest.mock import MagicMock, call, patch

import pytest

from mutahunter.core.entities.mutant import Mutant
from mutahunter.core.hunter import MutantHunter


@pytest.fixture
def config():
    return {
        "language": "python",
        "test_command": "pytest",
        "code_coverage_report_path": "path/to/coverage_report.xml",
        "only_mutate_file_paths": [],
        "exclude_files": [],
        "model": "test_model",  # Adding the missing 'model' key
        "api_base": "http://localhost:8000",  # Adding the missing 'api_base' key
    }


@pytest.fixture
def mutant_hunter(config):
    with patch("mutahunter.core.hunter.Analyzer") as mock_analyzer:
        mock_analyzer_instance = mock_analyzer.return_value
        mock_analyzer_instance.file_lines_executed = {"file1.py": [1, 2, 3]}
        mock_analyzer_instance.dry_run.return_value = None
        yield MutantHunter(config)


@patch("mutahunter.core.hunter.logger")
@patch.object(MutantHunter, "run_mutation_testing")
def test_run_generates_mutation_report(
    mock_run_mutation_testing, mock_logger, mutant_hunter
):
    mock_run_mutation_testing.return_value = None
    mutant_hunter.run()
    mock_logger.info.assert_any_call("Starting Coverage Analysis...")
    mock_logger.info.assert_any_call("🦠 Generating Mutations... 🦠")
    mock_logger.info.assert_any_call("🎯 Generating Mutation Report... 🎯")


@patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "git"))
@patch("mutahunter.core.hunter.logger")
def test_get_modified_files_handles_called_process_error(
    mock_logger, mock_check_output, mutant_hunter
):
    modified_files = mutant_hunter.get_modified_files()
    assert modified_files == []
    mock_logger.error.assert_called_with(
        "Error identifying modified files: Command 'git' returned non-zero exit status 1."
    )


def test_process_test_result_updates_status(mutant_hunter):
    mutant = Mutant(
        id="1",
        source_path="source.py",
        mutant_path="mutant.py",
        mutant_code="code",
        type="type",
        description="description",
    )
    result = MagicMock(returncode=1, stderr="error", stdout="output")
    mutant_hunter.process_test_result(result, mutant)
    assert mutant.status == "KILLED"
    assert mutant.error_msg == "erroroutput"
    result.returncode = 0
    mutant_hunter.process_test_result(result, mutant)
    assert mutant.status == "SURVIVED"


@patch.object(MutantHunter, "prepare_mutant_file", return_value="mutant_path")
@patch.object(
    MutantHunter,
    "run_test",
    return_value=MagicMock(returncode=1, stderr="error", stdout="output"),
)
def test_process_mutant_updates_status(
    mock_run_test, mock_prepare_mutant_file, mutant_hunter
):
    mutant_data = {"mutant_code": "code", "type": "type", "description": "description"}
    mutant_hunter.process_mutant(mutant_data, "source_file.py", 0, 10)
    assert len(mutant_hunter.mutants) == 1
    assert mutant_hunter.mutants[0].status == "KILLED"
    assert mutant_hunter.mutants[0].error_msg == "erroroutput"


@patch.object(
    MutantHunter, "get_modified_files", return_value=["file1.py", "test_file.py"]
)
@patch.object(MutantHunter, "get_modified_lines", return_value=[1, 2, 3])
@patch.object(MutantHunter, "generate_mutations")
def test_run_mutation_testing_on_modified_files_generates_mutations(
    mock_generate_mutations,
    mock_get_modified_lines,
    mock_get_modified_files,
    mutant_hunter,
):
    mutant_hunter.run_mutation_testing_on_modified_files()
    mock_generate_mutations.assert_called_once_with("file1.py", [1, 2, 3])


@patch.object(MutantHunter, "generate_mutations")
def test_run_mutation_testing_generates_mutations(
    mock_generate_mutations, mutant_hunter
):
    mutant_hunter.analyzer.file_lines_executed = {
        "file1.py": [1, 2, 3],
        "test_file.py": [1, 2, 3],
    }
    mutant_hunter.run_mutation_testing()
    mock_generate_mutations.assert_called_once_with("file1.py", [1, 2, 3])


def test_should_skip_file_identifies_test_files(mutant_hunter):
    test_files = [
        "test_file.py",
        "file_test.py",
        "file.test.py",
        "file.spec.py",
        "file.tests.py",
        "file.Test.py",
        "Test_file.py",
    ]
    for test_file in test_files:
        assert mutant_hunter.should_skip_file(test_file) is True
    non_test_file = "regular_file.py"
    assert mutant_hunter.should_skip_file(non_test_file) is False


def test_should_skip_file_raises_file_not_found(mutant_hunter):
    mutant_hunter.config["only_mutate_file_paths"] = ["non_existent_file.py"]
    with pytest.raises(
        FileNotFoundError, match="File non_existent_file.py does not exist."
    ):
        mutant_hunter.should_skip_file("some_file.py")


@patch("mutahunter.core.hunter.logger")
def test_run_handles_exception(mock_logger, mutant_hunter):
    with patch.object(
        mutant_hunter, "run_mutation_testing", side_effect=Exception("Test Exception")
    ):
        mutant_hunter.run()
    mock_logger.error.assert_called_with(
        "Error during mutation testing. Please report this issue.",
        exc_info=True,
    )


@patch.object(MutantHunter, "run_mutation_testing_on_modified_files")
@patch("mutahunter.core.hunter.logger")
def test_run_modified_files_only(
    mock_logger, mock_run_mutation_testing_on_modified_files, mutant_hunter
):
    mutant_hunter.config["modified_files_only"] = True
    mock_run_mutation_testing_on_modified_files.return_value = None
    mutant_hunter.run()
    mock_logger.info.assert_any_call(
        "🦠 Running mutation testing on modified files... 🦠"
    )


def test_run_test_execution(mutant_hunter):
    params = {
        "module_path": "test_module.py",
        "replacement_module_path": "mutant_module.py",
        "test_command": "pytest",
    }
    with patch.object(mutant_hunter.test_runner, "run_test") as mock_run_test:
        mock_run_test.return_value = MagicMock(returncode=0)
        result = mutant_hunter.run_test(params)
        mock_run_test.assert_called_once_with(params)
        assert result.returncode == 0


def test_should_skip_file_with_only_mutate_file_paths(mutant_hunter):
    mutant_hunter.config["only_mutate_file_paths"] = ["file1.py", "file2.py"]
    with patch("os.path.exists", return_value=True):
        assert mutant_hunter.should_skip_file("file1.py") is False
        assert mutant_hunter.should_skip_file("file2.py") is False
        assert mutant_hunter.should_skip_file("file3.py") is True


def test_get_modified_lines_handles_subprocess_error(mutant_hunter):
    file_path = "test_file.py"
    with patch(
        "subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "git")
    ):
        with patch("mutahunter.core.hunter.logger") as mock_logger:
            modified_lines = mutant_hunter.get_modified_lines(file_path)

            assert modified_lines == []
            mock_logger.error.assert_called_once_with(
                f"Error identifying modified lines in {file_path}: Command 'git' returned non-zero exit status 1."
            )


def test_generate_mutations_processes_all_function_blocks(mutant_hunter):
    file_path = "test_file.py"
    executed_lines = [1, 2, 3, 4, 5]

    mock_function_block = MagicMock()
    mock_function_block.start_byte = 0
    mock_function_block.end_byte = 100
    mock_function_block.child_by_field_name.return_value.text.decode.return_value = (
        "test_function"
    )

    with patch.object(
        mutant_hunter.analyzer,
        "get_covered_function_blocks",
        return_value=([mock_function_block], [[1, 2, 3]]),
    ):
        with patch("mutahunter.core.hunter.MutantGenerator") as mock_mutant_generator:
            mock_mutant_generator.return_value.generate.return_value = [
                {"mutant_code": "test", "type": "test", "description": "test"}
            ]
            with patch.object(mutant_hunter, "process_mutant") as mock_process_mutant:
                mutant_hunter.generate_mutations(file_path, executed_lines)

                mock_mutant_generator.assert_called_once()
                mock_process_mutant.assert_called_once()


def test_get_modified_files_no_previous_commit(mutant_hunter):
    with patch("subprocess.check_output") as mock_check_output:
        mock_check_output.side_effect = [
            b"",  # no unstaged changes
            subprocess.CalledProcessError(
                128, "git", stderr=b"ambiguous argument 'HEAD^'"
            ),
            b"file1.py\nfile2.py\n",  # modified files
        ]
        mutant_hunter.analyzer.file_lines_executed = {
            "file1.py": [1, 2],
            "file2.py": [1, 2],
        }
        modified_files = mutant_hunter.get_modified_files()
        assert modified_files == ["file1.py", "file2.py"]
        mock_check_output.assert_has_calls(
            [
                call(["git", "diff", "--name-only"]),
                call(["git", "diff", "--name-only", "HEAD^..HEAD"]),
                call(["git", "diff", "--name-only", "HEAD"]),
            ]
        )


def test_run_mutation_testing_on_modified_files_skips_no_modified_lines(mutant_hunter):
    with patch.object(
        mutant_hunter, "get_modified_files", return_value=["file1.py", "file2.py"]
    ):
        with patch.object(mutant_hunter, "should_skip_file", return_value=False):
            with patch.object(
                mutant_hunter, "get_modified_lines", side_effect=[[], [1, 2, 3]]
            ):
                with patch.object(
                    mutant_hunter, "generate_mutations"
                ) as mock_generate_mutations:
                    mutant_hunter.run_mutation_testing_on_modified_files()
                    mock_generate_mutations.assert_called_once_with(
                        "file2.py", [1, 2, 3]
                    )


def test_get_modified_lines_no_previous_commit(mutant_hunter):
    file_path = "test_file.py"
    with patch("subprocess.check_output") as mock_check_output:
        mock_check_output.side_effect = [
            b"",  # no unstaged changes
            subprocess.CalledProcessError(
                128, "git", stderr=b"ambiguous argument 'HEAD^'"
            ),
            b"@@ -1,3 +1,4 @@\n+new line\n",  # diff output
        ]
        with patch("mutahunter.core.hunter.logger") as mock_logger:
            modified_lines = mutant_hunter.get_modified_lines(file_path)
            assert modified_lines == [1, 2, 3, 4]
            mock_logger.warning.assert_called_once_with(
                "No previous commit found. Using initial commit for diff."
            )
            mock_check_output.assert_has_calls(
                [
                    call(["git", "diff", "--name-only"]),
                    call(["git", "diff", "-U0", "HEAD^..HEAD", file_path]),
                    call(["git", "diff", "-U0", "HEAD", file_path]),
                ]
            )


def test_get_modified_files_with_unstaged_changes(mutant_hunter):
    with patch("subprocess.check_output") as mock_check_output:
        mock_check_output.side_effect = [
            b"file1.py\nfile2.py\n",  # unstaged changes
            b"file1.py\nfile3.py\n",  # modified files
        ]
        mutant_hunter.analyzer.file_lines_executed = {
            "file1.py": [1, 2],
            "file3.py": [1, 2],
        }
        modified_files = mutant_hunter.get_modified_files()
        assert modified_files == ["file1.py", "file3.py"]
        mock_check_output.assert_has_calls(
            [
                call(["git", "diff", "--name-only"]),
                call(["git", "diff", "--name-only", "HEAD"]),
            ]
        )


def test_generate_mutations_no_covered_function_blocks(mutant_hunter):
    file_path = "test_file.py"
    executed_lines = [1, 2, 3]
    with patch.object(
        mutant_hunter.analyzer, "get_covered_function_blocks", return_value=([], [])
    ):
        mutant_hunter.generate_mutations(file_path, executed_lines)


def test_should_skip_file_exclude_files(mutant_hunter):
    mutant_hunter.config["exclude_files"] = ["excluded_file.py"]
    assert mutant_hunter.should_skip_file("excluded_file.py") is True


def test_process_test_result_compile_error(mutant_hunter):
    mutant = Mutant(
        id="1",
        source_path="source.py",
        mutant_path="mutant.py",
        mutant_code="code",
        type="type",
        description="description",
    )
    result = MagicMock(returncode=3, stderr="compile error", stdout="output")
    mutant_hunter.process_test_result(result, mutant)
    assert mutant.status == "COMPILE_ERROR"
    assert mutant.error_msg == "compile erroroutput"


def test_process_test_result_timeout(mutant_hunter):
    mutant = Mutant(
        id="1",
        source_path="source.py",
        mutant_path="mutant.py",
        mutant_code="code",
        type="type",
        description="description",
    )
    result = MagicMock(returncode=2, stderr="timeout error", stdout="output")
    mutant_hunter.process_test_result(result, mutant)
    assert mutant.status == "TIMEOUT"
    assert mutant.error_msg == "timeout error"


@patch.object(MutantHunter, "prepare_mutant_file", return_value="")
def test_process_mutant_compile_error(mock_prepare_mutant_file, mutant_hunter):
    mutant_data = {"mutant_code": "code", "type": "type", "description": "description"}
    mutant_hunter.process_mutant(mutant_data, "source_file.py", 0, 10)
    assert len(mutant_hunter.mutants) == 1
    assert mutant_hunter.mutants[0].status == "COMPILE_ERROR"
