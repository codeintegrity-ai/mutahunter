import pytest
from unittest.mock import Mock, patch
from unittest.mock import mock_open
import xml.etree.ElementTree as ET
from mutahunter.core.analyzer import Analyzer


@pytest.fixture
def config():
    return {
        "language": "python",
        "code_coverage_report_path": "path/to/coverage_report.xml",
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
    assert analyzer.check_syntax(source_code) is True


def test_check_syntax_invalid(analyzer):
    source_code = "def invalid_syntax(\n    pass"
    assert analyzer.check_syntax(source_code) is False


def test_find_function_blocks_nodes(analyzer):
    source_code = b"""
    def func1():
        pass

    def func2():
        pass
    """

    function_blocks = analyzer.find_function_blocks_nodes(source_code)
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
        covered_blocks = analyzer.get_covered_function_blocks(executed_lines, filename)
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


def test_traverse_ast_stop(analyzer):
    node_mock = Mock()
    node_mock.children = []

    def callback(node):
        return True

    result = analyzer.traverse_ast(node_mock, callback)
    assert result is True
