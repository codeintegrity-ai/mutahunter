import xml.etree.ElementTree as ET
from unittest.mock import Mock, mock_open, patch

import pytest

from mutahunter.core.analyzer import Analyzer


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
def function_blocks():
    return [
        Mock(start_point=(4, 0), end_point=(8, 0)),  # This block should be covered
        Mock(
            start_point=(9, 0), end_point=(14, 0)
        ),  # This block should be partially covered
        Mock(
            start_point=(15, 0), end_point=(20, 0)
        ),  # This block should not be covered
    ]


@pytest.fixture
def function_blocks_xml_content():
    return """<?xml version="1.0" ?>
    <coverage line-rate="0.8">
        <packages>
            <package>
                <classes>
                    <class filename="test_file.py">
                        <lines>
                            <line number="5" hits="1"/>
                            <line number="6" hits="1"/>
                            <line number="10" hits="1"/>
                        </lines>
                    </class>
                </classes>
            </package>
        </packages>
    </coverage>"""


@patch("xml.etree.ElementTree.parse")
@patch("builtins.open", new_callable=mock_open)
@patch.object(Analyzer, "get_function_blocks")
def test_get_covered_function_blocks(
    mock_get_function_blocks,
    mock_open,
    mock_parse,
    function_blocks,
    function_blocks_xml_content,
):
    source_file_path = "test_file.py"
    mock_file_content = "def test_func():\n    pass\n"
    mock_open.return_value.read.return_value = mock_file_content
    mock_parse.return_value = ET.ElementTree(ET.fromstring(function_blocks_xml_content))
    mock_get_function_blocks.return_value = function_blocks

    analyzer = Analyzer()
    covered_blocks, covered_block_executed_lines = analyzer.get_covered_function_blocks(
        executed_lines=[5, 6, 10], source_file_path=source_file_path
    )

    # Assertions
    assert len(covered_blocks) == 2
    assert covered_block_executed_lines == [[1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 6]]


@patch("xml.etree.ElementTree.parse")
@patch("builtins.open", new_callable=mock_open)
@patch.object(Analyzer, "get_method_blocks")
def test_get_covered_method_blocks(
    mock_get_method_blocks,
    mock_open,
    mock_parse,
    function_blocks,
    function_blocks_xml_content,
):
    source_file_path = "test_file.py"
    mock_file_content = "def test_method():\n    pass\n"
    mock_open.return_value.read.return_value = mock_file_content
    mock_parse.return_value = ET.ElementTree(ET.fromstring(function_blocks_xml_content))
    mock_get_method_blocks.return_value = function_blocks

    analyzer = Analyzer()
    covered_blocks, covered_block_executed_lines = analyzer.get_covered_method_blocks(
        executed_lines=[5, 6, 10], source_file_path=source_file_path
    )

    # Assertions
    assert len(covered_blocks) == 2
    assert covered_block_executed_lines == [[1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 6]]


@patch("xml.etree.ElementTree.parse")
@patch("builtins.open", new_callable=mock_open)
@patch("mutahunter.core.analyzer.filename_to_lang", return_value="python")
@patch("mutahunter.core.analyzer.get_parser")
def test_check_syntax(
    mock_get_parser,
    mock_filename_to_lang,
    mock_open,
    mock_parse,
    cobertura_xml_content,
):
    source_code = "def foo():\n    pass"
    source_file_path = "test_file.py"
    mock_open.return_value.read.return_value = source_code
    mock_parse.return_value = ET.ElementTree(ET.fromstring(cobertura_xml_content))
    mock_parser = mock_get_parser.return_value
    mock_tree = Mock()
    mock_tree.root_node.has_error = False
    mock_parser.parse.return_value = mock_tree

    analyzer = Analyzer()
    result = analyzer.check_syntax(source_file_path, source_code)

    # Assertions
    assert result is True
    mock_filename_to_lang.assert_called_once_with(source_file_path)
    mock_parser.parse.assert_called_once_with(bytes(source_code, "utf8"))


@patch("xml.etree.ElementTree.parse")
@patch("builtins.open", new_callable=mock_open)
def test_get_covered_blocks(mock_open, mock_parse, cobertura_xml_content):
    # Define the executed lines
    executed_lines = [5, 6, 10]

    # Mock blocks to be returned
    mock_blocks = [
        Mock(start_point=(4, 0), end_point=(8, 0)),  # This block should be covered
        Mock(
            start_point=(9, 0), end_point=(14, 0)
        ),  # This block should be partially covered
        Mock(
            start_point=(15, 0), end_point=(20, 0)
        ),  # This block should not be covered
    ]

    # Mock the file read operation for the coverage report
    mock_file_content = "def test_func():\n    pass\n"
    mock_open.return_value.read.return_value = mock_file_content
    mock_parse.return_value = ET.ElementTree(ET.fromstring(cobertura_xml_content))

    analyzer = Analyzer()
    covered_blocks, covered_block_executed_lines = analyzer._get_covered_blocks(
        mock_blocks, executed_lines
    )

    # Assertions
    assert len(covered_blocks) == 2
    assert covered_block_executed_lines == [
        [1, 2, 3, 4, 5],
        [1, 2, 3, 4, 5, 6],
    ]


@patch("xml.etree.ElementTree.parse")
@patch("builtins.open", new_callable=mock_open)
def test_read_source_file(mock_open, mock_parse, cobertura_xml_content):
    source_file_path = "test_file.py"
    source_code = b"def foo():\n    pass"
    mock_open.return_value.read.return_value = source_code
    mock_parse.return_value = ET.ElementTree(ET.fromstring(cobertura_xml_content))

    analyzer = Analyzer()
    result = analyzer._read_source_file(source_file_path)
    mock_open.assert_called_once_with(source_file_path, "rb")

    # Assertions
    assert result == source_code


@patch("xml.etree.ElementTree.parse")
@patch("mutahunter.core.analyzer.Analyzer._find_blocks_nodes")
def test_find_method_blocks_nodes(
    mock_find_blocks_nodes, mock_parse, cobertura_xml_content
):
    source_code = b"def foo():\n    pass"
    source_file_path = "test_file.py"
    mock_parse.return_value = ET.ElementTree(ET.fromstring(cobertura_xml_content))

    analyzer = Analyzer()
    analyzer.find_method_blocks_nodes(source_file_path, source_code)
    mock_find_blocks_nodes.assert_called_once_with(
        source_file_path, source_code, ["if_statement", "loop", "return"]
    )
