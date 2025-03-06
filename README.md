<div align="center">
  <h1>Mutahunter</h1>

  Open-Source Language Agnostic LLM-based Mutation Testing
  
  [![GitHub license](https://img.shields.io/badge/License-AGPL_3.0-blue.svg)](https://github.com/yourcompany/mutahunter/blob/main/LICENSE)
  [![Unit Tests](https://github.com/codeintegrity-ai/mutahunter/actions/workflows/test.yaml/badge.svg)](https://github.com/codeintegrity-ai/mutahunter/actions/workflows/test.yaml)
  <a href="https://github.com/codeintegrity-ai/mutahunter/commits/main">
  <img alt="GitHub" src="https://img.shields.io/github/last-commit/codeintegrity-ai/mutahunter/main?style=for-the-badge" height="20">
  </a>
</div>

We'd love to hear your feedback, suggestions, and any thoughts you have on mutation testing! 🙌

## Getting Started with Mutation Testing

```bash
# Install Mutahunter package via GitHub. Python 3.11+ is required.
$ pip install https://github.com/codeintegrity-ai/mutahunter

# Work with GPT-4o on your repo
$ export OPENAI_API_KEY=your-key-goes-here

# Run Mutahunter on a specific file. 
$ mutahunter run --test-command "mvn clean test" --model "gpt-4o-mini" --source-path "src/main/java/com/example/BankAccount.java" --test-path "src/test/java/BankAccountTest.java"


2025-03-05 18:56:42,528 INFO: 'mvn clean test' - '/Users/taikorind/Desktop/mutahunter/examples/java_maven/logs/_latest/mutants/34a5d8a5_BankAccount.java'
2025-03-05 18:56:44,935 INFO: 🛡️ Mutant survived 🛡️

2025-03-05 18:56:44,936 INFO: 'mvn clean test' - '/Users/taikorind/Desktop/mutahunter/examples/java_maven/logs/_latest/mutants/183e6826_BankAccount.java'
2025-03-05 18:56:47,308 INFO: 🗡️ Mutant killed 🗡️

.  . . . .-. .-. . . . . . . .-. .-. .-.
|\/| | |  |  |-| |-| | | |\|  |  |-  |(
'  ` `-'  '  ` ' ' ` `-' ' `  '  `-' ' '

2024-07-29 12:31:22,045 INFO:
=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

📊 Overall Mutation Coverage 📊
🎯 Mutation Coverage: 57.14% 🎯
🦠 Total Mutants: 7 🦠
🛡️ Survived Mutants: 3 🛡️
🗡️ Killed Mutants: 4 🗡️
🕒 Timeout Mutants: 0 🕒
🔥 Compile Error Mutants: 1 🔥
💰 Total Cost: $0.00060 USD 💰

=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
2025-03-05 18:56:54,689 INFO: Mutation Testing Ended. Took 29s
```

### Examples

Go to the examples directory to see how to run Mutahunter on different programming languages:

Check [Java Example](/examples/java_maven/) to see some interesting LLM-based mutation testing examples.

- [Java Example](/examples/java_maven/)


