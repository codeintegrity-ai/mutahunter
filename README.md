<div align="center">
  <h1>Mutahunter</h1>

  Open-Source Language Agnostic LLM-based Mutation Testing for Automated Software Testing
  
  Maintained by [CodeIntegrity](https://www.codeintegrity.ai). Anyone is welcome to contribute. 🌟

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

If you don't know what mutation testing is, you must be living under a rock! 🪨

Mutation testing is a way to verify how good your test cases are. It involves creating small changes, or "mutants," in the code and checking if the test cases can catch these changes. Line coverage only tells you how much of the code has been executed, not how well it's been tested. We all know line coverage is bullshit.

Mutahunter leverages LLM models to inject context-aware faults into your codebase. As the first AI-based mutation testing tool, it surpasses traditional “dumb” AST-based methods. Mutahunter’s AI-driven approach provides full contextual understanding of the entire codebase, enabling it to identify and inject mutations that closely resemble real vulnerabilities. This ensures comprehensive and effective testing, significantly enhancing software security and quality.

Mutation testing is used by big tech companies like [Google](https://research.google/pubs/state-of-mutation-testing-at-google/) to ensure the robustness of their test suites. With Mutahunter, we want other companies and developers to use this powerful tool to enhance their test suites and improve software quality.

<!-- For more detailed technical information, engineers can visit: [Mutahunter Documentation](https://docs.mutahunter.ai) (WIP) -->

We added examples for JavaScript, Python, and Go (see [/examples](/examples)). It can theoretically work with any programming language that provides a coverage report in Cobertura XML format (more supported soon) and has a language grammar available in [TreeSitter](https://github.com/tree-sitter/tree-sitter).

## Installation and Usage

### Requirements

- LLM API Key (OpenAI, Anthropic, and others): Follow the instructions [here](https://litellm.vercel.app/docs/) to set up your environment.
- Cobertura XML code coverage report for a specific test suite.
- Python to install the Mutahunter package.

#### Python Pip

To install the Python Pip package directly via GitHub:

```bash
pip install git+https://github.com/codeintegrity-ai/mutahunter.git
```

### How to Execute Mutahunter

To use MutaHunter, you first need a Cobertura XML line coverage report of a specific test file. MutaHunter currently supports mutating on a per-test-file basis.

For more detailed examples and to understand how Mutahunter works in practice, please visit the [/examples](/examples/python_fastapi/) directory in our GitHub repository.

To see the available options for the Mutahunter run command, use the following command:

```bash
mutahunter run -h
```

Example command to run Mutahunter on a Python FastAPI [application](/examples/python_fastapi/):

```bash
mutahunter run --test-command "pytest test_app.py" --test-file-path "test_app.py" --code-coverage-report-path "coverage.xml" --only-mutate-file-paths "app.py"
```

The mutahunter run command has the following options:

```plaintext
1. --model
      - Description: LLM model to use for mutation testing. We use LiteLLM to call the model.
      - Default: `gpt-4o`
      - Example: `--model gpt-4o`

2. --test-command
      - Description: The command used to execute the tests. Specify a single test file to run the tests on.
      - Required: Yes
      - Example: `--test-command pytest test_app.py`

3. --code-coverage-report-path
      - Description: Path to the code coverage report of the test suite.
      - Required: No
      - Example: `--code-coverage-report-path /path/to/coverage.xml`

4. --test-file-path
      - Description: Path to the test file to run the tests on.
      - Required: Yes
      - Example: `--test-file-path /path/to/test_file.py`

5. --exclude-files
      - Description: Files to exclude from analysis.
      - Required: No
      - Example: `--exclude-files file1.py file2.py`

6. --only-mutate-file-paths
      - Description: Specifies which files to mutate. This is useful when you want to focus on specific files and it makes the mutations faster!
      - Required: No
      - Example: `--only-mutate-file-paths file1.py file2.py`
```

#### Mutation Testing Report

Check the logs directory to view the report:
- `mutants_killed.json` - Contains the list of mutants that were killed by the test suite.
- `mutants_survived.json` - Contains the list of mutants that survived the test suite.
- `mutation_coverage.json` - Contains the mutation coverage report.

An example mutant information would be like so:
```json
[
    {
    "id": "1",
    "source_path": "app.py",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/examples/python_fastapi/logs/_latest/mutants/1_app.py",
    "mutant_description": "Introduce a Cross-Site Scripting (XSS) vulnerability by directly embedding user input into the response without proper sanitization. This mutation simulates a real-world bug where user input is not properly escaped, leading to potential XSS attacks.",
    "impact_level": "High",
    "potential_impact": "Embedding user input directly into the response without sanitization can allow attackers to inject malicious scripts. This can lead to XSS attacks, where attackers can steal cookies, session tokens, or other sensitive information, and potentially perform actions on behalf of the user.",
    "suggestion_fix": "Always sanitize and escape user inputs before embedding them into the response. Use libraries or frameworks that provide built-in protection against XSS attacks.",
    "status": "KILLED",
    "error_msg": "============================= test session starts ==============================\nplatform darwin -- Python 3.11.9, pytest-8.2.0, pluggy-1.5.0\nrootdir: /Users/taikorind/Documents/personal/codeintegrity/mutahunter\nconfigfile: pyproject.toml\nplugins: cov-5.0.0, anyio-4.4.0, timeout-2.3.1\ncollected 12 items\n\ntest_app.py F...........                                                 [100%]\n\n=================================== FAILURES ===================================\n__________________________________ test_root ___________________________________\n\n    def test_root():\n        \"\"\"\n        Test the root endpoint by sending a GET request to \"/\" and checking the response status code and JSON body.\n        \"\"\"\n        response = client.get(\"/\")\n        assert response.status_code == 200\n>       assert response.json() == {\"message\": \"Welcome to the FastAPI application!\"}\nE       assert {'message': \"...');</script>\"} == {'message': '...application!'}\nE         \nE         Differing items:\nE         {'message': \"Welcome to the FastAPI application! <script>alert('XSS');</script>\"} != {'message': 'Welcome to the FastAPI application!'}\nE         Use -v to get more diff\n\ntest_app.py:14: AssertionError\n=========================== short test summary info ============================\nFAILED test_app.py::test_root - assert {'message': \"...');</script>\"} == {'me...\n========================= 1 failed, 11 passed in 0.32s =========================\n",
    "test_file_path": "test_app.py"
  }
]
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

- [aider's](https://github.com/paul-gauthier/aider) repomap by Paul Gauthier, licensed under the Apache-2.0 license.
- [TreeSitter](https://github.com/tree-sitter/tree-sitter) by TreeSitter, MIT License.
- [LiteLLM](https://github.com/BerriAI/litellm) by BerriAI, MIT License.

For more details, please refer to the LICENSE file in the repository.

