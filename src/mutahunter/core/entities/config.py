from dataclasses import dataclass
from typing import List, Optional


@dataclass
class MutatorConfig:
    model: str
    api_base: str
    test_command: str
    code_coverage_report_path: Optional[str]
    coverage_type: str
    exclude_files: List[str]
    only_mutate_file_paths: List[str]
    modified_files_only: bool
    extreme: bool


@dataclass
class UnittestGeneratorConfig:
    model: str
    api_base: str
    test_file_path: str
    source_file_path: str
    test_command: str
    code_coverage_report_path: Optional[str]
    coverage_type: str
    target_line_coverage_rate: float
    target_mutation_coverage_rate: float
    max_attempts: int
