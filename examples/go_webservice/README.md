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

mutahunter gen-line --test-command "go test -coverprofile=coverage.out" --code-coverage-report-path "coverage.xml" --coverage-type cobertura --test-file-path "app_test.go" --source-file-path "app.go" --model "gpt-4o" --target-line-coverage 0.9 --max-attempts 3

gocov convert coverage.out | gocov-xml > coverage.xml # as there is no easy way to get direct coverage report from go test
```

Check `logs/_latest/html` for mutation report.
