import os
from unittest.mock import MagicMock, patch

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
        "test_file_path": "tests/test_file.py",
    }


@pytest.fixture
def mutant_hunter(config):
    with patch("mutahunter.core.hunter.Analyzer") as mock_analyzer:
        mock_analyzer_instance = mock_analyzer.return_value
        mock_analyzer_instance.file_lines_executed = {"file1.py": [1, 2, 3]}
        mock_analyzer_instance.dry_run.return_value = None
        yield MutantHunter(config)


@patch("mutahunter.core.hunter.os.path.exists", return_value=False)
@patch("mutahunter.core.hunter.os.rename")
@patch("mutahunter.core.hunter.os.symlink")
@patch("mutahunter.core.hunter.os.remove")
@patch("mutahunter.core.hunter.open", new_callable=MagicMock)
@patch("mutahunter.core.hunter.logger")
def test_prepare_mutant_file(
    mock_logger,
    mock_open,
    mock_os_remove,
    mock_os_symlink,
    mock_os_rename,
    mock_os_path_exists,
    mutant_hunter,
):
    source_path = "source.py"
    mutant_code = "mutant code"
    start_byte = 0
    end_byte = 10

    mock_open.side_effect = [MagicMock(), MagicMock()]
    mock_open.return_value.read.return_value = b"source code"

    with patch.object(mutant_hunter.analyzer, "check_syntax", return_value=True):
        mutant_path = mutant_hunter.prepare_mutant_file(
            "1", source_path, start_byte, end_byte, mutant_code
        )

    assert mutant_path == f"{os.getcwd()}/logs/_latest/mutants/1_source.py"


def test_prepare_mutant_file_syntax_error(mutant_hunter):
    source_path = "source.py"
    mutant_code = "mutant code"
    start_byte = 0
    end_byte = 10
    with patch.object(mutant_hunter.analyzer, "check_syntax", return_value=False):
        with patch("builtins.open", new_callable=MagicMock):
            with pytest.raises(Exception, match="Mutant code has syntax errors."):
                mutant_hunter.prepare_mutant_file(
                    "1", source_path, start_byte, end_byte, mutant_code
                )


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


def test_generate_mutations_skips_test_directories(mutant_hunter, config):
    mutant_hunter.analyzer.file_lines_executed = {"tests/test_file.py": [1, 2, 3]}
    mutations = list(mutant_hunter.generate_mutations())
    assert len(mutations) == 0


def test_generate_mutations_skips_files_in_exclude_files(mutant_hunter, config):
    config["exclude_files"] = ["file1.py"]
    mutant_hunter.analyzer.file_lines_executed = {"file1.py": [1, 2, 3]}
    mutations = list(mutant_hunter.generate_mutations())
    assert len(mutations) == 0


def test_generate_mutations_skips_files_not_in_only_mutate_file_paths(
    mutant_hunter, config
):
    config["only_mutate_file_paths"] = ["file2.py"]
    mutant_hunter.analyzer.file_lines_executed = {"file1.py": [1, 2, 3]}
    mutations = list(mutant_hunter.generate_mutations())
    assert len(mutations) == 0


@patch("mutahunter.core.hunter.logger")
def test_run_handles_exceptions(mock_logger, mutant_hunter):
    with patch.object(
        mutant_hunter.analyzer, "dry_run", side_effect=Exception("Test Exception")
    ):
        mutant_hunter.run()
    mock_logger.error.assert_called_with(
        "Error during mutation testing. Please report this issue. Test Exception"
    )


def test_run_mutation_testing_mutant_killed(mutant_hunter):
    mutant = {
        "source_path": "source.py",
        "start_byte": 0,
        "end_byte": 10,
        "hunk": "hunk",
        "mutant_code_snippet": "mutant code",
        "test_file_path": "tests/test_file.py",
    }

    mutant_hunter.generate_mutations = MagicMock(return_value=[mutant])
    mutant_hunter.prepare_mutant_file = MagicMock(return_value="mutant_path")
    result_mock = MagicMock()
    result_mock.returncode = 1
    result_mock.stderr = b"stderr"
    result_mock.stdout = b"stdout"
    mutant_hunter.run_test = MagicMock(return_value=result_mock)

    mutant_hunter.run_mutation_testing()

    assert len(mutant_hunter.mutants) == 1
    assert mutant_hunter.mutants[0].status == "KILLED"
    assert mutant_hunter.mutants[0].error_msg == b"stderrstdout"


def test_run_mutation_testing_mutant_survives(mutant_hunter):
    mutant = {
        "source_path": "source.py",
        "start_byte": 0,
        "end_byte": 10,
        "hunk": "hunk",
        "mutant_code_snippet": "mutant code",
        "test_file_path": "tests/test_file.py",
    }

    mutant_hunter.generate_mutations = MagicMock(return_value=[mutant])
    mutant_hunter.prepare_mutant_file = MagicMock(return_value="mutant_path")
    result_mock = MagicMock()
    result_mock.returncode = 0
    mutant_hunter.run_test = MagicMock(return_value=result_mock)

    mutant_hunter.run_mutation_testing()

    assert len(mutant_hunter.mutants) == 1
    assert mutant_hunter.mutants[0].status == "SURVIVED"


def test_run_mutation_testing_handles_exceptions_during_preparation(mutant_hunter):
    mutant = {
        "source_path": "source.py",
        "start_byte": 0,
        "end_byte": 10,
        "hunk": "hunk",
        "mutant_code_snippet": "mutant code",
        "test_file_path": "tests/test_file.py",
    }
    mutant_hunter.generate_mutations = MagicMock(return_value=[mutant])
    mutant_hunter.prepare_mutant_file = MagicMock(
        side_effect=Exception("Test Exception")
    )
    with patch("mutahunter.core.hunter.logger") as mock_logger:
        mutant_hunter.run_mutation_testing()
    mock_logger.error.assert_called_with("Error generating mutant: Test Exception")


def test_run_test_calls_test_runner(mutant_hunter):
    params = {
        "module_path": "source.py",
        "replacement_module_path": "mutant_path",
        "test_command": "pytest",
    }
    with patch.object(
        mutant_hunter.test_runner, "run_test", return_value="test_result"
    ) as mock_run_test:
        result = mutant_hunter.run_test(params)
    mock_run_test.assert_called_once_with(params)
    assert result == "test_result"
