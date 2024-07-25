LINE_COV_UNITTEST_GENERATOR_USER_PROMPT = """
## Overview
You are a code assistant that accepts a {{ language }} source file and test file. Your goal is to generate additional unit tests to complement the existing test suite and increase line coverage against the source file.

## Guidelines:
- Analyze the provided code to understand its purpose, inputs, outputs, and key logic.
- Brainstorm test cases to fully validate the code and achieve 100% line coverage.
- Ensure the tests cover all scenarios, including exceptions or errors.
- If the original test file has a test suite, integrate new tests consistently in terms of style, naming, and structure.
- Ensure unit tests are independent and do not rely on the system's state or other tests.
- Include clear assertions in each test to validate expected behavior.
- Mock or stub external dependencies to keep tests isolated and repeatable.

## Source File
Here is the source file for which you will write tests, called `{{ source_file_name }}`. Note that line numbers have been manually added for reference. Do not include these line numbers in your response.
```{{ language }}
{{ source_file_numbered }}
```

## Test File
Here is the file that contains the existing tests, called `{{ test_file_name }}.
```{{ language }}
{{ test_file }}
```

## Line Coverage
The following line numbers are not covered by the existing tests. Your goal is to write tests that cover as many of these lines as possible.
{{ lines_to_cover }}

## Response
The output should be formatted as a YAML object that corresponds accurately with the $TestInsertionResponse type as defined in our system's schema. Below are the Pydantic class definitions that outline the structure and details required for the YAML output.
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class InsertionPointMarker(BaseModel):
    class_name: str = Field(..., description="The name of the class after which the test should be inserted.")
    method_name: str = Field(..., description="The last method name after which the test should be inserted in the class.")

class NewTest(BaseModel):
    test_behavior: str = Field(..., description="Short description of the behavior the test covers.")
    lines_to_cover: str = Field(..., description="List of line numbers, currently uncovered, that this specific new test aims to cover.")
    test_name: str = Field(..., description="A short unique test name reflecting the test objective.")
    test_code: str = Field(..., description="A single test function testing the behavioral description.")
    new_imports_code: str = Field(..., description="New imports required for the new test function, or an empty string if none.")
    test_tags: List[str] = Field(..., 
        description="Tags for the test such as 'happy path', 'edge case', 'other'.")

class TestInsertionResponse(BaseModel):
    language: str = Field(..., description="Programming language the tests are written in.")
    insertion_point_marker: InsertionPointMarker = Field(..., description="Indicates where new tests should be inserted in the test file.")
    new_tests: List[NewTest] = Field(..., description="List of new tests to be added.", max_items=5)
```

## Example Output
```yaml
language: ...
insertion_point_marker:
    class_name: ...
    method_name: ...
new_tests:
    - test_behavior: ...
    - lines_to_cover: [1, 2, 3]
    - test_name: ...
    - test_code: |
        ...
    - new_imports_code: |
        ...
    - test_tags: ["happy path", "edge case"]
```

{{ failed_tests_section }}
"""


MUTATION_COV_UNITTEST_GENERATOR_USER_PROMPT = """
## Overview
You are a code assistant that accepts a {{ language }} source file and test file. The current code has a line coverage of {{ line_coverage }}% and a mutation coverage of {{ mutation_coverage }}%.

Your goal is to generate additional unit tests to kill the survived mutants in the source code. To kill a mutant, you need to write a test that triggers the fault introduced by the mutant but passes for the original code.

## Source File
Here is the source file you will be writing tests against, called `{{ source_file_name }}`.
```{{ language }}
{{ source_code }}
```
## Test File
Here is the file that contains the existing tests, called `{{ test_file_name }}`
```{{ language }}
{{ test_file }}
```

## Survived Mutants
Below is a list of survived mutants. Your goal is to write tests that will detect faults based on these mutants.
```json
{{ survived_mutants }}
```

## Response
The output should be formatted as a YAML object that corresponds accurately with the $TestInsertionResponse type as defined in our system's schema. Below are the Pydantic class definitions that outline the structure and details required for the YAML output.
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class InsertionPointMarker(BaseModel):
    class_name: str = Field(..., description="The name of the class after which the test should be inserted.")
    method_name: str = Field(..., description="The last method name after which the test should be inserted in the class.")

class NewTest(BaseModel):
    test_behavior: str = Field(..., description="Short description of the behavior the test covers.")
    mutant_id: str = Field(..., description="The ID of the mutant that the test should kill.")
    test_name: str = Field(..., description="A short unique test name reflecting the test objective.")
    test_code: str = Field(..., description="A single test function testing the behavioral description.")
    new_imports_code: str = Field(..., description="New imports required for the new test function, or an empty string if none.")

class TestInsertionResponse(BaseModel):
    language: str = Field(..., description="Programming language the tests are written in.")
    insertion_point_marker: InsertionPointMarker = Field(..., description="Indicates where new tests should be inserted in the test file.")
    new_tests: List[NewTest] = Field(..., description="List of new tests to be added.", max_items=5)
```

## Example Output
```yaml
language: ...
insertion_point_marker:
    class_name: ...
    method_name: ...
new_tests:
    - test_behavior: ...
    - mutant_id: ...
    - test_name: ...
    - test_code: |
        ...
    - new_imports_code: |
        ...
```

{{ weak_tests_section }}

{{ failed_tests_section }}

## Task
Produce between 1 and 5 new tests that will kill the survived mutants. The new tests should be written in the same style and structure as the existing test suite. Ensure that the tests are independent, cover all scenarios, and include clear assertions to validate expected behavior.
"""

MUTATION_WEAK_TESTS_TEXT = """
## Previous Iterations Passes But Fails to Kill Mutants
Below is a list of tests that pass but fail to kill the mutants. Do not generate the same tests again, and take these tests into account when generating new tests.
```json
{{ weak_tests }}
```
"""

FAILED_TESTS_TEXT = """
## Previous Iterations Failed Tests
Below is a list of failed tests that you generated in previous iterations. Do not generate the same tests again, and take the failed tests into account when generating new tests.
```json
{{ failed_test }}
```
"""

REPORT_PROMPT = """
## Overview
You are a code assistant that accepts a {{ language }} source file and test file. Your goal is to analyze the existing test suite and generate a report that provides insights into the quality and effectiveness of the tests based on the surviving mutants and failed tests.

Here is the source file that you will be writing tests against, called `{{ source_file_name }}`.
```{{ language }}
{{ source_code }}
```
## Test File
Here is the file that contains the existing tests, called `{{ test_file }}`
```{{ language }}
{{ test_code }}
```

## Survived Mutants
{{survived_mutants_section}}

Based on the surviving mutants that could not be killed by the existing tests, there might be bugs in the source code or weaknesses in the test file. Please identify potential bugs in the source code or weaknesses in the test file. The report must be in markdown format and no more than 400 words. Use concise bullet points to summarize the key insights and recommendations.
"""
