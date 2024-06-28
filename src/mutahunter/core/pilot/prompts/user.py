USER_PROMPT = """
You will be provided with the test file as well as the Abstract Syntax Tree (AST) of the source code for contextual understanding. This AST will help you understand the entire source code. Make sure to read the AST before proceeding with the mutation:

The test file path is {{test_file_path}}.
The test file content is:
```{{language}}
{{test_file_content}}
```

```ast
{{ast}}
```

The function block in {{filename}}:
```{{language}}
{{function_block}}
```

# Task:
1. Read the Abstract Syntax Tree of the source code to understand its context.
2. Analyze the provided function block.
3. Introduce a mutation using one of the following mutation operators:

AOD - arithmetic operator deletion
AOR - arithmetic operator replacement
ASR - assignment operator replacement
BCR - break continue replacement
COD - conditional operator deletion
COI - conditional operator insertion
CRP - constant replacement
DDL - decorator deletion
EHD - exception handler deletion
EXS - exception swallowing
IHD - hiding variable deletion
IOD - overriding method deletion
IOP - overridden method calling position change
LCR - logical connector replacement
LOD - logical operator deletion
LOR - logical operator replacement
ROR - relational operator replacement
SCD - super calling deletion
SCI - super calling insert
SIR - slice index remove

Your output must follow the format below:
1. Return the full function block with the mutation included.
2. Describe the mutation using the comment # Mutation: on the specific line where the mutation occurs.
3. unified diff format.
4. unified diff must contain the file path in the first 2 lines.
5. Do not include specific line numbers. Replace line number with so: `@@ ... @@`
6. Do not include any additional information in the output.

{{example_output}}
"""
