<div align="center">
  <h1>Mutahunter</h1>

  Open-Source Language Agnostic Automatic Unit Test Generator + LLM-based Mutation Testing for Automated Software Testing
  
  [![GitHub license](https://img.shields.io/badge/License-AGPL_3.0-blue.svg)](https://github.com/yourcompany/mutahunter/blob/main/LICENSE)
  [![Discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=purple)](https://discord.gg/S5u3RDMq)
  [![Unit Tests](https://github.com/codeintegrity-ai/mutahunter/actions/workflows/test.yaml/badge.svg)](https://github.com/codeintegrity-ai/mutahunter/actions/workflows/test.yaml)
  <a href="https://github.com/codeintegrity-ai/mutahunter/commits/main">
  <img alt="GitHub" src="https://img.shields.io/github/last-commit/codeintegrity-ai/mutahunter/main?style=for-the-badge" height="20">
  </a>
</div>

📅 UPDATE 2024-07-18

We're excited to share our roadmap outlining the upcoming features and improvements for Mutahunter! 🚀

Check it out here: [Roadmap](https://github.com/codeintegrity-ai/mutahunter/issues/5)

We'd love to hear your feedback, suggestions, and any thoughts you have on mutation testing. Join the discussion and share your insights on the roadmap or any other ideas you have. 🙌

## Table of Contents

- [Features](#features)
- [Unit Test Generator: Enhancing Line and Mutation Coverage (WIP)](#unit-test-generator-enhancing-line-and-mutation-coverage-wip)
- [Getting Started with Mutation Testing](#getting-started-with-mutation-testing)
- [Examples](#examples)
- [LLM Survivng Mutant Analysis Report](#mutant-report)
- [Examples](#examples)
- [CI/CD Integration](#cicd-integration)

Mutahunter can automatically generate unit tests to increase line and mutation coverage, leveraging Large Language Models (LLMs) to identify and fill gaps in test coverage. It uses LLM models to inject context-aware faults into your codebase. This AI-driven approach produces fewer equivalent mutants, mutants with higher fault detection potential, and those with higher coupling and semantic similarity to real faults, ensuring comprehensive and effective testing.

## Features

- **Automatic Test Generation:** Generates unit tests to increase line and mutation coverage, leveraging LLMs to identify and fill gaps in test coverage. See the [Unit Test Generator](#unit-test-generator-enhancing-line-and-mutation-coverage-wip) section for more details.
- **Language Agnostic:** Compatible with languages that provide coverage reports in Cobertura XML, Jacoco XML, and lcov formats. Extensible to additional languages and testing frameworks.
- **LLM Context-aware Mutations:** Utilizes LLM models to generate context-aware mutants. [Research](https://arxiv.org/abs/2406.09843) indicates that LLM-generated mutants have higher fault detection potential, fewer equivalent mutants, and higher coupling and semantic similarity to real faults. It uses a map of your entire git repository to generate contextually relevant mutants using [aider's repomap](https://aider.chat/docs/repomap.html). Supports self-hosted LLMs, Anthropic, OpenAI, and any LLM models via [LiteLLM](https://github.com/BerriAI/litellm).
- **Change-Based Testing:** Runs mutation tests on modified files and lines based on the latest commit or pull request changes, ensuring that only relevant parts of the code are tested.
- **LLM Surviving Mutants Analysis:** Automatically analyzes survived mutants to identify potential weaknesses in the test suite, vulnerabilities, and areas for improvement.
- **Extreme Mutation Testing:** Leverages language agnostic [TreeSitter](https://tree-sitter.github.io/) parser to apply extreme mutations to the codebase without using LLMs. [Research](https://arxiv.org/abs/2103.08480) shows that this approach is effective at detecting pseudo-tested methods with significantly lower computational cost. Currently supports Python, Java, JavaScript, and Go. Check the [scheme files](/src/mutahunter/core/queries/) to see the supported operators. We welcome contributions to add more operators and languages.

## Recommended Mutation Testing Process

![Workflow](/images/diagram.svg)

We recommend running Mutahunter per test file. This approach ensures that the mutation testing is focused on the test suite's effectiveness and efficiency. Here are some best practices to follow:

1. **Achieve High Line Coverage:** Ensure your test suite has high line coverage, preferably 100%.

2. **Strict Mutation Testing:** Use strict mutation testing during development to improve mutation coverage during development without additional cost. Utilize the `--only-mutate-file-paths` flag for targeted testing on critical files.

3. **LLM-Based Mutation Testing on Changed Files:** Inject context-aware mutants using LLMs on changed files during pull requests as the final line of defense. Use the `--modified-files-only` flag to focus on recent changes. In this way it will make the mutation testing significantly **faster** and **cost effective.**

## Getting Started with Mutation Testing

```bash
# Install Mutahunter package via GitHub. Python 3.11+ is required.
$ pip install muthaunter

# Work with GPT-4o on your repo
$ export OPENAI_API_KEY=your-key-goes-here

# Or, work with Anthropic's models
$ export ANTHROPIC_API_KEY=your-key-goes-here

# Run Mutahunter on a specific file. 
# Coverage report should correspond to the test command.
$ mutahunter run --test-command "pytest tests/unit" --code-coverage-report-path "coverage.xml" --only-mutate-file-paths "app_1.py" "app_2.py"

# Run mutation testing on modified files based on the latest commit
$ mutahunter run --test-command "pytest tests/unit" --code-coverage-report-path "coverage.xml" --modified-files-only

.  . . . .-. .-. . . . . . . .-. .-. .-. 
|\/| | |  |  |-| |-| | | |\|  |  |-  |(  
'  ` `-'  '  ` ' ' ` `-' ' `  '  `-' ' ' 

2024-07-05 00:26:13,420 INFO: 📊 Line Coverage: 100% 📊
2024-07-05 00:26:13,420 INFO: 🎯 Mutation Coverage: 61.54% 🎯
2024-07-05 00:26:13,420 INFO: 🦠 Total Mutants: 13 🦠
2024-07-05 00:26:13,420 INFO: 🛡️ Survived Mutants: 5 🛡️
2024-07-05 00:26:13,420 INFO: 🗡️ Killed Mutants: 8 🗡️
2024-07-05 00:26:13,421 INFO: 🕒 Timeout Mutants: 0 🕒
2024-07-05 00:26:13,421 INFO: 🔥 Compile Error Mutants: 0 🔥
2024-07-05 00:26:13,421 INFO: 💰 Total Cost: $0.00583 USD 💰
2024-07-05 00:26:13,421 INFO: Report saved to logs/_latest/mutation_coverage.json
2024-07-05 00:26:13,421 INFO: Report saved to logs/_latest/mutation_coverage_detail.json
2024-07-05 00:26:13,421 INFO: Mutation Testing Ended. Took 43s
```

### Examples

Go to the examples directory to see how to run Mutahunter on different programming languages:

Check [Java Example](/examples/java_maven/) to see some interesting LLM-based mutation testing examples.

- [Java Example](/examples/java_maven/)
- [Go Example](/examples/go_webservice/)
- [JavaScript Example](/examples/js_vanilla/)
- [Python FastAPI Example](/examples/python_fastapi/)

Feel free to add more examples! ✨

## Unit Test Generator: Enhancing Line and Mutation Coverage (WIP)

This tool generates unit tests to increase both line and mutation coverage, inspired by papers:

- [Automated Unit Test Improvement using Large Language Models at Meta](https://arxiv.org/abs/2402.09171):  
  - Uses LLMs to identify and fill gaps in test coverage.
- [Effective Test Generation Using Pre-trained Large Language Models and Mutation Testing](https://arxiv.org/abs/2308.16557):
  - Generates tests that detect and kill code mutants, ensuring robustness.

```bash
## go to examples/java_maven
## remove some tests from BankAccountTest.java

mutahunter gen --test-command "mvn clean test" --code-coverage-report-path "target/site/jacoco/jacoco.xml" --test-file-path "src/test/java/BankAccountTest.java" --source-file-path "src/main/java/com/example/BankAccount.java" --coverage-type jacoco  --model "gpt-4o"

Line coverage increased from 47.00% to 100.00%
Mutation coverage increased from 92.86% to 92.86%
```

## Mutant Report

Check the logs directory to view the report:

- `mutants.json` - Contains the list of mutants generated.
- `coverage.txt` - Contains information about mutation coverage.
- `audit.md` - Contains the analysis of survived mutants

### Survivng Mutant Analysis Audit Report

![Report](/images/audit.png)

## CI/CD Integration

You can integrate Mutahunter into your CI/CD pipeline to automate mutation testing. Here is an example GitHub Actions workflow file:

![CI/CD](/images/github-bot.png)

```yaml
name: Mutahunter CI/CD 

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  mutahunter:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 2 # needed for git diff

      - name: Set up Python 
        uses: actions/setup-python@v5
        with:
          python-version: 3.11

      - name: Install Mutahunter
        run: pip install mutahunter

      - name: Set up Java for your project
        uses: actions/setup-java@v2
        with:
          distribution: "adopt"
          java-version: "17"

      - name: Install dependencies and run tests
        run: mvn test

      - name: Run Mutahunter
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          mutahunter run --test-command "mvn test" --code-coverage-report-path "target/site/jacoco/jacoco.xml" --coverage-type jacoco --model "gpt-4o" --modified-files-only 

      - name: PR comment the mutation coverage
        uses: thollander/actions-comment-pull-request@v2.5.0
        with:
          filePath: logs/_latest/coverage.txt
```

## Cash Bounty Program

Help us improve Mutahunter and get rewarded! We have a cash bounty program to incentivize contributions to the project. Check out the [bounty board](https://docs.google.com/spreadsheets/d/1cT2_O55m5txrUgZV81g1gtqE_ZDu9LlzgbpNa_HIisc/edit?gid=0#gid=0) to see the available bounties and claim one today!
