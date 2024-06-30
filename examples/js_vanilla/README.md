This example is from CodiumAI’s cover-agent [repository](https://github.com/Codium-ai/cover-agent/tree/main/templated_tests/js_vanilla). The unit tests were generated using CodiumAI’s cover agent, and Mutahunter was used to verify the effectiveness of the test suite.

Coverage report was already generated. Now, we will run Mutahunter to analyze the tests.

## Running Mutahunter to analyze the tests

```bash
mutahunter run --test-command "npm run test" --test-file-path "ui.test.js" --code-coverage-report-path "coverage.xml" --only-mutate-file-paths "ui.js"
```
