import json
from dataclasses import asdict
from unittest.mock import mock_open, patch

import pytest

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
