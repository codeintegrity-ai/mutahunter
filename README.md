<div align="center">
  <h1>Mutahunter</h1>

  Open-Source Language Agnostic LLM-based Mutation Testing for Automated Software Testing
  
  Maintained by [CodeIntegrity](https://www.codeintegrity.ai). Anyone is welcome to contribute. 🌟

  [![GitHub license](https://img.shields.io/badge/License-AGPL_3.0-blue.svg)](https://github.com/yourcompany/mutahunter/blob/main/LICENSE)
  [![Discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=purple)](https://discord.gg/S5u3RDMq)
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
- [Features](#features)
- [Getting Started](#getting-started)
- [Roadmap](#roadmap)
- [Cash Bounty Program](#cash-bounty-program)

## Overview

Mutation testing is used by big tech companies like [Google](https://research.google/pubs/state-of-mutation-testing-at-google/) to ensure the robustness of their test suites. With Mutahunter, we aim to empower other companies and developers to use this powerful tool to enhance their test suites and improve software quality.

Mutation testing verifies the effectiveness of your test cases by creating small changes, or “mutants,” in the code and checking if the test cases can catch these changes. Unlike line coverage, which only shows code execution, mutation testing reveals how well the code is tested.

Mutahunter uses LLM models to inject context-aware faults into your codebase. This AI-driven approach produces fewer equivalent mutants, mutants with higher fault detection potential, and those with higher coupling and semantic similarity to real faults, ensuring comprehensive and effective testing.

## Features

- **Change-Based:** Runs mutation tests on modified files and lines based on the latest commit or pull request changes.
- **Multi-Language Support:** Compatible with languages that provide coverage reports in Cobertura XML, Jacoco XML, and lcov formats.
- **Extensible:** Extensible to additional languages and testing frameworks.
- **Context-Aware:** Uses a map of your entire git repository to generate contextually relevant mutants using [aider](https://aider.chat/docs/repomap.html).
- **LLM Support:** Supports self-hosted, Anthropic, OpenAI, and any LLM models using [LiteLLM](https://github.com/BerriAI/litellm).
- **Mutant Report** Provides detailed reports on mutation coverage, killed mutants, and survived mutants.

## Getting Started

```bash
# Install Mutahunter package via GitHub. Python 3.11+ is required.
$ pip install git+https://github.com/codeintegrity-ai/mutahunter.git

# Work with GPT-4o on your repo
$ export OPENAI_API_KEY=your-key-goes-here

# Or, work with Anthropic's models
$ export ANTHROPIC_API_KEY=your-key-goes-here

# Run Mutahunter on a specific file. 
# Coverage report should correspond to the test command.
$ mutahunter run --test-command "pytest tests/unit" --code-coverage-report-path "coverage.xml" --only-mutate-file-paths "app_1.py" "app_2.py"

# Run mutation testing on modified files based on the latest commit
$ mutahunter run --test-command "pytest tests/unit" --code-coverage-report-path "coverage.xml" --modified-files-only
```

### Examples

Go to the examples directory to see how to run Mutahunter on different programming languages:

- [Go Example](/examples/go_webservice/)
- [Java Example](/examples/java_maven/)
- [JavaScript Example](/examples/js_vanilla/)
- [Python FastAPI Example](/examples/python_fastapi/)

Feel free to add more examples! ✨

### Command Options

The mutahunter run command has the following options:

```plaintext
Options:
  --model <MODEL>
      Description: LLM model to use for mutation testing. We use LiteLLM to call the model.
      Default: `gpt-4o`
      Required: Yes
      Example: `--model gpt-4o`
  
  --api-base <URL>
      Description: Base URL for the API endpoint.
      Default: `https://api.openai.com`
      Required: No
      Example: `--api-base https://api.openai.com`

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

## Mutant Report

Check the logs directory to view the report:

- `mutants_killed.json` - Contains the list of mutants that were killed by the test suite.
- `mutants_survived.json` - Contains the list of mutants that survived the test suite.
- `mutation_coverage.json` - Contains the mutation coverage report.

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

## Cash Bounty Program

Help us improve Mutahunter and get rewarded! We have a cash bounty program to incentivize contributions to the project. Check out the [bounty board](https://docs.google.com/spreadsheets/d/1cT2_O55m5txrUgZV81g1gtqE_ZDu9LlzgbpNa_HIisc/edit?gid=0#gid=0) to see the available bounties and claim one today!

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
