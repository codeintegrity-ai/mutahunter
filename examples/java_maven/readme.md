# Java Maven Example

## Generate test coverage report

```bash
mvn test -DtestSourceDirectory=src/test/java/CalculatorTest.java
```

## Running Mutahunter to analyze the tests

Coverage report was already generated. Now, we will run Mutahunter to analyze the tests.

```bash
mutahunter run --test-command "mvn test -DtestSourceDirectory=src/test/java/CalculatorTest.java" --test-file-path "src/test/java/CalculatorTest.java" --code-coverage-report-path "target/site/jacoco/jacoco.xml" --only-mutate-file-paths "src/main/java/com/example/Calculator.java" --coverage-type jacoco
```
