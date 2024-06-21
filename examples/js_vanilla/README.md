This example is from CodiumAI’s cover-agent [repository](https://github.com/Codium-ai/cover-agent/tree/main/templated_tests/js_vanilla). The unit tests were generated using CodiumAI’s cover agent, and Mutahunter was used to verify the effectiveness of the test suite.

## Running Mutahunter to analyze the tests

```bash
mutahunter run --test-command "npm run test:coverage" --test-file-path "ui.test.js" --code-coverage-report-path "coverage/coverage.xml" --only-mutate-file-paths "ui.js"
```
