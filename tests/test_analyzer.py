import xml.etree.ElementTree as ET
from unittest.mock import Mock, mock_open, patch

import pytest

from mutahunter.core.analyzer import Analyzer


@pytest.fixture
def config():
    return {
        "code_coverage_report_path": "path/to/coverage_report.xml",
        "coverage_type": "cobertura",
        "test_command": "pytest",
    }


@pytest.fixture
def analyzer(config):
    with patch.object(
        Analyzer,
        "parse_coverage_report_cobertura",
        return_value={"test_file.py": [1, 3]},
    ):
        return Analyzer(config)


def test_dry_run_success(analyzer):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        try:
            analyzer.dry_run()
        except Exception:
            pytest.fail("dry_run() raised Exception unexpectedly!")


def test_dry_run_failure(analyzer):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        with pytest.raises(
            Exception,
            match="Tests failed. Please ensure all tests pass before running mutation testing.",
        ):
            analyzer.dry_run()


def test_check_syntax_valid(analyzer):
    source_code = "def valid_syntax():\n    pass"
    source_file_path = "tets_file.py"
    assert (
        analyzer.check_syntax(
            source_file_path=source_file_path, source_code=source_code
        )
        is True
    )


def test_check_syntax_invalid(analyzer):
    source_code = "def invalid_syntax(\n    pass"
    source_file_path = "tets_file.py"
    assert (
        analyzer.check_syntax(
            source_file_path=source_file_path, source_code=source_code
        )
        is False
    )


def test_find_function_blocks_nodes(analyzer):
    source_code = b"""
    def func1():
        pass

    def func2():
        pass
    """
    source_file_path = "test_file.py"

    function_blocks = analyzer.find_function_blocks_nodes(source_file_path, source_code)
    assert len(function_blocks) == 2
    assert function_blocks[0].type == "function_definition"
    assert function_blocks[1].type == "function_definition"


def test_get_function_blocks(analyzer):
    filename = "test_file.py"
    source_code = b"def func():\n    pass\n"

    with patch("builtins.open", mock_open(read_data=source_code)):
        with patch.object(
            analyzer, "find_function_blocks_nodes", return_value=["mock_function_block"]
        ):
            function_blocks = analyzer.get_function_blocks(filename)
            assert function_blocks == ["mock_function_block"]


def test_get_covered_function_blocks(analyzer):
    executed_lines = [2, 3, 4, 5, 6]
    filename = "test_file.py"

    function_block_mock = Mock()
    function_block_mock.start_point = (1, 0)
    function_block_mock.end_point = (5, 0)

    with patch.object(
        analyzer, "get_function_blocks", return_value=[function_block_mock]
    ):
        covered_blocks, covered_function_executed_lines = (
            analyzer.get_covered_function_blocks(executed_lines, filename)
        )
        assert len(covered_blocks) == 1
        assert covered_blocks[0] == function_block_mock


def test_parse_coverage_report_cobertura(config):
    xml_content = """<?xml version="1.0" ?>
    <coverage>
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

    with patch("xml.etree.ElementTree.parse") as mock_parse:
        mock_parse.return_value.getroot.return_value = ET.fromstring(xml_content)
        analyzer = Analyzer(config)
        result = analyzer.parse_coverage_report_cobertura()
        assert result == {"test_file.py": [1, 3]}


def test_parse_coverage_report_jacoco(config):
    xml_content = """<?xml version="1.0" ?>
    <report>
        <package name="com/example">
            <sourcefile name="Example.java">
                <line nr="1" mi="0" ci="1"/>
                <line nr="2" mi="1" ci="0"/>
                <line nr="3" mi="0" ci="1"/>
            </sourcefile>
        </package>
    </report>"""

    with patch("xml.etree.ElementTree.parse") as mock_parse:
        mock_parse.return_value.getroot.return_value = ET.fromstring(xml_content)
        config["coverage_type"] = "jacoco"
        analyzer = Analyzer(config)
        result = analyzer.parse_coverage_report_jacoco()
        assert result == {"src/main/java/com/example/Example.java": [1, 3]}


def test_analyzer_init_invalid_coverage_type():
    config = {
        "code_coverage_report_path": "path/to/coverage_report.xml",
        "coverage_type": "invalid",
        "test_command": "pytest",
    }
    with pytest.raises(
        Exception,
        match="Invalid coverage tool. Please specify either 'cobertura' or 'jacoco'.",
    ):
        Analyzer(config)


def test_analyzer_init_jacoco():
    config = {
        "code_coverage_report_path": "path/to/coverage_report.xml",
        "coverage_type": "jacoco",
        "test_command": "pytest",
    }
    with patch.object(
        Analyzer,
        "parse_coverage_report_jacoco",
        return_value={"test_file.py": [1, 3]},
    ):
        analyzer = Analyzer(config)
        assert analyzer.file_lines_executed == {"test_file.py": [1, 3]}


def test_get_function_blocks_large_file(analyzer):
    large_source_code = b"def func1():\n    pass\n" * 50
    with patch("builtins.open", mock_open(read_data=large_source_code)):
        function_blocks = analyzer.get_function_blocks("test_file.py")
        assert len(function_blocks) == 50


def test_parse_coverage_report_lcov(config):
    lcov_content = "SF:test_file.py\nDA:1,1\nDA:2,0\nDA:3,1\nend_of_record\n"

    with patch("builtins.open", mock_open(read_data=lcov_content)):
        config["coverage_type"] = "lcov"
        analyzer = Analyzer(config)
        result = analyzer.parse_coverage_report_lcov()
        assert result == {"test_file.py": [1, 3]}
