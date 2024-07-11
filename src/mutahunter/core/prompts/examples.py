"""
This module contains example output templates for different 
programming languages supported by MutaHunter.
"""

GO_EXAMPLE_OUTPUT = """
Output Format:
```json
{
    "changes": [
        {
            "type": "Off-by-One Error",
            "description": "Changed the condition from i < j to i <= j to simulate off-by-one error.",
            "context_before": "        runes := []rune(s)",
            "original_line": "       for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {",
            "mutated_line": "       for i, j := 0, len(runes)-1; i <= j; i, j = i+1, j-1 { // Mutation: Changed the condition from i < j to i <= j to simulate off-by-one error.",
            "context_after": "}",
        }
    ]
}
```
"""

JAVASCRIPT_EXAMPLE_OUTPUT = """
Output Format:
```json
{
    "changes": [
        {
            "type": "Boundary Condition",
            "description": "Simulate missing user data by setting default values if user properties are undefined.",
            "context_before": "                        <div class="col-md-9">,
            'original_line': "                        <span class=\"badge badge-primary\"> Public Repos: ${user.public_repos}</span>",
            "mutated_line": "                        <span class=\"badge badge-primary\"> Public Repos: ${user.public_repos || 'N/A'}</span>  // Mutation: Set default value if user.public_repos is undefined.",
            "context_after": "                        <span class=\"badge badge-secondary\"> Public Gists: ${user.public_gists}</span>"
        }
    ]
}
```
"""

PYTHON_EXAMPLE_OUTPUT = """
Output Format:
```json
{
    "changes": [
        {
            "type": "Floating-Point Precision Error",
            "description": "Convert inputs to floats to simulate floating-point precision error.",
            "context_before": "         \"\"\"Return the sum of a and b.\"\"\"",
            "original_line": "        return a + b",
            "mutated_line": "        return float(a) + float(b) # Mutation: Convert inputs to floats to simulate floating-point precision error.",
            "context_after": ""
        }
    ]
}
```
"""

JAVA_EXAMPLE_OUTPUT = """
Output Format:
```json
{
    "changes": [
        {
            "type": "Boundary Condition",
            "description": "Added division by zero check.",
            "context_before": "    public double divide(double a, double b) {",
            "original_line": "        return a / b;",
            "mutated_line": "        if (b == 0) { throw new ArithmeticException(\"Division by zero\"); } return a / b; // Mutation: Added division by zero check",
            "context_after": "    }"
        },
        {
            "type": "Arithmetic Operator Replacement",
            "description": "Changed division to multiplication using AOR (Arithmetic Operator Replacement)",
            "context_before": "    public double divide(double a, double b) {",
            "original_line": "        return a / b;",
            "mutated_line": "        return a * b; // Mutation: Changed division to multiplication using AOR (Arithmetic Operator Replacement)",
            "context_after": "    }"
        }
    ]
}
```
"""
