USER_PROMPT = """
## Abstract Syntax Tree (AST) for Context
```ast
{{ast}}
```

## Response
The output must be a YAML object equivalent to type $Mutants, according to the following Pydantic definitions:
```python
class SingleMutant(BaseModel):
    function_name: str = Field(description="The name of the function where the mutation was applied.")
    type: str = Field(description="The type of the mutation operator.")
    description: str = Field(description="Description of the mutation.")
    original_line: str = Field(description="The original line of code before mutation. Do not include the line number.")
    mutated_line: str = Field(description="The line of code after mutation, including a comment with the mutation description. Do not include the line number.")

class Mutants(BaseModel):
    changes: List[Change] = Field(description="A list of changes representing the mutants.")
```

## Function Block to Mutate
Lines Covered: {{covered_lines}}. Only mutate lines that are covered by execution.
Note that line numbers have been manually added for reference. Do not include these line numbers in your response.
```{{language}}
{{function_block}}
```

## Example Output
```yaml
changes:
  - function_name: "... function name ..."
    type: "... the type of mutant and how it affects the code ..."
    description: "... clear and concise description of the mutation and the reason for its application ..."
    original_line: '     ... original code (Do not include lin number) ...}'
    mutated_line: '     ... mutated code (Do not include lin number)...'
```


Generate 1~{{maximum_num_of_mutants_per_function_block}} mutants for the function block provided to you. Refer to the mutation guidelines provided in the system prompt for mutation focus areas. The Response should be only a valid YAML object, without any introduction text or follow-up text.
"""


MUTANT_ANALYSIS = """
## Related Source Code:
```
{{source_code}}
```

## Surviving Mutants:
```json
{{surviving_mutants}}
```

Based on the mutation testing results only showing the surviving mutants. Please analyze the following aspects:
- Vulnerable Code Areas: Identification of critical areas in the code that are most vulnerable based on the surviving mutants.
- Test Case Gaps: Analysis of specific reasons why the existing test cases failed to detect these mutants.
- Improvement Recommendations: Suggestions for new or improved test cases to effectively target and eliminate the surviving mutants.

## Example Output:
<example>
### Vulnerable Code Areas
**File:** `src/main/java/com/example/BankAccount.java`
**Location:** Line 45
**Description:** The method `withdraw` does not properly handle negative inputs, leading to potential incorrect account balances.

### Test Case Gaps
**File:** `src/test/java/com/example/BankAccountTest.java`
**Location:** Test method `testWithdraw`
**Reason:** Existing test cases do not cover edge cases such as negative withdrawals or withdrawals greater than the account balance.

### Improvement Recommendations
**New Test Cases Needed:**
1. **Test Method:** `testWithdrawNegativeAmount`
   - **Description:** Add a test case to check behavior when attempting to withdraw a negative amount.
2. **Test Method:** `testWithdrawExceedingBalance`
   - **Description:** Add a test case to ensure proper handling when withdrawing an amount greater than the current account balance.
3. **Test Method:** `testWithdrawBoundaryConditions`
   - **Description:** Add boundary condition tests for withdrawal amounts exactly at zero and exactly equal to the account balance.
</example>

To reduce cognitive load, focus on quality over quantity to ensure that the mutants analysis are meaningful and provide valuable insights into the code quality and test coverage. Output your analysis in a clear and concise manner, highlighting the key points for each aspect with less than 300 words.
"""


TEST_GEN_USER_PROMPT = """
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
The output must be a JSON object wrapped in json. Do not generate more than 5 tests in a single response.
```json
{
  "language": {{ language }},
  "insertion_point_marker": {
    "class_name": "The name of the class after which the test should be inserted.",
    "method_name": "The last method name after which the test should be inserted in the class."
  },
  "new_tests": [
    {
      "test_behavior": "Short description of the behavior the test covers.",
      "lines_to_cover": "List of line numbers, currently uncovered, that this specific new test aims to cover.",
      "test_name": "A short unique test name reflecting the test objective.",
      "test_code": "A single test function testing the behavior described in 'test_behavior'. Write it as part of the existing test suite, using existing helper functions, setup, or teardown code.",
      "new_imports_code": "New imports required for the new test function, or an empty string if none. Use 'import ...' lines if relevant.",
      "test_tags": ["happy path", "edge case", "other"]
    }
  ]
}
```
{{ failed_tests_section }}
"""

MUTATION_TEST_PROMPT = """
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
The output must be a JSON object wrapped in json. Do not generate more than 5 tests in a single response.
``json
{
  "language": {{ language }},
  "insertion_point_marker": {
    "class_name": "The name of the class after which the test should be inserted.",
    "method_name": "The last method name after which the test should be inserted in the class."
  },
  "new_tests": [
    {
      "test_behavior": "Short description of the behavior the test covers.",
      "mutant_id": "The ID of the mutant this test aims to kill.",
      "test_name": "A short unique test name reflecting the test objective.",
      "test_code": "A single test function that tests the behavior described in 'test_behavior'. Write it as part of the existing test suite, using existing helper functions, setup, or teardown code.",
      "new_imports_code": "New imports required for the new test function, or an empty string if none. Use 'import ...' lines if relevant.",
      "test_tags": ["happy path", "edge case", "other"]
    }
  ]
}
```
{{ weak_tests_section }}

{{ failed_tests_section }}
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
