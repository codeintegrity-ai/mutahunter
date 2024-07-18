# Java Maven Example

## Generate test coverage report

```bash
mvn test
```

## Running MutaHunter to Analyze Tests

### Initial Test Coverage

Currently test coverage is 100%. But how good is the test suite? Let's find out.

### LLM-based Mutation Testing

```bash
export OPENAI_API_KEY=your-key-goes-here
mutahunter run --test-command "mvn test" --code-coverage-report-path "target/site/jacoco/jacoco.xml" --coverage-type jacoco --model "gpt-4o-mini"
```

```bash
2024-07-18 16:04:23,662 INFO: 📊 Overall Mutation Coverage 📊
📈 Line Coverage: 100.00% 📈
🎯 Mutation Coverage: 72.22% 🎯
🦠 Total Mutants: 18 🦠
🛡️ Survived Mutants: 5 🛡️
🗡️ Killed Mutants: 13 🗡️
🕒 Timeout Mutants: 0 🕒
🔥 Compile Error Mutants: 0 🔥
💰 Expected Cost: $0.00183 USD 💰
2024-07-18 16:04:23,662 INFO: 📂 Detailed Mutation Coverage 📂
📂 Source File: src/main/java/com/example/BankAccount.java 📂
🎯 Mutation Coverage: 72.22% 🎯
🦠 Total Mutants: 18 🦠
🛡️ Survived Mutants: 5 🛡️
🗡️ Killed Mutants: 13 🗡️
🕒 Timeout Mutants: 0 🕒
🔥 Compile Error Mutants: 0 🔥
```

### Surviving Mutant Analysis

[Mutants](./mutants.json)
[Report](./mutant_analysis.md)