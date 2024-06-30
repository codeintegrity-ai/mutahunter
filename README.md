<div align="center">
  <h1>Mutahunter</h1>

  Open-Source Language Agnostic LLM-based Mutation Testing for Automated Software Testing
  
  Maintained by [CodeIntegrity](https://www.codeintegrity.ai). Anyone is welcome to contribute. 🌟

  [![GitHub license](https://img.shields.io/badge/License-AGPL_3.0-blue.svg)](https://github.com/yourcompany/mutahunter/blob/main/LICENSE)
  [![Twitter](https://img.shields.io/twitter/follow/CodeIntegrity)](https://twitter.com/CodeIntegrity)
  [![Unit Tests](https://github.com/codeintegrity-ai/mutahunter/actions/workflows/test.yaml/badge.svg)](https://github.com/codeintegrity-ai/mutahunter/actions/workflows/test.yaml)
  <a href="https://github.com/codeintegrity-ai/mutahunter/commits/main">
  <img alt="GitHub" src="https://img.shields.io/github/last-commit/codeintegrity-ai/mutahunter/main?style=for-the-badge" height="20">
  </a>
</div>

<div align="center">
  <video src="https://github.com/codeintegrity-ai/mutahunter/assets/37044660/cca8a41b-b97e-4ce1-806d-e53d475d4226"></video>
</div>

## Table of Contents

- [Overview](#overview)
- [Installation and Usage](#installation-and-usage)
- [Roadmap](#roadmap)

## Overview

If you don't know what mutation testing is, you must be living under a rock! 🪨

Mutation testing is a way to verify how good your test cases are. It involves creating small changes, or "mutants," in the code and checking if the test cases can catch these changes. Line coverage only tells you how much of the code has been executed, not how well it's been tested. We all know line coverage is limited.

Mutahunter leverages LLM models to inject context-aware faults into your codebase. As the first AI-based mutation testing tool, it surpasses traditional “dumb” AST-based methods. Mutahunter’s AI-driven approach provides full contextual understanding of the entire codebase, enabling it to identify and inject mutations that closely resemble real vulnerabilities. This ensures comprehensive and effective testing, significantly enhancing software security and quality.

Mutation testing is used by big tech companies like [Google](https://research.google/pubs/state-of-mutation-testing-at-google/) to ensure the robustness of their test suites. With Mutahunter, we want other companies and developers to use this powerful tool to enhance their test suites and improve software quality.

Examples:
- [Go Example](/examples/go_webservice/)
- [Java Example](/examples/java_maven/)
- [JavaScript Example](/examples/js_vanilla/)
- [Python FastAPI Example](/examples/python_fastapi/)

Feel free to add more examples! ✨

## Why you should use Mutahunter

1. **AI-Driven Mutation Testing:** Mutahunter leverages advanced LLM models to inject context-aware faults into your codebase, ensuring comprehensive mutation testing.
2. **Language Agnostic:** Mutahunter supports various programming languages and can be extended to work with any language that provides a coverage report in **Cobertura** XML format, **Jacoco** XML format, and **lcov** format.
3. **Enhanced Mutation Coverage Report:** Mutahunter provides detailed mutation coverage reports, highlighting the effectiveness of your test suite and identifying potential weaknesses.

## Installation and Usage

### Requirements

- LLM API Key (OpenAI, Anthropic, self-hosted, etc): Follow the instructions [here](https://litellm.vercel.app/docs/) to set up your environment.
- **Cobertura XML**, **Jacoco XML**, or **lcov** code coverage report for a specific test file.
- Python to install the Mutahunter package. **Versions 3.11+** are supported.

#### Python Pip 

To install the Python Pip package directly via GitHub:

```bash
# Work with GPT-4o on your repo. See litellm for other models.
export OPENAI_API_KEY=your-key-goes-here

# Or, work with Anthropic's models. See litellm for other models.
export ANTHROPIC_API_KEY=your-key-goes-here

pip install git+https://github.com/codeintegrity-ai/mutahunter.git
```

### How to Execute Mutahunter

To use Mutahunter, you first need a **Cobertura XML**, **Jacoco XML**, or **lcov** code coverage report of a specific test file. Currently, mutation testing works per test file level, not the entire test suite. Therefore, you need to get the coverage report per test file.

Example command to run Mutahunter on a Python FastAPI [application](/examples/python_fastapi/):

```bash
mutahunter run --test-command "pytest test_app.py" --test-file-path "test_app.py" --code-coverage-report-path "coverage.xml" --only-mutate-file-paths "app.py"
```

The mutahunter run command has the following options:

```plaintext
Options:
  --model <MODEL>
      Description: LLM model to use for mutation testing. We use LiteLLM to call the model.
      Default: `gpt-4o`
      Required: Yes
      Example: `--model gpt-4o`

  --test-command <COMMAND>
      Description: The command used to execute the tests. Specify a single test file to run the tests on.
      Required: Yes
      Example: `--test-command pytest test_app.py`

  --code-coverage-report-path <PATH>
      Description: Path to the code coverage report of the test suite.
      Required: Yes
      Example: `--code-coverage-report-path /path/to/coverage.xml`
  
  --coverage-type <TYPE>
      Description: Type of coverage report. Currently supports `cobertura` and `jacoco`.
      Required: Yes
      Example: `--coverage-type cobertura`

  --test-file-path <PATH>
      Description: Path to the test file to run the tests on.
      Required: Yes
      Example: `--test-file-path /path/to/test_file.py`

  --exclude-files <FILES>
      Description: Files to exclude from analysis.
      Required: No
      Example: `--exclude-files file1.py file2.py`

  --only-mutate-file-paths <FILES>
      Description: Specifies which files to mutate. This is useful when you want to focus on specific files and it makes the mutations faster!
      Required: No
      Example: `--only-mutate-file-paths file1.py file2.py`
```

#### Mutation Testing Report

Check the logs directory to view the report:

- `mutants_killed.json` - Contains the list of mutants that were killed by the test suite.
- `mutants_survived.json` - Contains the list of mutants that survived the test suite.
- `mutation_coverage.json` - Contains the mutation coverage report.
- `test_suite_report.md` - Contains a detailed report of identified weaknesses in the test suite and potential bugs not caught by the test suite.

An example survived mutant information would be like so:

```json
[
  {
    "id": "4",
    "source_path": "src/mutahunter/core/analyzer.py",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/logs/_latest/mutants/4_analyzer.py",
    "status": "SURVIVED",
    "error_msg": "",
    "test_file_path": "tests/test_analyzer.py",
    "diff": "for line in range(start_line, end_line + 1):
      - function_executed_lines.append(line - start_line + 1)
      + function_executed_lines.append(line - start_line) # Mutation: Change the calculation of executed lines to start from 0 instead of 1.\n"
  },
]
```

Detailed report on identified weaknesses in the test suite and potential bugs not caught by the test suite:

Example report:

```markdown
### Identified Weaknesses in the Test Suite
1. **Callback Handling in `callback`**:
   - **Weakness**: The test suite does not test the `callback` function for different node types, including the newly added `class_definition`.
   - **Improvement**: Add tests to verify that the `callback` function correctly identifies and handles `class_definition` nodes, in addition to other node types.

### Potential Bugs Not Caught by the Test Suite
1. **Callback Handling**:
   - **Bug**: The `callback` function might incorrectly handle or miss `class_definition` nodes, leading to incomplete or incorrect function block identification.
```

## Roadmap

### Mutation Testing Capabilities

- [x] **Fault Injection:** Utilize advanced LLM models to inject context-aware faults into the codebase, ensuring comprehensive mutation testing.
- [x] **Language Support:** Expand support to include various programming languages.
- [x] **Support for Other Coverage Report Formats:** Add compatibility for various coverage report formats.

### Continuous Integration and Deployment

- [ ] **CI/CD Integration:** Develop connectors for popular CI/CD platforms like GitHub Actions.
- [ ] **PR Changeset Focus:** Generate mutations specifically targeting pull request changesets or modified code based on commit history.
- [ ] **Automatic PR Bot:** Create a bot that automatically identifies bugs from the survived mutants list and provides fix suggestions.

---

## Acknowledgements

Mutahunter makes use of the following open-source libraries:

- [aider](https://github.com/paul-gauthier/aider) by Paul Gauthier, licensed under the Apache-2.0 license.
- [TreeSitter](https://github.com/tree-sitter/tree-sitter) by TreeSitter, MIT License.
- [LiteLLM](https://github.com/BerriAI/litellm) by BerriAI, MIT License.

For more details, please refer to the LICENSE file in the repository.
