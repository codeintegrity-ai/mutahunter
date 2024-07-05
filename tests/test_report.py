import json
from dataclasses import asdict
from unittest.mock import mock_open, patch

import pytest

from mutahunter.core.entities.mutant import Mutant
from mutahunter.core.report import MutantReport


@pytest.fixture
def config():
    return {
        "model": "test_model",
        "api_base": "http://localhost:8000",
    }


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


def test_generate_mutant_report_detail_all_statuses(config):
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
            status="TIMEOUT",
            error_msg="",
            mutant_code="",
            type="",
            description="",
        ),
        Mutant(
            id="4",
            source_path="app.go",
            mutant_path="mutant4.py",
            status="COMPILE_ERROR",
            error_msg="",
            mutant_code="",
            type="",
            description="",
        ),
    ]
    report = MutantReport(config)
    mutants = [asdict(mutant) for mutant in mutants]

    with patch.object(report, "save_report") as mock_save_report:
        report.generate_mutant_report_detail(mutants)

        mock_save_report.assert_called_once_with(
            "logs/_latest/mutation_coverage_detail.json",
            {
                "app.go": {
                    "total_mutants": 4,
                    "killed_mutants": 1,
                    "survived_mutants": 1,
                    "timeout_mutants": 1,
                    "compile_error_mutants": 1,
                    "mutation_coverage": "50.00%",
                }
            },
        )


def test_generate_mutant_report(mutants, config):
    report = MutantReport(config)
    mutants = [asdict(mutant) for mutant in mutants]

    with (
        patch.object(report, "save_report") as mock_save_report,
        patch("mutahunter.core.logger.logger.info") as mock_logger_info,
    ):
        report.generate_mutant_report(mutants, 0.0, 0.0)
        mock_logger_info.assert_any_call("📊 Line Coverage: %s 📊", "0.00%")
        mock_logger_info.assert_any_call("🎯 Mutation Coverage: %s 🎯", "50.00%")
        mock_logger_info.assert_any_call("🦠 Total Mutants: %d 🦠", len(mutants))
        mock_logger_info.assert_any_call("🛡️ Survived Mutants: %d 🛡️", 2)
        mock_logger_info.assert_any_call("🗡️ Killed Mutants: %d 🗡️", 2)
        mock_logger_info.assert_any_call("🕒 Timeout Mutants: %d 🕒", 0)
        mock_logger_info.assert_any_call("🔥 Compile Error Mutants: %d 🔥", 0)
        mock_logger_info.assert_any_call("💰 Expected Cost: $%.5f USD 💰", 0.0)

        mock_save_report.assert_called_once_with(
            "logs/_latest/mutation_coverage.json",
            {
                "total_mutants": 4,
                "killed_mutants": 2,
                "survived_mutants": 2,
                "timeout_mutants": 0,
                "compile_error_mutants": 0,
                "mutation_coverage": "50.00%",
                "line_coverage": "0.00%",
                "expected_cost": 0.0,
            },
        )


def test_save_report(config):
    report = MutantReport(config)
    data = {"key": "value"}
    filepath = "test.json"

    with (
        patch("builtins.open", mock_open()) as mock_file,
        patch("json.dump") as mock_json_dump,
        patch("mutahunter.core.logger.logger.info") as mock_logger_info,
    ):
        report.save_report(filepath, data)

        mock_file.assert_called_once_with(filepath, "w")
        mock_json_dump.assert_called_once_with(data, mock_file(), indent=4)
        mock_logger_info.assert_called_once_with(f"Report saved to {filepath}")
