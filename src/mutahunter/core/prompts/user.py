USER_PROMPT = """
## Abstract Syntax Tree (AST) for Context
```ast
{{ast}}
```

## Response
The output must be a JSON object equivalent to type $Mutants, according to the following Pydantic definitions:
```
class SingleMutant(BaseModel):
    function_name: str = Field(description="The name of the function where the mutation was applied.")
    type: str = Field(description="The type of the mutation operator.")
    description: str = Field(description="Description of the mutation.")
    original_line: str = Field(description="The original line of code before mutation.")
    mutated_line: str = Field(description="The line of code after mutation, including a comment with the mutation description.")

class Mutants(BaseModel):
    changes: List[Change] = Field(description="A list of changes representing the mutants.")
```

## Function Block to Mutate
Lines Covered: {{covered_lines}}. Only mutate lines that are covered by execution.
Note that we have manually added line numbers for each line of code. Do not include line numbers in your mutation. Make sure indentation is preserverd when generating mutants.
```{{language}}
{{function_block}}
```

Generate 1~{{maximum_num_of_mutants_per_function_block}} mutants for the function block provided to you. Ensure that the mutants are semantically different from the original code. Refer to the mutation guidelines provided in the system prompt for mutation focus areas. Each mutant should be a single mutation applied to the original code. Provide the mutated line along with a comment describing the mutation. Ensure that the mutated line is syntactically correct and does not introduce compilation errors.
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
====

To reduce cognitive load, focus on quality over quantity to ensure that the mutants analysis are meaningful and provide valuable insights into the code quality and test coverage. Output your analysis in a clear and concise manner, highlighting the key points for each aspect with less than 300 words.
"""
