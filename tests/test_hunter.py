import os
from unittest.mock import MagicMock, patch

import pytest

from unittest.mock import patch
import subprocess
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


def test_get_modified_files(mutant_hunter):
    with patch("subprocess.check_output", side_effect=[
        b"file1.py\nfile2.py\n",
        b"file1.py\nfile2.py\n",
        b"file1.py\nfile2.py\n"
    ]):
        modified_files = mutant_hunter.get_modified_files()
    
    assert modified_files == ["file1.py"]


def test_process_test_result_killed(mutant_hunter):
    result = MagicMock()
    result.returncode = 1
    result.stderr = "stderr"
    result.stdout = "stdout"
    mutant = Mutant(id="1", diff="diff", source_path="source.py", mutant_path="mutant.py")
    
    mutant_hunter.process_test_result(result, mutant)
    
    assert mutant.status == "KILLED"
    assert mutant.error_msg == "stderrstdout"
    assert len(mutant_hunter.mutants) == 1
    assert mutant_hunter.mutants[0].status == "KILLED"


def test_process_test_result_survived(mutant_hunter):
    result = MagicMock()
    result.returncode = 0
    mutant = Mutant(id="1", diff="diff", source_path="source.py", mutant_path="mutant.py")
    
    mutant_hunter.process_test_result(result, mutant)
    
    assert mutant.status == "SURVIVED"
    assert len(mutant_hunter.mutants) == 1
    assert mutant_hunter.mutants[0].status == "SURVIVED"

@patch.object(MutantHunter, "prepare_mutant_file", side_effect=Exception("Test Exception"))
@patch("mutahunter.core.hunter.logger")
def test_process_mutant_handles_exceptions(mock_logger, mock_prepare_mutant_file, mutant_hunter):
    mutant_data = {
        "source_path": "source.py",
        "start_byte": 0,
        "end_byte": 10,
        "mutant_code_snippet": "mutant code",
        "hunk": ["hunk data"]
    }
    mutant_hunter.process_mutant(mutant_data)
    mock_logger.error.assert_called_with(
        "Error processing mutant for file: source.py",
        exc_info=True,
    )


@patch.object(MutantHunter, "get_modified_files", return_value=["file1.py", "file2.py"])
@patch.object(MutantHunter, "should_skip_file", side_effect=[True, False])
@patch.object(MutantHunter, "get_modified_lines", return_value=[1, 2, 3])
@patch.object(MutantHunter, "generate_mutations_for_file", return_value=[{"mutation": "data"}])
def test_generate_mutations_for_modified_files_skips_files(mock_generate_mutations_for_file, mock_get_modified_lines, mock_should_skip_file, mock_get_modified_files, mutant_hunter):
    mutations = list(mutant_hunter.generate_mutations_for_modified_files())
    assert len(mutations) == 1


@patch.object(MutantHunter, "generate_mutations_for_modified_files", return_value=[{"mutation": "data1"}, {"mutation": "data2"}])
@patch.object(MutantHunter, "process_mutant")
def test_run_mutation_testing_on_modified_files_processes_all_mutants(mock_process_mutant, mock_generate_mutations_for_modified_files, mutant_hunter):
    mutant_hunter.run_mutation_testing_on_modified_files()
    assert mock_process_mutant.call_count == 2


@patch.object(MutantHunter, "generate_mutations", return_value=[{"mutation": "data1"}, {"mutation": "data2"}])
@patch.object(MutantHunter, "process_mutant")
def test_run_mutation_testing_processes_all_mutants(mock_process_mutant, mock_generate_mutations, mutant_hunter):
    mutant_hunter.run_mutation_testing()
    assert mock_process_mutant.call_count == 2


def test_generate_mutations_yields_mutations(mutant_hunter):
    mutant_hunter.analyzer.file_lines_executed = {"file1.py": [1, 2, 3]}
    with patch.object(mutant_hunter, "generate_mutations_for_file", return_value=[{"mutation": "data"}]):
        mutations = list(mutant_hunter.generate_mutations())
    assert len(mutations) > 0


def test_should_skip_file_raises_file_not_found_error(mutant_hunter):
    mutant_hunter.config["only_mutate_file_paths"] = ["non_existent_file.py"]
    with pytest.raises(FileNotFoundError, match="File non_existent_file.py does not exist."):
        mutant_hunter.should_skip_file("some_file.py")


@patch("mutahunter.core.hunter.logger")
def test_run_handles_exceptions(mock_logger, mutant_hunter):
    with patch.object(mutant_hunter.analyzer, "dry_run", side_effect=Exception("Test Exception")):
        mutant_hunter.run()
    mock_logger.error.assert_called_with(
        "Error during mutation testing. Please report this issue.",
        exc_info=True,
    )


@patch.object(MutantHunter, "run_mutation_testing_on_modified_files")
def test_run_mutation_testing_on_modified_files(mock_run_mutation_testing_on_modified_files, mutant_hunter):
    mutant_hunter.config["modified_files_only"] = True
    mutant_hunter.run()
    mock_run_mutation_testing_on_modified_files.assert_called_once()


def test_get_modified_lines_no_changes(mutant_hunter):
    file_path = "file1.py"
    diff_output = []
    with patch("subprocess.check_output", return_value="\n".join(diff_output).encode("utf-8")):
        modified_lines = mutant_hunter.get_modified_lines(file_path)
    assert modified_lines == []


def test_generate_mutations_for_file_no_covered_blocks(mutant_hunter):
    file_path = "file1.py"
    executed_lines = [1, 2, 3]
    with patch.object(mutant_hunter.analyzer, "get_covered_function_blocks", return_value=([], [])):
        mutations = list(mutant_hunter.generate_mutations_for_file(file_path, executed_lines))
    assert len(mutations) == 0


def test_get_modified_files_handles_subprocess_error(mutant_hunter):
    with patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "git")):
        modified_files = mutant_hunter.get_modified_files()
    assert modified_files == []


def test_process_test_result_unknown_return_code(mutant_hunter):
    result = MagicMock()
    result.returncode = 2
    mutant = Mutant(id="1", diff="diff", source_path="source.py", mutant_path="mutant.py")
    mutant_hunter.process_test_result(result, mutant)
    assert len(mutant_hunter.mutants) == 0


def test_generate_mutations_for_file_file_not_found(mutant_hunter):
    file_path = "file1.py"
    executed_lines = [1, 2, 3]
    covered_function_blocks = [MagicMock(start_byte=0, end_byte=10)]
    covered_function_block_executed_lines = [[1, 2, 3]]
    
    with patch.object(mutant_hunter.analyzer, "get_covered_function_blocks", return_value=(covered_function_blocks, covered_function_block_executed_lines)):
        with patch("mutahunter.core.hunter.MutantGenerator.generate", return_value=[(None, "hunk", "content")]):
            with pytest.raises(FileNotFoundError):
                list(mutant_hunter.generate_mutations_for_file(file_path, executed_lines))


def test_get_modified_lines_identifies_modified_lines(mutant_hunter):
    file_path = "file1.py"
    diff_output = [
        "@@ -1,2 +1,2 @@",
        "+modified line 1",
        "+modified line 2"
    ]
    
    with patch("subprocess.check_output", return_value="\n".join(diff_output).encode("utf-8")):
        modified_lines = mutant_hunter.get_modified_lines(file_path)
    
    assert modified_lines == [1, 2]


def test_run_test_calls_test_runner(mutant_hunter):
    params = {
        "module_path": "source.py",
        "replacement_module_path": "mutant.py",
        "test_command": "pytest"
    }
    
    with patch.object(mutant_hunter.test_runner, "run_test", return_value="test_result") as mock_run_test:
        result = mutant_hunter.run_test(params)
    
    mock_run_test.assert_called_once_with(params)
    assert result == "test_result"



def test_get_modified_lines_handles_subprocess_error(mutant_hunter):
    file_path = "file1.py"
    with patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "git")):
        modified_lines = mutant_hunter.get_modified_lines(file_path)
    assert modified_lines == []
