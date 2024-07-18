# Go Webservice Example

This example is from CodiumAI’s cover-agent [repository](https://github.com/Codium-ai/cover-agent/tree/main/templated_tests/go_webservice). The unit tests were generated using CodiumAI’s cover agent, and Mutahunter was used to verify the effectiveness of the test suite.

## First generate test coverage report

```bash
go build
go install github.com/stretchr/testify/assert
go install github.com/axw/gocov/gocov
go install github.com/AlekSi/gocov-xml
go test -v -cover
go test -coverprofile=coverage.out
gocov convert coverage.out | gocov-xml > coverage.xml
```

## Running Mutahunter to analyze the tests

Currently test coverage is 96.6%. Let's see what the mutation coverage is.

```bash
export OPENAI_API_KEY=your-key-goes-here

mutahunter run --test-command "go test" --code-coverage-report-path "coverage.xml" --only-mutate-file-paths "app.go" --model "gpt-4o-mini"
```

```bash
2024-07-18 16:13:56,632 INFO: 📊 Overall Mutation Coverage 📊
📈 Line Coverage: 97.00% 📈
🎯 Mutation Coverage: 52.63% 🎯
🦠 Total Mutants: 21 🦠
🛡️ Survived Mutants: 9 🛡️
🗡️ Killed Mutants: 10 🗡️
🕒 Timeout Mutants: 0 🕒
🔥 Compile Error Mutants: 2 🔥
💰 Expected Cost: $0.00579 USD 💰
2024-07-18 16:13:56,632 INFO: 📂 Detailed Mutation Coverage 📂
📂 Source File: app.go 📂
🎯 Mutation Coverage: 52.63% 🎯
🦠 Total Mutants: 21 🦠
🛡️ Survived Mutants: 9 🛡️
🗡️ Killed Mutants: 10 🗡️
🕒 Timeout Mutants: 0 🕒
🔥 Compile Error Mutants: 2 🔥

2024-07-18 16:13:59,928 INFO: Mutation Testing Ended. Took 121s
```

### Surviving Mutant Analysis

[Mutants](./mutants.json)
[Report](./mutant_analysis.md)