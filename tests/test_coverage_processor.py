import xml.etree.ElementTree as ET
from unittest.mock import Mock, mock_open, patch

import pytest

from mutahunter.core.coverage_processor import CoverageProcessor
from mutahunter.core.entities.config import MutationTestControllerConfig


@pytest.fixture
def config():
    return MutationTestControllerConfig(
        model="dummy_model",
        api_base="http://dummy_api_base",
        test_command="pytest",
        code_coverage_report_path="dummy_path",
        coverage_type="cobertura",
        exclude_files=[],
        only_mutate_file_paths=[],
        diff=False,
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


def test_check_file_exists():
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="dummy_path"
    )
    with pytest.raises(FileNotFoundError):
        cov_processor._check_file_exists("non_existent_file")


def test_check_file_extension():
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="dummy_path"
    )
    with pytest.raises(ValueError):
        cov_processor._check_file_extension([".xml"], "dummy_path.info")


def test_calculate_line_coverage_rate_for_file():
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="dummy_path"
    )
    cov_processor.file_lines_executed = {"test_file.py": [1, 3]}
    cov_processor.file_lines_not_executed = {"test_file.py": [2]}
    rate = cov_processor.calculate_line_coverage_rate_for_file("test_file.py")
    assert rate == 2 / 3


def test_calculate_line_coverage_rate():
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="dummy_path"
    )
    cov_processor.file_lines_executed = {"test_file.py": [1, 3], "another_file.py": [1]}
    cov_processor.file_lines_not_executed = {
        "test_file.py": [2],
        "another_file.py": [2, 3],
    }
    rate = cov_processor.calculate_line_coverage_rate()
    assert rate == 0.5


@patch("os.walk")
def test_find_source_file(mock_walk):
    mock_walk.return_value = [
        ("/home/user/project/src", [], ["test_file.py"]),
        ("/home/user/project/tests", [], ["test_file_test.py"]),
    ]
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="dummy_path"
    )
    file_path = cov_processor.find_source_file("test_file.py")
    assert file_path == "/home/user/project/src/test_file.py"


def test_calculate_line_coverage_rate_for_file_no_lines():
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="dummy_path"
    )
    rate = cov_processor.calculate_line_coverage_rate_for_file("empty_file.py")
    assert rate == 0.00


def test_calculate_line_coverage_rate_no_lines():
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="dummy_path"
    )
    rate = cov_processor.calculate_line_coverage_rate()
    assert rate == 0.00


def test_check_file_exists():
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="dummy_path"
    )
    with pytest.raises(FileNotFoundError):
        cov_processor._check_file_exists("non_existent_file")


def test_check_file_extension_valid():
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="dummy_path"
    )
    try:
        cov_processor._check_file_extension([".info"], "dummy_path.info")
    except ValueError:
        pytest.fail("ValueError raised unexpectedly!")


@patch("os.path.exists", return_value=True)
def test_check_file_exists_valid(mock_exists):
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="dummy_path"
    )
    try:
        cov_processor._check_file_exists("dummy_path")
    except FileNotFoundError:
        pytest.fail("FileNotFoundError raised unexpectedly!")


def test_check_file_extension_invalid():
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="dummy_path"
    )
    with pytest.raises(ValueError):
        cov_processor._check_file_extension([".xml"], "dummy_path.info")


def test_parse_coverage_report_file_not_found():
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="non_existent_file.info"
    )
    with pytest.raises(
        FileNotFoundError, match="File 'non_existent_file.info' not found."
    ):
        cov_processor.parse_coverage_report()


def test_parse_coverage_report_lcov_invalid_file():
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="non_existent_file.info"
    )
    with pytest.raises(
        FileNotFoundError, match="File 'non_existent_file.info' not found."
    ):
        cov_processor.parse_coverage_report()


def test_parse_coverage_report_cobertura_invalid_file():
    cov_processor = CoverageProcessor(
        coverage_type="cobertura", code_coverage_report_path="non_existent_file.xml"
    )
    with pytest.raises(
        FileNotFoundError, match="File 'non_existent_file.xml' not found."
    ):
        cov_processor.parse_coverage_report()


def test_parse_coverage_report_jacoco_invalid_file():
    cov_processor = CoverageProcessor(
        coverage_type="jacoco", code_coverage_report_path="non_existent_file.xml"
    )
    with pytest.raises(
        FileNotFoundError, match="File 'non_existent_file.xml' not found."
    ):
        cov_processor.parse_coverage_report()


def test_calculate_line_coverage_rate_no_executed_lines():
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="dummy_path"
    )
    cov_processor.file_lines_executed = {"test_file.py": []}
    cov_processor.file_lines_not_executed = {"test_file.py": [1, 2, 3]}
    rate = cov_processor.calculate_line_coverage_rate()
    assert rate == 0.00


def test_parse_coverage_report_invalid_type():
    cov_processor = CoverageProcessor(
        coverage_type="invalid_type", code_coverage_report_path="dummy_path"
    )
    with pytest.raises(
        ValueError,
        match="Invalid coverage tool. Please specify either 'cobertura', 'jacoco', or 'lcov'.",
    ):
        cov_processor.parse_coverage_report()


@patch("os.path.exists", return_value=True)
def test_check_file_exists_valid(mock_exists):
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="dummy_path"
    )
    try:
        cov_processor._check_file_exists("dummy_path")
    except FileNotFoundError:
        pytest.fail("FileNotFoundError raised unexpectedly!")


def test_calculate_line_coverage_rate_all_executed_lines():
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="dummy_path"
    )
    cov_processor.file_lines_executed = {"test_file.py": [1, 2, 3]}
    cov_processor.file_lines_not_executed = {"test_file.py": []}
    rate = cov_processor.calculate_line_coverage_rate()
    assert rate == 1.00


def test_calculate_line_coverage_rate_all_executed():
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="dummy_path"
    )
    cov_processor.file_lines_executed = {"test_file.py": [1, 2, 3]}
    cov_processor.file_lines_not_executed = {"test_file.py": []}
    rate = cov_processor.calculate_line_coverage_rate()
    assert rate == 1.00


def test_calculate_line_coverage_rate_all_missed():
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="dummy_path"
    )
    cov_processor.file_lines_executed = {"test_file.py": []}
    cov_processor.file_lines_not_executed = {"test_file.py": [1, 2, 3]}
    rate = cov_processor.calculate_line_coverage_rate()
    assert rate == 0.00


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="SF:test_file.py\nDA:1,1\nDA:2,0\nDA:3,1\nLF:3\nLH:2\nend_of_record",
)
@patch("os.path.exists", return_value=True)
def test_parse_coverage_report_lcov(mock_exists, mock_file):
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="dummy_path.info"
    )
    cov_processor.parse_coverage_report()
    assert cov_processor.file_lines_executed == {"test_file.py": [1, 3]}
    assert cov_processor.file_lines_not_executed == {"test_file.py": [2]}


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="""<?xml version="1.0" ?>
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
</coverage>""",
)
@patch("os.path.exists", return_value=True)
def test_parse_coverage_report_cobertura(mock_exists, mock_file):
    cov_processor = CoverageProcessor(
        coverage_type="cobertura", code_coverage_report_path="dummy_path.xml"
    )
    cov_processor.parse_coverage_report()
    assert cov_processor.file_lines_executed == {"test_file.py": [1, 3]}
    assert cov_processor.file_lines_not_executed == {"test_file.py": [2]}


def test_parse_coverage_report_lcov_file_not_found():
    cov_processor = CoverageProcessor(
        coverage_type="lcov", code_coverage_report_path="non_existent_file.info"
    )
    with pytest.raises(
        FileNotFoundError, match="File 'non_existent_file.info' not found."
    ):
        cov_processor.parse_coverage_report()


def test_parse_coverage_report_cobertura_file_not_found():
    cov_processor = CoverageProcessor(
        coverage_type="cobertura", code_coverage_report_path="non_existent_file.xml"
    )
    with pytest.raises(
        FileNotFoundError, match="File 'non_existent_file.xml' not found."
    ):
        cov_processor.parse_coverage_report()


def test_parse_coverage_report_jacoco_file_not_found():
    cov_processor = CoverageProcessor(
        coverage_type="jacoco", code_coverage_report_path="non_existent_file.xml"
    )
    with pytest.raises(
        FileNotFoundError, match="File 'non_existent_file.xml' not found."
    ):
        cov_processor.parse_coverage_report()
