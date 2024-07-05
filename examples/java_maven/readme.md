# Java Maven Example

## Generate test coverage report

```bash
mvn test
```

## Running Mutahunter to analyze the tests

Coverage report was already generated. Now, we will run Mutahunter to analyze the tests.

```bash
export OPENAI_API_KEY=your-key-goes-here
mutahunter run --test-command "mvn test" --code-coverage-report-path "target/site/jacoco/jacoco.xml" --coverage-type jacoco
```
