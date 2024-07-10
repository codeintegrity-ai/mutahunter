import json
from dataclasses import asdict
from unittest.mock import mock_open, patch

import pytest

from unittest.mock import mock_open, patch
import json
from mutahunter.core.entities.config import MutahunterConfig
from mutahunter.core.entities.mutant import Mutant
from mutahunter.core.report import MutantReport


@pytest.fixture
def config():
    return MutahunterConfig(
        model="dummy_model",
        api_base="http://dummy_api_base",
        test_command="pytest",
        code_coverage_report_path="dummy_path",
        coverage_type="cobertura",
        exclude_files=[],
        only_mutate_file_paths=[],
        modified_files_only=False,
        extreme=False,
    )


@pytest.fixture
def mutants():
    return [
        Mutant(
            id="1",
            source_path="app.go",
            mutant_path="mutant1.py",
            status="KILLED",
            error_msg="",
            mutant_code="",
            type="",
            description="",
        ),
        Mutant(
            id="2",
            source_path="app.go",
            mutant_path="mutant2.py",
            status="SURVIVED",
            error_msg="",
            mutant_code="",
            type="",
            description="",
        ),
        Mutant(
            id="3",
            source_path="app.go",
            mutant_path="mutant3.py",
            status="KILLED",
            error_msg="",
            mutant_code="",
            type="",
            description="",
        ),
        Mutant(
            id="4",
            source_path="app.go",
            mutant_path="mutant4.py",
            status="SURVIVED",
            error_msg="",
            mutant_code="",
            type="",
            description="",
        ),
    ]


def test_mutant_report_initialization(config):
    report = MutantReport(config)
    assert report.config == config
    assert report.log_file == "logs/_latest/coverage.txt"


@patch.object(MutantReport, "save_report")
@patch.object(MutantReport, "_generate_summary_report")
@patch.object(MutantReport, "_generate_detailed_report")
def test_generate_report(
    mock_generate_detailed_report,
    mock_generate_summary_report,
    mock_save_report,
    config,
    mutants,
):
    report = MutantReport(config)
    total_cost = 100.0
    line_rate = 0.75

    report.generate_report(mutants, total_cost, line_rate)

    mutant_dicts = [asdict(mutant) for mutant in mutants]
    mock_save_report.assert_called_once_with("logs/_latest/mutants.json", mutant_dicts)
    mock_generate_summary_report.assert_called_once_with(
        mutant_dicts, total_cost, line_rate
    )
    mock_generate_detailed_report.assert_called_once_with(mutant_dicts)


@patch.object(MutantReport, "_compute_summary_data")
@patch.object(MutantReport, "_format_summary")
@patch.object(MutantReport, "_log_and_write")
def test_generate_summary_report(
    mock_log_and_write, mock_format_summary, mock_compute_summary_data, config, mutants
):
    report = MutantReport(config)
    total_cost = 100.0
    line_rate = 0.75

    summary_data = {
        "killed_mutants": 2,
        "survived_mutants": 2,
        "timeout_mutants": 0,
        "compile_error_mutants": 0,
        "total_mutants": 4,
        "valid_mutants": 4,
        "mutation_coverage": "50.00%",
    }
    mock_compute_summary_data.return_value = summary_data
    formatted_summary = "Formatted Summary Text"
    mock_format_summary.return_value = formatted_summary

    report._generate_summary_report(
        [asdict(mutant) for mutant in mutants], total_cost, line_rate
    )

    mock_compute_summary_data.assert_called_once_with(
        [asdict(mutant) for mutant in mutants]
    )
    mock_format_summary.assert_called_once_with(summary_data, total_cost, line_rate)
    mock_log_and_write.assert_called_once_with(formatted_summary)


def test_compute_summary_data(config, mutants):
    report = MutantReport(config)

    summary_data = report._compute_summary_data([asdict(mutant) for mutant in mutants])

    expected_data = {
        "killed_mutants": 2,
        "survived_mutants": 2,
        "timeout_mutants": 0,
        "compile_error_mutants": 0,
        "total_mutants": 4,
        "valid_mutants": 4,
        "mutation_coverage": "50.00%",
    }
    assert summary_data == expected_data


def test_format_summary(config):
    report = MutantReport(config)

    summary_data = {
        "killed_mutants": 2,
        "survived_mutants": 2,
        "timeout_mutants": 0,
        "compile_error_mutants": 0,
        "total_mutants": 4,
        "valid_mutants": 4,
        "mutation_coverage": "50.00%",
    }
    total_cost = 100.0
    line_rate = 0.75

    formatted_summary = report._format_summary(summary_data, total_cost, line_rate)

    expected_summary = (
        "Mutation Coverage:\n"
        "📊 Line Coverage: 75.00% 📊\n"
        "🎯 Mutation Coverage: 50.00% 🎯\n"
        "🦠 Total Mutants: 4 🦠\n"
        "🛡️ Survived Mutants: 2 🛡️\n"
        "🗡️ Killed Mutants: 2 🗡️\n"
        "🕒 Timeout Mutants: 0 🕒\n"
        "🔥 Compile Error Mutants: 0 🔥\n"
        "💰 Expected Cost: $100.00000 USD 💰"
    )
    assert formatted_summary == expected_summary


def test_compute_detailed_data_with_all_statuses(config, mutants):
    report = MutantReport(config)
    mutant_dicts = [asdict(mutant) for mutant in mutants]

    detailed_data = report._compute_detailed_data(mutant_dicts)

    expected_data = {
        "app.go": {
            "total_mutants": 4,
            "killed_mutants": 2,
            "survived_mutants": 2,
            "timeout_mutants": 0,
            "compile_error_mutants": 0,
            "mutation_coverage": "50.00%",
        }
    }
    assert detailed_data == expected_data


@patch("builtins.open", new_callable=mock_open)
@patch("mutahunter.core.logger.logger.info")
def test_log_and_write(mock_logger_info, mock_open_func, config):
    report = MutantReport(config)
    text = "Test log and write"

    report._log_and_write(text)

    mock_logger_info.assert_called_once_with(text)
    mock_open_func.assert_called_once_with("logs/_latest/coverage.txt", "a")
    mock_open_func().write.assert_called_once_with(text + "\n")


@patch.object(MutantReport, "_log_and_write")
def test_generate_detailed_report(mock_log_and_write, config, mutants):
    report = MutantReport(config)
    mutant_dicts = [asdict(mutant) for mutant in mutants]

    report._generate_detailed_report(mutant_dicts)

    detailed_data = report._compute_detailed_data(mutant_dicts)
    formatted_detailed_report = report._format_detailed_report(detailed_data)

    mock_log_and_write.assert_called_once_with(
        "\nDetailed Mutation Coverage:\n" + formatted_detailed_report
    )


@patch("builtins.open", new_callable=mock_open)
@patch("json.dump")
@patch("mutahunter.core.logger.logger.info")
def test_save_report(mock_logger_info, mock_json_dump, mock_open_func, config):
    report = MutantReport(config)
    data = {"key": "value"}
    filepath = "dummy_path.json"

    report.save_report(filepath, data)

    mock_open_func.assert_called_once_with(filepath, "w")
    mock_json_dump.assert_called_once_with(data, mock_open_func(), indent=4)
    mock_logger_info.assert_called_once_with(f"Report saved to {filepath}")


def test_compute_detailed_data_all_timeout(config):
    mutants = [
        Mutant(
            id="1",
            source_path="app.go",
            mutant_path="mutant1.py",
            status="TIMEOUT",
            error_msg="",
            mutant_code="",
            type="",
            description="",
        ),
        Mutant(
            id="2",
            source_path="app.go",
            mutant_path="mutant2.py",
            status="TIMEOUT",
            error_msg="",
            mutant_code="",
            type="",
            description="",
        ),
    ]
    report = MutantReport(config)
    mutant_dicts = [asdict(mutant) for mutant in mutants]

    detailed_data = report._compute_detailed_data(mutant_dicts)

    expected_data = {
        "app.go": {
            "total_mutants": 2,
            "killed_mutants": 0,
            "survived_mutants": 0,
            "timeout_mutants": 2,
            "compile_error_mutants": 0,
            "mutation_coverage": "0.00%",
        }
    }
    assert detailed_data == expected_data


def test_compute_detailed_data_with_compile_error(config):
    mutants = [
        Mutant(
            id="1",
            source_path="app.go",
            mutant_path="mutant1.py",
            status="KILLED",
            error_msg="",
            mutant_code="",
            type="",
            description="",
        ),
        Mutant(
            id="2",
            source_path="app.go",
            mutant_path="mutant2.py",
            status="COMPILE_ERROR",
            error_msg="",
            mutant_code="",
            type="",
            description="",
        ),
    ]
    report = MutantReport(config)
    mutant_dicts = [asdict(mutant) for mutant in mutants]

    detailed_data = report._compute_detailed_data(mutant_dicts)

    expected_data = {
        "app.go": {
            "total_mutants": 2,
            "killed_mutants": 1,
            "survived_mutants": 0,
            "timeout_mutants": 0,
            "compile_error_mutants": 1,
            "mutation_coverage": "100.00%",
        }
    }
    assert detailed_data == expected_data


def test_format_summary_extreme(config):
    config.extreme = True
    report = MutantReport(config)

    summary_data = {
        "killed_mutants": 2,
        "survived_mutants": 2,
        "timeout_mutants": 0,
        "compile_error_mutants": 0,
        "total_mutants": 4,
        "valid_mutants": 4,
        "mutation_coverage": "50.00%",
    }
    total_cost = 100.0
    line_rate = 0.75

    formatted_summary = report._format_summary(summary_data, total_cost, line_rate)

    expected_summary = (
        "Mutation Coverage:\n"
        "📊 Line Coverage: 75.00% 📊\n"
        "🎯 Mutation Coverage: 50.00% 🎯\n"
        "🦠 Total Mutants: 4 🦠\n"
        "🛡️ Survived Mutants: 2 🛡️\n"
        "🗡️ Killed Mutants: 2 🗡️\n"
        "🕒 Timeout Mutants: 0 🕒\n"
        "🔥 Compile Error Mutants: 0 🔥\n"
        "💰 No Cost for extreme mutation testing 💰"
    )
    assert formatted_summary == expected_summary
