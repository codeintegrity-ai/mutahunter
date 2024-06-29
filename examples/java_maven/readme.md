## Running Mutahunter to analyze the tests

```bash
mutahunter run --test-command "mvn test -DtestSourceDirectory=src/test/java/CalculatorTest.java" --test-file-path "src/test/java/CalculatorTest.java" --code-coverage-report-path "target/site/jacoco/jacoco.xml" --only-mutate-file-paths "src/test/java/CalculatorTest.java" --coverage-type jacoco
```
