USER_PROMPT = """
You will be provided with the {{language}} test file as well as the Abstract Syntax Tree (AST) of the source code for contextual understanding. This AST will help you understand the entire source code. Make sure to read the AST before proceeding with the mutation:

The test file path is {{test_file_path}}.
The test file content is:
```{{language}}
{{test_file_content}}
```

```ast
{{ast}}
```

The function block in {{filename}}:
Covered executed lines: {{covered_lines}}
```{{language}}
{{function_block}}
```

# Task:
1.	Read the Abstract Syntax Tree of the source code to understand its context.
2.	Analyze the provided function block to identify a mutation that will test the robustness of the test suite.
3.	Focus on critical areas such as error handling, boundary conditions, and logical branches.
4.	Related multi-step mutations are allowed if they are logically connected and can expose weaknesses.
5. Only mutates lines that are covered by execution. Line number starts from 1.

Your output must follow the format below:
1.	Return the full function block with the mutation included.
2.	Describe the mutation using a comment in {{language}} syntax on the specific line where the mutation occurs.
3.	Unified diff format.
4.	Unified diff must contain the file path in the first 2 lines.
5.	Do not include specific line numbers. Replace line number with so: @@ ... @@
6.	Do not include any additional information in the output.

{{example_output}}
"""
