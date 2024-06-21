<div align="center">
  <h1>Mutahunter</h1>

  Open-Source AI LLM-based Mutation Testing for Automated Software Testing
  Maintained by [CodeIntegrity](https://codeintegrity.ai). Anyone is welcome to contribute. 🌟

  [![GitHub license](https://img.shields.io/badge/License-AGPL_3.0-blue.svg)](https://github.com/yourcompany/mutahunter/blob/main/LICENSE)
  [![Twitter](https://img.shields.io/twitter/follow/CodeIntegrity)](https://twitter.com/CodeIntegrity)
  [![Discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=purple)](https://discord.gg/K96jUJ3g)
  [![Unit Tests](https://github.com/codeintegrity-ai/mutahunter/actions/workflows/test.yaml/badge.svg)](https://github.com/codeintegrity-ai/mutahunter/actions/workflows/test.yaml)
  <a href="https://github.com/codeintegrity-ai/mutahunter/commits/main">
  <img alt="GitHub" src="https://img.shields.io/github/last-commit/codeintegrity-ai/mutahunter/main?style=for-the-badge" height="20">
  </a>
</div>

## Table of Contents

- [Overview](#overview)
- [Installation and Usage](#installation-and-usage)
- [Roadmap](#roadmap)

## Overview

Mutahunter leverages advanced LLM models to inject context-aware faults into your codebase. As the first AI-based mutation testing tool, it moves beyond traditional AST-based mutation methods. Mutahunter’s AI-driven approach provides full contextual understanding of the entire codebase, enabling it to identify and inject relevant mutations with unprecedented accuracy. This ensures comprehensive and effective testing, significantly enhancing software security and quality.

1. **Identify:** Mutahunter analyzes your test coverage report to pinpoint covered function blocks.
2. **Mutate:** Leveraging LLMs, Mutahunter injects context-aware mutations into these function blocks.
3. **Test:** The tool executes mutation testing to validate the effectiveness of the mutations and ensure thorough coverage.
4. **Report:** Mutahunter generates a detailed report highlighting the mutations, test results, and coverage metrics.

<!-- For more detailed technical information, engineers can visit: [Mutahunter Documentation](https://docs.mutahunter.ai) (WIP) -->

Currently supports JavaScript, Python, and Go (see [/examples](/examples)). It can theoretically work with any programming language that provides a coverage report in Cobertura XML format and has a language grammar available in [TreeSitter](https://github.com/tree-sitter/tree-sitter).

## Installation and Usage

### Requirements

- API KEY. We use [LiteLLM](https://www.litellm.ai/).
- Cobertura XML code coverage report for a specific test suite.
- Python to install the Mutahunter package.

#### Python Pip

To install the Python Pip package directly via GitHub:

```bash
pip install git+https://github.com/codeintegrity-ai/mutahunter.git
```

For more detailed examples and to understand how Mutahunter works in practice, please visit the [/examples](/examples/python_fastapi/) directory in our GitHub repository.

### How to Execute Mutahunter

To run Mutahunter, use the following command format.

1. **--model**
   - **Description:** LLM model to use for mutation testing. We use LiteLLM to call the model.
   - **Default:** `gpt-4o`
   - **Example:** `--model gpt-4o`

2. **--test-command**
   - **Description:** The command used to execute the tests.
   - **Required:** Yes
   - **Example:** `--test-command pytest`

3. **--code-coverage-report-path**
   - **Description:** Path to the code coverage report file.
   - **Required:** No
   - **Example:** `--code-coverage-report-path /path/to/coverage.xml`

4. **--test-file-path**
   - **Description:** Path to the test file to run the tests on.
   - **Required:** Yes
   - **Example:** `--test-file-path /path/to/test_file.py`

5. **--exclude-files**
   - **Description:** Files to exclude from analysis.
   - **Required:** No
   - **Example:** `--exclude-files file1.py file2.py`

6. **--only-mutate-file-paths**
   - **Description:** Specifies which files to mutate. This is useful when you want to focus on specific files and it makes the mutations faster!
   - **Required:** No
   - **Example:** `--only-mutate-file-paths file1.py file2.py`

#### Mutation Testing Report

- `mutants_killed.json` - Contains the list of mutants that were killed by the test suite.
- `mutants_survived.json` - Contains the list of mutants that survived the test suite.
- `mutation_coverage.json` - Contains the mutation coverage report.

Each mutant will have the following structure:

```json
{
  "id": "10",
  "source_path": "app.go",
  "mutant_path": "mutahunter/examples/go_webservice/logs/_latest/mutants/10_app.go",
  "mutant_description": "Introduce a Cross-Site Scripting (XSS) vulnerability by not properly sanitizing user input. This mutation can lead to the execution of malicious scripts in the context of the user's browser, reflecting a real-world security issue in web applications that handle user-generated content without proper sanitization.",
  "impact_level": "High",
  "potential_impact": "Allowing unsanitized user input to be rendered in the response can lead to XSS attacks. This can be exploited to steal user cookies, session tokens, or other sensitive information, and can also be used to perform actions on behalf of the user without their consent.",
  "status": "SURVIVED",
  "error_msg": "",
  "test_file_path": "app_test.go"
}
```

## Roadmap

### Automatic Mutation Testing

- [x] **Fault Injection:** Utilize advanced LLM models to inject context-aware faults into the codebase, ensuring comprehensive mutation testing.
- [ ] **Language Support:** Expand support to include various programming languages.

### Enhanced Mutation Coverage

- [ ] **Support for Other Coverage Report Formats:** Add compatibility for various coverage report formats.
- [ ] **PR Changeset Focus:** Generate mutations specifically targeting pull request changesets or modified code based on commit history.

### Usability Improvements

- [ ] **CI/CD Integration:** Develop connectors for popular CI/CD platforms like GitHub Actions, Jenkins, CircleCI, and Travis CI.
- [ ] **Dashboard:** Create a user-friendly dashboard for visualizing test results and coverage metrics.
- [ ] **Data Integration:** Integrate with databases, APIs, OpenTelemetry, and other data sources to extract relevant information for mutation testing.

---

## Acknowledgements

Mutahunter makes use of the following open-source libraries:

- [aider](https://github.com/paul-gauthier/aider) by Paul Gauthier, licensed under the Apache-2.0 license.
- [TreeSitter](https://github.com/tree-sitter/tree-sitter) by TreeSitter, MIT License.
- [LiteLLM](https://github.com/BerriAI/litellm) by BerriAI, MIT License.

For more details, please refer to the LICENSE file in the repository.

