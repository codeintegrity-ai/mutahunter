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
# --extreme flag is used to run the mutation testing in extreme mode. This does not use the LLM-based model.
mutahunter run --test-command "go test" --code-coverage-report-path "coverage.xml" --only-mutate-file-paths "app.go" --extreme

# After achieving a high mutation score, let's say 90%, you can check one last time using LLM-based

# go seems to do pretty bad when using gpt-3.5-turbo, so we recommend using gpt-4o

export OPENAI_API_KEY=your-key-goes-here

mutahunter run --test-command "go test" --code-coverage-report-path "coverage.xml" --only-mutate-file-paths "app.go" --model "gpt-4o"

## you can use --modifies-files-only to only mutate the files that are modified by the test suite
mutahunter run --test-command "go test" --code-coverage-report-path "coverage.xml" --only-mutate-file-paths "app.go" --extreme --modifies-files-only

## and then keeping improving the test suite until you get 100%
```
