MUTATION_COV_UNITTEST_GENERATOR_USER_PROMPT = """
## Overview
You are a code assistant that accepts a {{ language }} source code and test file. 

Your goal is to generate additional unit tests to kill the survived mutants. To kill a mutant, you need to write a test that triggers the fault introduced by the mutant but passes for the original code.

## Source Code
Here is the source code you will be writing tests against, called `{{ source_file_name }}`.
```{{ language }}
{{ source_code }}
```
## Test File
Here is the file that contains the existing tests, called `{{ test_file_name }}`
```{{ language }}
{{ test_file }}
```

## Survived Mutants
Below is a list of survived mutants.
```json
{{ survived_mutants }}
```

## Response
The output should be formatted as a YAML object that corresponds accurately with the $NewTests type as defined in our system's schema. Below are the Pydantic class definitions that outline the structure and details required for the YAML output.
```python
class TestCase(BaseModel):
    test_behavior: str = Field(..., description="Short description of the behavior the test covers.")
    mutant_id: str = Field(..., description="The ID of the mutant that the test should kill.")
    test_name: str = Field(..., description="A short unique test name reflecting the test objective.")
    test_code: str = Field(..., description="A single test function testing the behavioral description.Full test code, following the existing test style.")
    new_imports_code: str = Field(..., description="New imports required for the new test function, or an empty string if none.")

class NewTests(BaseModel):
    test_cases: List[TestCase] = Field(..., description="List of new tests to be added.", max_items=5)
```

{{ weak_tests_section }}

{{ failed_tests_section }}

## Task
For each 
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
