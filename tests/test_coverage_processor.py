import xml.etree.ElementTree as ET
from unittest.mock import Mock, mock_open, patch

import pytest

from mutahunter.core.coverage_processor import CoverageProcessor
from mutahunter.core.entities.config import MutatorConfig


@pytest.fixture
def config():
    return MutatorConfig(
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
def cobertura_xml_content():
    return """<?xml version="1.0" ?>
    <coverage line-rate="0.8">
        <packages>
            <package>
                <classes>
                    <class filename="test_file.py">
                        <lines>
                            <line number="1" hits="1"/>
                            <line number="2" hits="0"/>
                            <line number="3" hits="1"/>
                        </lines>
                    </class>
                </classes>
            </package>
        </packages>
    </coverage>"""


@pytest.fixture
def jacoco_xml_content():
    return """<?xml version="1.0" ?>
    <report>
        <package name="com/example">
            <sourcefile name="TestFile.java">
                <line nr="1" mi="0" ci="1"/>
                <line nr="2" mi="1" ci="0"/>
                <line nr="3" mi="0" ci="1"/>
            </sourcefile>
        </package>
    </report>"""


@pytest.fixture
def lcov_content():
    return """SF:test_file.py
DA:1,1
DA:2,0
DA:3,1
LF:3
LH:2
end_of_record"""


@patch("xml.etree.ElementTree.parse")
def test_parse_coverage_report_cobertura(mock_parse, config, cobertura_xml_content):
    config.coverage_type = "cobertura"
    mock_tree = Mock()
    mock_tree.getroot.return_value = ET.fromstring(cobertura_xml_content)
    mock_parse.return_value = mock_tree

    cov_processor = CoverageProcessor(
        coverage_type=config.coverage_type,
        code_coverage_report_path=config.code_coverage_report_path,
    )
    cov_processor.parse_coverage_report()

    assert cov_processor.file_lines_executed == {"test_file.py": [1, 3]}
    assert cov_processor.file_lines_not_executed == {"test_file.py": [2]}
    assert cov_processor.line_coverage_rate == 0.67


@patch("xml.etree.ElementTree.parse")
def test_parse_coverage_report_jacoco(mock_parse, config, jacoco_xml_content):
    config.coverage_type = "jacoco"
    mock_tree = Mock()
    mock_tree.getroot.return_value = ET.fromstring(jacoco_xml_content)
    mock_parse.return_value = mock_tree

    cov_processor = CoverageProcessor(
        coverage_type=config.coverage_type,
        code_coverage_report_path=config.code_coverage_report_path,
    )
    cov_processor.parse_coverage_report()

    assert cov_processor.file_lines_executed == {
        "src/main/java/com/example/TestFile.java": [1, 3]
    }
    assert cov_processor.file_lines_not_executed == {
        "src/main/java/com/example/TestFile.java": [2]
    }
    assert cov_processor.line_coverage_rate == 0.67


@patch("builtins.open", new_callable=mock_open)
def test_parse_coverage_report_lcov(mock_open, config, lcov_content):
    config.coverage_type = "lcov"
    mock_open.return_value.readlines.return_value = lcov_content.splitlines(
        keepends=True
    )

    cov_processor = CoverageProcessor(
        coverage_type=config.coverage_type,
        code_coverage_report_path=config.code_coverage_report_path,
    )
    cov_processor.parse_coverage_report()

    assert cov_processor.file_lines_executed == {"test_file.py": [1, 3]}
    assert cov_processor.file_lines_not_executed == {"test_file.py": [2]}
    assert cov_processor.line_coverage_rate == 0.67


def test_invalid_coverage_type(config):
    config.coverage_type = "invalid_type"

    with pytest.raises(
        ValueError,
        match="Invalid coverage tool. Please specify either 'cobertura', 'jacoco', or 'lcov'.",
    ):
        cov_processor = CoverageProcessor(
            coverage_type=config.coverage_type,
            code_coverage_report_path=config.code_coverage_report_path,
        )
        cov_processor.parse_coverage_report()
