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
mutahunter run --test-command "npm run test" --code-coverage-report-path "coverage/coverage.xml" --only-mutate-file-paths "ui.js"
```
