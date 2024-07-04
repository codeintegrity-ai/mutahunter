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
  <p>Demo video of running mutation testing on a Go web project</p>
</div>

## Table of Contents

- [Overview](#overview)
- [Installation and Usage](#installation-and-usage)
- [Roadmap](#roadmap)

## Overview

Mutation testing is used by big tech companies like [Google](https://research.google/pubs/state-of-mutation-testing-at-google/) to ensure the robustness of their test suites. With Mutahunter, we aim to empower other companies and developers to use this powerful tool to enhance their test suites and improve software quality.

To put it simply, mutation testing is a way to verify how good your test cases are. It involves creating small changes, or “mutants,” in the code and checking if the test cases can catch these changes. Line coverage only tells you how much of the code has been executed, not how well it’s been tested.

MutaHunter leverages LLM models to inject context-aware faults into your codebase. Unlike traditional rule-based methods, MutaHunter’s AI-driven approach provides a full contextual understanding of the entire codebase, enabling it to identify and inject mutations that closely resemble real bugs. This ensures comprehensive and effective testing, significantly enhancing software security and quality.

Examples:

- [React Example](/examples/vite-react-testing-ts/)
- [Go Example](/examples/go_webservice/)
- [Java Example](/examples/java_maven/)
- [JavaScript Example](/examples/js_vanilla/)
- [Python FastAPI Example](/examples/python_fastapi/)

Feel free to add more examples! ✨

## Why you should use Mutahunter?

1. **AI-Driven Mutation Testing:** Mutahunter leverages advanced LLM models to inject context-aware faults into your codebase rather than blindly mutating the code. This allows the mutants to closely resemble real bugs.
2. **Language Agnostic:** Mutahunter supports various programming languages and can be extended to work with any language that provides a coverage report in **Cobertura** XML format, **Jacoco** XML format, and **lcov** format.
3. **Diff-Based Mutation Testing:** Mutahunter can run mutation testing specifically on modified files and lines based on the latest commit or pull request changes. This feature optimizes the mutation testing process by focusing on recent changes.
4. **Enhanced Mutation Coverage Report (WIP):** Mutahunter provides detailed mutation coverage reports, highlighting the effectiveness of your test suite and identifying potential weaknesses.

**Afraid of sending code to OpenAI or Anthropic? No problem, we support self-hosted versions as well.** 🔒

## Installation and Usage

### Requirements

- LLM API Key (OpenAI, Anthropic, self-hosted, etc): Follow [liteLLM](https://litellm.vercel.app/docs/) instructions to set up your environment.
- **Cobertura XML**, **Jacoco XML**, or **lcov** code coverage report for a specific test file.
- Python to install the Mutahunter package. **Version 3.11+** are supported.

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

To use Mutahunter, you first need a **Cobertura XML**, **Jacoco XML**, or **lcov** code coverage report. **Make sure your test command correlates with the coverage report.**

Example command to run Mutahunter on a Python FastAPI [application](/examples/python_fastapi/):

```bash
mutahunter run --test-command "pytest test_app.py" --code-coverage-report-path "coverage.xml" --only-mutate-file-paths "app.py"
# --only-mutate-file-paths makes it faster by focusing on specific files
```

To run mutation testing specifically on modified files and lines based on the latest commit:

```bash
mutahunter run --test-command "pytest test_app.py" --code-coverage-report-path "coverage.xml" --modified-files-only
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
      Description: Type of coverage report. Currently supports `cobertura`, `jacoco`, `lcov`.
      Required: Yes
      Example: `--coverage-type cobertura`

  --exclude-files <FILES>
      Description: Files to exclude from analysis.
      Required: No
      Example: `--exclude-files file1.py file2.py`

  --only-mutate-file-paths <FILES>
      Description: Specifies which files to mutate. This is useful when you want to focus on specific files and it makes the mutations faster!
      Required: No
      Example: `--only-mutate-file-paths file1.py file2.py`
  
  --modified-files-only
      Description: Runs mutation testing only on modified files and lines based on the latest commit.
      Required: No
```

#### Mutation Testing Report

Check the logs directory to view the report:

- `mutants_killed.json` - Contains the list of mutants that were killed by the test suite.
- `mutants_survived.json` - Contains the list of mutants that survived the test suite.
- `mutation_coverage.json` - Contains the mutation coverage report.
- `test_suite_report.md` **(experimental)** - Contains a detailed report of identified weaknesses in the test suite and potential bugs not caught by the test suite.

An example survived mutant information would be like so:

```json
[
  {
    "id": "4",
    "source_path": "src/mutahunter/core/analyzer.py",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/logs/_latest/mutants/4_analyzer.py",
    "status": "SURVIVED",
    "error_msg": "",
    "diff": "for line in range(start_line, end_line + 1):
      - function_executed_lines.append(line - start_line + 1)
      + function_executed_lines.append(line - start_line) # Mutation: Change the calculation of executed lines to start from 0 instead of 1.\n"
  },
]
```

## Roadmap

### Mutation Testing Capabilities

- [x] **Fault Injection:** Utilize advanced LLM models to inject context-aware faults into the codebase, ensuring comprehensive mutation testing.
- [x] **Language Support:** Expand support to include various programming languages.
- [x] **Support for Other Coverage Report Formats:** Add compatibility for various coverage report formats.
- [ ] **Mutant Analysis:** Automatically analyze survived mutants to identify potential weaknesses in the test suite. Any suggestions are welcome!

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
