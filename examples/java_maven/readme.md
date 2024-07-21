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

### Surviving Mutant Analysis

[Mutants](./mutants.json)
[Report](./mutant_analysis.md)