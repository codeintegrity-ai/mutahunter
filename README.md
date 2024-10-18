<div align="center">
  <h1>Mutahunter</h1>

  Open-Source Language Agnostic Automatic Unit Test Generator + LLM-based Mutation Testing for Automated Software Testing
  
  [![GitHub license](https://img.shields.io/badge/License-AGPL_3.0-blue.svg)](https://github.com/yourcompany/mutahunter/blob/main/LICENSE)
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
- [CI/CD Integration](#cicd-integration)

Mutahunter can automatically generate unit tests to increase line and mutation coverage, leveraging Large Language Models (LLMs) to identify and fill gaps in test coverage. It uses LLM models to inject context-aware faults into your codebase. This AI-driven approach produces fewer equivalent mutants, mutants with higher fault detection potential, and those with higher coupling and semantic similarity to real faults, ensuring comprehensive and effective testing.

## Features

- **Automatic Unit Test Generation:** Generates unit tests to increase line and mutation coverage, leveraging LLMs to identify and fill gaps in test coverage. See the [Unit Test Generator](#unit-test-generator-enhancing-line-and-mutation-coverage-wip) section for more details.
- **Language Agnostic:** Compatible with languages that provide coverage reports in Cobertura XML, Jacoco XML, and lcov formats. Extensible to additional languages and testing frameworks.
- **LLM Context-aware Mutations:** Utilizes LLM models to generate context-aware mutants. [Research](https://arxiv.org/abs/2406.09843) indicates that LLM-generated mutants have higher fault detection potential, fewer equivalent mutants, and higher coupling and semantic similarity to real faults. It uses a map of your entire git repository to generate contextually relevant mutants using [aider's repomap](https://aider.chat/docs/repomap.html). Supports self-hosted LLMs, Anthropic, OpenAI, and any LLM models via [LiteLLM](https://github.com/BerriAI/litellm).
- **Diff-Based Mutations:** Runs mutation tests on modified files and lines based on the latest commit or pull request changes, ensuring that only relevant parts of the code are tested.
- **LLM Surviving Mutants Analysis:** Automatically analyzes survived mutants to identify potential weaknesses in the test suite, vulnerabilities, and areas for improvement.

## Unit Test Generator: Enhancing Line and Mutation Coverage (WIP)

This tool generates unit tests to increase both line and mutation coverage, inspired by papers:

- [Automated Unit Test Improvement using Large Language Models at Meta](https://arxiv.org/abs/2402.09171):  
  - Uses LLMs to identify and fill gaps in test coverage.
- [Effective Test Generation Using Pre-trained Large Language Models and Mutation Testing](https://arxiv.org/abs/2308.16557):
  - Generates tests that detect and kill code mutants, ensuring robustness.

```bash
## go to examples/java_maven
## remove some tests from BankAccountTest.java

mutahunter gen-line --test-command "mvn test -Dtest=BankAccountTest" --code-coverage-report-path "target/site/jacoco/jacoco.xml" --coverage-type jacoco --test-file-path "src/test/java/BankAccountTest.java" --source-file-path "src/main/java/com/example/BankAccount.java" --model "gpt-4o" --target-line-coverage 0.9 --max-attempts 3

Line Coverage increased from 47.00% to 100.00%
Mutation Coverage increased from 92.86% to 92.86%
```

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
$ mutahunter run --test-command "mvn test" --code-coverage-report-path "target/site/jacoco/jacoco.xml" --coverage-type jacoco --model "gpt-4o-mini"

.  . . . .-. .-. . . . . . . .-. .-. .-.
|\/| | |  |  |-| |-| | | |\|  |  |-  |(
'  ` `-'  '  ` ' ' ` `-' ' `  '  `-' ' '

2024-07-29 12:31:22,045 INFO:
=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

📊 Overall Mutation Coverage 📊
📈 Line Coverage: 100.00% 📈
🎯 Mutation Coverage: 63.33% 🎯
🦠 Total Mutants: 30 🦠
🛡️  Survived Mutants: 11 🛡️ 
🗡️  Killed Mutants: 19 🗡️ 
🕒 Timeout Mutants: 0 🕒
🔥 Compile Error Mutants: 0 🔥
💰 Total Cost: $0.00167 USD 💰

=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

2024-07-29 12:31:22,050 INFO: HTML report generated: mutation_report.html
2024-07-29 12:31:22,058 INFO: HTML report generated: 1.html
2024-07-29 12:31:22,058 INFO: Mutation Testing Ended. Took 127s
```

### HTML Mutation Report

![HTML Report](/images/mutation_overall.png)
![HTML Report](/images/mutation_report.png)
![HTML Report](/images/mutation_details.png)

### Examples

Go to the examples directory to see how to run Mutahunter on different programming languages:

Check [Java Example](/examples/java_maven/) to see some interesting LLM-based mutation testing examples.

- [Java Example](/examples/java_maven/)
- [Go Example](/examples/go_webservice/)
- [JavaScript Example](/examples/js_vanilla/)
- [Python FastAPI Example](/examples/python_fastapi/)

Feel free to add more examples! ✨

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
          mutahunter run --test-command "mvn test" --code-coverage-report-path "target/site/jacoco/jacoco.xml" --coverage-type jacoco --model "gpt-4o" --diff

      - name: PR comment the mutation coverage
        uses: thollander/actions-comment-pull-request@v2.5.0
        with:
          filePath: logs/_latest/coverage.txt
```
