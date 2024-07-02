import json
from unittest.mock import mock_open, patch

import pytest

from mutahunter.core.entities.mutant import Mutant
from mutahunter.core.report import MutantReport


@pytest.fixture
def config():
    return {
        "model": "test_model",
        "api_base": "http://localhost:8000",
        "test_file_path": "app_test.go",
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
            test_file_path="app_test.go",
            diff="",
        ),
        Mutant(
            id="2",
            source_path="app.go",
            mutant_path="mutant2.py",
            status="SURVIVED",
            error_msg="",
            test_file_path="app_test.go",
            diff="",
        ),
        Mutant(
            id="3",
            source_path="app.go",
            mutant_path="mutant3.py",
            status="KILLED",
            error_msg="",
            test_file_path="app_test.go",
            diff="",
        ),
        Mutant(
            id="4",
            source_path="app.go",
            mutant_path="mutant4.py",
            status="SURVIVED",
            error_msg="",
            test_file_path="app_test.go",
            diff="",
        ),
    ]


def test_generate_mutation_coverage_by_source_file(mutants, config):
    report = MutantReport(config)
    mutation_coverage = report.generate_mutation_coverage_by_source_file(mutants)
    assert mutation_coverage == {
        "app.go": {"killed": 2, "survived": 2, "total": 4, "mutation_score": "50.0%"}
    }


def test_generate_mutant_report(mutants, config):
    report = MutantReport(config)
    with patch("mutahunter.core.logger.logger.info") as mock_logger_info:
        report_summary = report.generate_mutant_report(mutants)
        assert report_summary == {
            "Total Mutants": 4,
            "Killed Mutants": 2,
            "Survived Mutants": 2,
            "Mutation Coverage": "50.0%",
        }
        mock_logger_info.assert_any_call("🦠 Total Mutants: 4 🦠")
        mock_logger_info.assert_any_call("🛡️ Survived Mutants: 2 🛡️")
        mock_logger_info.assert_any_call("🗡️ Killed Mutants: 2 🗡️")
        mock_logger_info.assert_any_call("🎯 Mutation Coverage: 50.0% 🎯")


def test_generate_report(mutants, config):
    report = MutantReport(config)
    with patch("builtins.open", mock_open()) as mocked_file:
        with patch("json.dump") as mock_json_dump:
            with (
                patch.object(
                    report, "generate_killed_mutants"
                ) as mock_generate_killed_mutants,
                patch.object(
                    report, "generate_survived_mutants"
                ) as mock_generate_survived_mutants,
                patch.object(
                    report,
                    "generate_mutation_coverage_by_source_file",
                    return_value={
                        "app.go": {
                            "killed": 2,
                            "survived": 2,
                            "total": 4,
                            "mutation_score": "50.0%",
                        }
                    },
                ) as mock_generate_mutation_coverage_by_source_file,
                patch.object(
                    report, "generate_mutant_report"
                ) as mock_generate_mutant_report,
            ):

                report.generate_report(mutants)

                mock_generate_killed_mutants.assert_called_once_with(mutants)
                mock_generate_survived_mutants.assert_called_once_with(mutants)
                mock_generate_mutation_coverage_by_source_file.assert_called_once_with(
                    mutants
                )
                mock_generate_mutant_report.assert_called_once_with(mutants)

                mocked_file.assert_any_call("logs/_latest/mutation_coverage.json", "w")
                mock_json_dump.assert_called_once_with(
                    {
                        "app.go": {
                            "killed": 2,
                            "survived": 2,
                            "total": 4,
                            "mutation_score": "50.0%",
                        }
                    },
                    mocked_file(),
                    indent=2,
                )


def test_generate_survived_mutants(mutants, config):
    report = MutantReport(config)
    with patch("builtins.open", mock_open()) as mocked_file:
        with patch("json.dump") as mock_json_dump:
            report.generate_survived_mutants(mutants)
            mocked_file.assert_called_once_with(
                "logs/_latest/mutants_survived.json", "w"
            )
            mock_json_dump.assert_called_once()
            written_data = mock_json_dump.call_args[0][0]
            assert written_data == {
                "app_test.go": [
                    {
                        "id": "2",
                        "source_path": "app.go",
                        "mutant_path": "mutant2.py",
                        "status": "SURVIVED",
                        "error_msg": "",
                        "test_file_path": "app_test.go",
                        "diff": "",
                    },
                    {
                        "id": "4",
                        "source_path": "app.go",
                        "mutant_path": "mutant4.py",
                        "status": "SURVIVED",
                        "error_msg": "",
                        "test_file_path": "app_test.go",
                        "diff": "",
                    },
                ]
            }


def test_generate_killed_mutants(mutants, config):
    report = MutantReport(config)
    with patch("builtins.open", mock_open()) as mocked_file:
        with patch("json.dump") as mock_json_dump:
            report.generate_killed_mutants(mutants)
            mocked_file.assert_called_once_with("logs/_latest/mutants_killed.json", "w")
            mock_json_dump.assert_called_once()
            written_data = mock_json_dump.call_args[0][0]
            assert written_data == {
                "app_test.go": [
                    {
                        "id": "1",
                        "source_path": "app.go",
                        "mutant_path": "mutant1.py",
                        "status": "KILLED",
                        "error_msg": "",
                        "test_file_path": "app_test.go",
                        "diff": "",
                    },
                    {
                        "id": "3",
                        "source_path": "app.go",
                        "mutant_path": "mutant3.py",
                        "status": "KILLED",
                        "error_msg": "",
                        "test_file_path": "app_test.go",
                        "diff": "",
                    },
                ]
            }
