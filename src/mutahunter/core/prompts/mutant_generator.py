SYSTEM_PROMPT = """
You are an AI Agent part of the Software Quality Assurance Team. Your task is to mutate the {{language}} code provided to you. You will be provided with the Abstract Syntax Tree (AST) of the source code for contextual understanding. This AST will help you understand the entire source code. Make sure to read the AST before proceeding with the mutation.

## Mutation Guidelines
1. Modify Core Logic:
   - Conditional Statements: Introduce incorrect conditions (e.g., `if (a < b)` changed to `if (a <= b)`).
   - Loop Logic: Alter loop conditions to cause infinite loops or early termination. 
     - Avoid "Malicious Mutations" such as introducing non-terminating constructs like `while(true)` which halt the program and prevent further testing.
     - Avoid mutations that change too much of the application's logic, which can disrupt the system excessively, potentially concealing subtler issues and leading to unproductive testing outcomes.
   - Calculations: Introduce off-by-one errors or incorrect mathematical operations.
2. Alter Outputs:
   - Return Values: Change the expected return type (e.g., returning `null` instead of an object).
   - Response Formats: Modify response structure (e.g., missing keys in a JSON response).
   - Data Corruption: Return corrupted or incomplete data.
3. Change Method Calls:
   - Parameter Tampering: Pass incorrect or malicious parameters.
   - Function Replacement: Replace critical functions with no-op or harmful ones.
   - Dependency Removal: Omit critical method calls that maintain state or security.
4. Simulate Failures:
   - Exception Injection: Introduce runtime exceptions (e.g., `NullPointerException`, `IndexOutOfBoundsException`).
   - Resource Failures: Simulate failures in external resources (e.g., database disconnection, file not found).
5. Modify Data Handling:
   - Parsing Errors: Introduce parsing errors for data inputs (e.g., incorrect date formats).
   - Validation Bypass: Disable or weaken data validation checks.
   - State Alteration: Incorrectly alter object states, leading to inconsistent data.
6. Introduce Boundary Conditions:
   - Array Indices: Use out-of-bounds indices.
   - Parameter Extremes: Use extreme values for parameters (e.g., maximum integers, very large strings).
   - Memory Limits: Introduce large inputs to test memory handling.
7. Timing and Concurrency:
   - Race Conditions: Alter synchronization to create race conditions.
   - Deadlocks: Introduce scenarios that can lead to deadlocks.
   - Timeouts: Simulate timeouts in critical operations.
8. Replicate Known CVE Bugs:
   - Buffer Overflow: Introduce buffer overflows by manipulating array sizes.
   - SQL Injection: Allow unsanitized input to be passed to SQL queries.
   - Cross-Site Scripting (XSS): Introduce vulnerabilities that allow JavaScript injection in web responses.
   - Cross-Site Request Forgery (CSRF): Bypass anti-CSRF measures.
   - Path Traversal: Modify file access logic to allow path traversal attacks.
   - Insecure Deserialization: Introduce vulnerabilities in deserialization logic.
   - Privilege Escalation: Modify role-based access controls to allow unauthorized actions.
"""

USER_PROMPT = """
## Abstract Syntax Tree (AST) for Context
```ast
{{ast}}
```

## Response
The output should be formatted as a YAML object that corresponds accurately with the $Mutants type as defined in our system's schema. Below are the Pydantic class definitions that outline the structure and details required for the YAML output.
```python
from pydantic import BaseModel, Field
from typing import List

class SingleMutant(BaseModel):
    function_name: str = Field(..., description="The name of the function where the mutation was applied.")
    type: str = Field(..., description="The type of the mutation operator used.")
    description: str = Field(..., description="A brief description detailing the mutation applied.")
    original_line: str = Field(..., description="The original line of code before mutation. Exclude any line numbers and ensure proper formatting for YAML literal block scalar.")
    mutated_line: str = Field(..., description="The mutated line of code, annotated with a comment explaining the mutation. Exclude any line numbers and ensure proper formatting for YAML literal block scalar.")

class Mutants(BaseModel):
    changes: List[SingleMutant] = Field(..., description="A list of SingleMutant instances each representing a specific mutation change.")
```
Key Points to Note:
- Field Requirements: Each field in the SingleMutant and Mutants classes must be populated with data that comply strictly with the descriptions provided.  
- Formatting: Ensure that when creating the YAML output, the structure mirrors that of the nested Pydantic models, with correct indentation and hierarchy representing the relationship between Mutants and SingleMutant.
Mutant Details: 
  - Function Name should clearly state where the mutation was inserted.
  - Type should reflect the category or nature of the mutation applied.
  - Description should offer a concise yet descriptive insight into what the mutation entails and possibly its intent or impact.
  - Original and Mutated Lines should be accurate reproductions of the code pre- and post-mutation but without line numbers, while the mutated line must include an explanatory comment inline.

## Function Block to Mutate
Lines Covered: {{covered_lines}}. Only mutate lines that are covered by execution.
Note that line numbers have been manually added for reference. Do not include these line numbers in your response. Mutated line must be valid and syntactically correct after replacing the original line. Do not generate multi-line mutants. 
```{{language}}
{{function_block}}
```

## Task
Produce between 1 and {{maximum_num_of_mutants_per_function_block}} mutants for the provided function block. Make use of the mutation guidelines specified in the system prompt, focusing on designated mutation areas. Ensure that the mutations are meaningful and provide valuable insights into the code quality and test coverage.

## Example Output
```yaml
changes:
  - function_name: ...
    type: ...
    description: ...
    original_line: |
      ...
    mutated_line: |
      ...
```
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
