USER_PROMPT = """
You will be provided with the {{language}} Abstract Syntax Tree (AST) of the source code for contextual understanding. This AST will help you understand the entire source code. Make sure to read the AST before proceeding with the mutation:

```ast
{{ast}}
```

# Task:
1.	Read the Abstract Syntax Tree of the source code to understand its context.
2.	Mutate the function `{{function_name}}`. Function block is provided below.
3.	Focus on critical areas such as error handling, boundary conditions, and logical branches.
4. Only mutates lines that are covered by execution. Line number starts from 1.
5. Only generate mutant that is in the given function block.
6. Generate only 1 mutation.

Your output must follow:
1.	Follow the example output format.
2.	Inlcude mutant description in the comment.
3.	Output must be in json format, wrapped in triple backticks (```json...```).
4.	Do not include any additional information in the output.

{{example_output}}

# Here is the function block to be mutated:
Covered executed lines: {{covered_lines}}
```{{language}}
{{function_block}}
```
"""
