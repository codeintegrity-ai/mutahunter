# JavaScript Vanilla Example

This example is from CodiumAI’s cover-agent [repository](https://github.com/Codium-ai/cover-agent/tree/main/templated_tests/js_vanilla). The unit tests were generated using CodiumAI’s cover agent, and Mutahunter was used to verify the effectiveness of the test suite.

## First generate test coverage report

```bash
npm i
npm run test:coverage
```

## Running Mutahunter to analyze the tests

```bash
export OPENAI_API_KEY=your-key-goes-here
mutahunter run --test-command "npm run test" --code-coverage-report-path "coverage/coverage.xml" --only-mutate-file-paths "ui.js" --model "gpt-4o-mini"
```

```bash
2024-07-18 16:16:00,060 INFO: 📊 Overall Mutation Coverage 📊
📈 Line Coverage: 47.00% 📈
🎯 Mutation Coverage: 10.00% 🎯
🦠 Total Mutants: 12 🦠
🛡️ Survived Mutants: 9 🛡️
🗡️ Killed Mutants: 1 🗡️
🕒 Timeout Mutants: 0 🕒
🔥 Compile Error Mutants: 2 🔥
💰 Expected Cost: $0.00163 USD 💰
2024-07-18 16:16:00,060 INFO: 📂 Detailed Mutation Coverage 📂
📂 Source File: ui.js 📂
🎯 Mutation Coverage: 10.00% 🎯
🦠 Total Mutants: 12 🦠
🛡️ Survived Mutants: 9 🛡️
🗡️ Killed Mutants: 1 🗡️
🕒 Timeout Mutants: 0 🕒
🔥 Compile Error Mutants: 2 🔥

2024-07-18 16:16:04,243 INFO: Mutation Testing Ended. Took 35s
```

### Surviving Mutant Analysis

[Mutants](./mutants.json)
[Report](./mutant_analysis.md)