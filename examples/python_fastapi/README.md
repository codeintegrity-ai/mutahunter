# Python FastAPI Example

This example is from CodiumAI’s cover-agent [repository](https://github.com/Codium-ai/cover-agent/tree/main/templated_tests/python_fastapi). The unit tests were generated using CodiumAI’s cover agent, and Mutahunter was used to verify the effectiveness of the test suite.

## First generate test coverage report

```bash
pip install -r requirements.txt
pytest --cov=. --cov-report=xml --cov-report=term
```

## Running Mutahunter to analyze the tests

```bash
export OPENAI_API_KEY=your-key-goes-here
mutahunter run --test-command "pytest" --code-coverage-report-path "coverage.xml" --only-mutate-file-paths "app.py" --model "gpt-4o-mini"
```

### Surviving Mutant Analysis

[Mutants](./mutants.json)
[Report](./mutant_analysis.md)