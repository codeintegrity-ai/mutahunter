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
    line_number: int = Field(..., description="Line number where the mutation was applied.")
    original_code: str = Field(..., description="The original line of code before mutation. Ensure proper formatting for YAML literal block scalar.
    mutated_code: Ones Field(..., description="The mutated line of code. Please annotate with a {{language}} syntax comment explaining the mutation. Ensure proper formatting for YAML literal block scalar.")

class Mutants(BaseModel):
    source_file: str = Field(..., description="The name of the source file where mutations were applied.")
    mutants: List[SingleMutant] = Field(..., description="A list of SingleMutant instances each representing a specific mutation change.")
```

## Source Code to Mutate, located at {{src_code_file}}
Lines Covered: {{covered_lines}}. Only mutate lines that are covered by execution.
Note that line numbers have been manually added for reference. Do not include these line numbers in your response. Generate mutant for each covered line, focusing on function blocks and critical areas. Do not generate multi-line mutants.
```{{language}}
{{src_code_with_line_num}}
```

## Task
Analyze the source code line by line. For each line number, {{covered_lines}} identify the mutation points based on the guidelines provided. Focus on designated mutation areas. Ensure that these mutations contribute valuable insights into the code quality and test coverage. The output should be organized with line numbers in ascending order.

<example>
```yaml
source_file: {{src_code_file}}
mutants:
   - function_name: ...
      type: ...
      description: ...
      line_number: 2
      original_code: |
         line 1
      mutated_code: |
         line 1 mutated
``` 
</example>
"""


SYSTEM_PROMPT_MUTANT_ANALYSUS = """
You are an AI Agent part of the Software Quality Assurance Team. Your task is to analyze the mutation testing results generated by the mutation testing tool. The tool has identified surviving mutants that were not detected by the existing test cases. Your goal is to provide a detailed analysis of these surviving mutants to improve the test coverage and code quality.
"""
USER_PROMPT_MUTANT_ANALYSIS = """
## Related Source Code:
```
{{source_code}}
```

## Surviving Mutants:
```json
{{surviving_mutants}}
```

Based on the mutation testing results only showing the surviving mutants. Please analyze the following aspects:
## Vulnerable Code Areas:
1. Identify critical sections in the code that are most susceptible to undetected mutations.
2. Rank these areas by severity, considering factors such as frequency of occurrence and potential impact on functionality.
3. For each identified area, cite specific surviving mutant(s) as evidence.

## Test Case Gaps:
1. Provide concrete examples from the surviving mutants JSON for each identified gap.

## Improvement Recommendations:
1. Suggest specific new test cases or modifications to existing ones to target each surviving mutant.
2. Prioritize recommendations based on their potential impact and ease of implementation.
2. Where applicable, provide pseudo-code or test case outlines to illustrate the suggested improvements.

## Code Refactoring Suggestions:
1. Based on the surviving mutants, propose any potential code refactoring that could make the code more robust against mutations.
2. Explain how each refactoring suggestion would help in reducing the number of surviving mutants.

## Format Requirements:
1. Present the final output in concise bullet points.
2. Limit the entire analysis to no more than one page.
3. Ensure each point is supported by specific references to the surviving mutants JSON data.
4. Focus on the most critical findings and high-impact recommendations.
5. Output should be in markdown format for easy readability.
"""
