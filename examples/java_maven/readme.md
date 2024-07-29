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

### Generate unit tests to increase line and mutation coverage

```bash
# remove some tests
mutahunter gen --test-command "mvn test" --code-coverage-report-path "target/site/jacoco/jacoco.xml" --coverage-type jacoco --test-file-path "src/test/java/BankAccountTest.java" --source-file-path "src/main/java/com/example/BankAccount.java" --model "gpt-4o"
```

Check `logs/_latest/html` for mutation report.
