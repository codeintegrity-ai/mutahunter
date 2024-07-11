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

## Output
The output must be in JSON format, wrapped in triple backticks (json...), and adhere to the following Pydantic definitions.
```
{
    "changes": [
        {
            'function_name': "divide",
            "type": "DivisionByZero",
            'description': "Added division by zero check to prevent division by zero error.",
            'original_line': "    return a / b",
            'mutated_line': "    if (b == 0) throw new ArithmeticException("Division by zero"); return a / b; // Mutant: Added division by zero check"
        }
    ]
}
```

## Function Block to Mutate
Lines Covered: {{covered_lines}}. Only mutate lines that are covered by execution.
Note that we have manually added line numbers for each line of code. Do not include line numbers in your mutation. Make sure indentation is preserverd when generating mutants.
```{{language}}
{{function_block}}
```

Generate 1~{{maximum_num_of_mutants_per_function_block}} mutants for the function block provided to you. Ensure that the mutants are semantically different from the original code. Focus on critical areas such as error handling, boundary conditions, and logical branches.
"""
