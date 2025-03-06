## How to run

```bash
export OPENAI_API_KEY=your-key-goes-here
mutahunter run --test-command "mvn clean test" --model "gpt-4o-mini" --source-path "src/main/java/com/example/BankAccount.java" --test-path "src/test/java/BankAccountTest.java"
```
