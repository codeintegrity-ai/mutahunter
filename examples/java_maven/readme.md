# Java Maven Example

## Generate test coverage report

```bash
mvn test
```

## Running MutaHunter to Analyze Tests

### Initial Test Coverage

Currently test coverage is 100%. But how good is the test suite? Let's find out.

### Extreme Mutation Testing

Run the mutation testing in extreme mode (without using LLM-based models).

```bash
  mutahunter run --test-command "mvn test" --code-coverage-report-path "target/site/jacoco/jacoco.xml" --coverage-type jacoco --extreme
```

```bash
2024-07-05 23:14:10,691 INFO: 📊 Line Coverage: 100.00% 📊
2024-07-05 23:14:10,691 INFO: 🎯 Mutation Coverage: 100.00% 🎯
2024-07-05 23:14:10,691 INFO: 🦠 Total Mutants: 6 🦠
2024-07-05 23:14:10,692 INFO: 🛡️ Survived Mutants: 0 🛡️
2024-07-05 23:14:10,692 INFO: 🗡️ Killed Mutants: 6 🗡️
2024-07-05 23:14:10,692 INFO: 🕒 Timeout Mutants: 0 🕒
2024-07-05 23:14:10,692 INFO: 🔥 Compile Error Mutants: 0 🔥
2024-07-05 23:14:10,692 INFO: 💰 Expected Cost: \$0.00000 USD 💰
2024-07-05 23:14:10,693 INFO: Report saved to logs/_latest/mutation_coverage.json
2024-07-05 23:14:10,693 INFO: Report saved to logs/_latest/mutation_coverage_detail.json
2024-07-05 23:14:10,693 INFO: Mutation Testing Ended. Took 19s
```

Nice 100% mutation coverage! 🎉. Let try using LLM

### LLM-based Mutation Testing

```bash
export OPENAI_API_KEY=your-key-goes-here
mutahunter run --test-command "mvn test" --code-coverage-report-path "target/site/jacoco/jacoco.xml" --coverage-type jacoco --model "gpt-4o"
```

```bash
2024-07-05 23:15:52,418 INFO: 📊 Line Coverage: 100.00% 📊
2024-07-05 23:15:52,418 INFO: 🎯 Mutation Coverage: 42.11% 🎯
2024-07-05 23:15:52,418 INFO: 🦠 Total Mutants: 21 🦠
2024-07-05 23:15:52,419 INFO: 🛡️ Survived Mutants: 11 🛡️
2024-07-05 23:15:52,419 INFO: 🗡️ Killed Mutants: 8 🗡️
2024-07-05 23:15:52,419 INFO: 🕒 Timeout Mutants: 0 🕒
2024-07-05 23:15:52,419 INFO: 🔥 Compile Error Mutants: 2 🔥
2024-07-05 23:15:52,419 INFO: 💰 Expected Cost: \$0.06956 USD 💰
2024-07-05 23:15:52,420 INFO: Report saved to logs/_latest/mutation_coverage.json
2024-07-05 23:15:52,420 INFO: Report saved to logs/_latest/mutation_coverage_detail.json
2024-07-05 23:15:52,420 INFO: Mutation Testing Ended. Took 87s
```

### Survived Mutant: Add check for negative balance

```json
  {
    "id": "1",
    "source_path": "src/main/java/com/example/BankAccount.java",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/examples/java_maven/logs/_latest/mutants/1_BankAccount.java",
    "status": "SURVIVED",
    "error_msg": "",
    "mutant_code": "public double getBalance() {\n        if (balance < 0) { throw new IllegalStateException(\"Balance is negative\"); } return balance; // Mutation: Added check for negative balance\n    }",
    "type": "Boundary Condition",
    "description": "Added check for negative balance."
  },
```

Should we check for negative balance? 🤔 Maybe. I think it depends. But maybe we can add a new test case something like this.

```java
@Test
void testNegativeBalance() {
    BankAccount account = new BankAccount(-200, 500);

    Exception exception = assertThrows(IllegalStateException.class, () -> {
        account.getBalance();
    });
    assertEquals("Balance is negative", exception.getMessage());
}

```

### Survived Mutant: Test 0 Balance

```json
  {
    "id": "7",
    "source_path": "src/main/java/com/example/BankAccount.java",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/examples/java_maven/logs/_latest/mutants/7_BankAccount.java",
    "status": "SURVIVED",
    "error_msg": "",
    "mutant_code": "public void deposit(double amount) {\n        if (amount < 0) { // Mutation: Changed the condition to allow zero deposit\n            throw new IllegalArgumentException(\"Deposit amount must be positive\");\n        }\n        balance += amount;\n        transactionHistory.add(\"Deposited: \" + amount);\n    }",
    "type": "Boundary Condition",
    "description": "Changed the condition to allow zero deposit."
  },
  {
    "id": "10",
    "source_path": "src/main/java/com/example/BankAccount.java",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/examples/java_maven/logs/_latest/mutants/10_BankAccount.java",
    "status": "SURVIVED",
    "error_msg": "",
    "mutant_code": "public void withdraw(double amount) {\n        if (amount < 0) { // Mutation: Changed condition to allow zero withdrawal\n            throw new IllegalArgumentException(\"Withdrawal amount must be positive\");\n        }\n        if (amount > balance + overdraftLimit) {\n            throw new IllegalArgumentException(\"Insufficient funds, including overdraft limit\");\n        }\n        balance -= amount;\n        transactionHistory.add(\"Withdrew: \" + amount);\n    }",
    "type": "Boundary Condition",
    "description": "Changed condition to allow zero withdrawal."
  }
```

The above mutant suggests that it allows zero deposit. But how can that be? Didn't we have 100% test coverage? 🤔. If you look at the test suite you can see that it tests for
`testWithdrawNegativeAmount` but not for `testWithdrawZeroAmount`. Let's add that test.

```java

        @Test
        void testWithdrawZeroAmount() {
                BankAccount account = new BankAccount(1000, 500);
                Exception exception = assertThrows(IllegalArgumentException.class, () -> {
                        account.withdraw(0);
                });
                assertEquals("Withdrawal amount must be positive", exception.getMessage());
        }
```

### Survived Mutant: Added check for null deposits array

```json
  {
    "id": "16",
    "source_path": "src/main/java/com/example/BankAccount.java",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/examples/java_maven/logs/_latest/mutants/16_BankAccount.java",
    "status": "SURVIVED",
    "error_msg": "",
    "mutant_code": "public void executeBatchTransactions(double[] deposits, double[] withdrawals) {\n        if (deposits == null) { throw new IllegalArgumentException(\"Deposits array must not be null\"); } for (double deposit : deposits) { // Mutation: Added check for null deposits array\n            deposit(deposit);\n        }\n        for (double withdrawal : withdrawals) {\n            withdraw(withdrawal);\n        }\n        transactionHistory.add(\"Batch transactions executed\");\n    }",
    "type": "Boundary Condition",
    "description": "Added check for null deposits array."
  },
 {
    "id": "17",
    "source_path": "src/main/java/com/example/BankAccount.java",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/examples/java_maven/logs/_latest/mutants/17_BankAccount.java",
    "status": "SURVIVED",
    "error_msg": "",
    "mutant_code": "public void executeBatchTransactions(double[] deposits, double[] withdrawals) {\n        for (double deposit : deposits) {\n            deposit(deposit);\n        }\n        if (withdrawals == null) { throw new IllegalArgumentException(\"Withdrawals array must not be null\"); } for (double withdrawal : withdrawals) { // Mutation: Added check for null withdrawals array\n            withdraw(withdrawal);\n        }\n        transactionHistory.add(\"Batch transactions executed\");\n    }",
    "type": "Boundary Condition",
    "description": "Added check for null withdrawals array."
  },
 {
    "id": "18",
    "source_path": "src/main/java/com/example/BankAccount.java",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/examples/java_maven/logs/_latest/mutants/18_BankAccount.java",
    "status": "SURVIVED",
    "error_msg": "",
    "mutant_code": "public void executeBatchTransactions(double[] deposits, double[] withdrawals) {\n        for (double deposit : deposits) {\n            deposit(deposit);\n        }\n        for (double withdrawal : withdrawals) {\n            withdraw(withdrawal);\n        }\n        if (deposits.length == 0 && withdrawals.length == 0) { throw new IllegalArgumentException(\"At least one transaction must be executed\"); } transactionHistory.add(\"Batch transactions executed\"); // Mutation: Added check to ensure at least one transaction is executed\n    }",
    "type": "Logical Branch",
    "description": "Added check to ensure at least one transaction is executed."
  },
```

It looks like we need to check for null deposits array or else `transactionHistory.add("Batch transactions executed");` will be executed.

```java
public void executeBatchTransactions(double[] deposits, double[] withdrawals) {
    if (deposits == null) { 
        throw new IllegalArgumentException("Deposits array must not be null"); 
    } 
    for (double deposit : deposits) { 
        deposit(deposit); 
    } 
    for (double withdrawal : withdrawals) { 
        withdraw(withdrawal); 
    } 
    transactionHistory.add("Batch transactions executed");
}
```

Here is the full survived mutants list for reference:

```json
[
  {
    "id": "1",
    "source_path": "src/main/java/com/example/BankAccount.java",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/examples/java_maven/logs/_latest/mutants/1_BankAccount.java",
    "status": "SURVIVED",
    "error_msg": "",
    "mutant_code": "public double getBalance() {\n        if (balance < 0) { throw new IllegalStateException(\"Balance is negative\"); } return balance; // Mutation: Added check for negative balance\n    }",
    "type": "Boundary Condition",
    "description": "Added check for negative balance."
  },
  {
    "id": "2",
    "source_path": "src/main/java/com/example/BankAccount.java",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/examples/java_maven/logs/_latest/mutants/2_BankAccount.java",
    "status": "SURVIVED",
    "error_msg": "",
    "mutant_code": "public double getBalance() {\n        System.out.println(\"Retrieving balance: \" + balance); return balance; // Mutation: Added logging for balance retrieval\n    }",
    "type": "Logical Branch",
    "description": "Added logging for balance retrieval."
  },
  {
    "id": "3",
    "source_path": "src/main/java/com/example/BankAccount.java",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/examples/java_maven/logs/_latest/mutants/3_BankAccount.java",
    "status": "SURVIVED",
    "error_msg": "",
    "mutant_code": "public double getBalance() {\n        if (balance == 0) { throw new IllegalStateException(\"Balance is zero\"); } return balance; // Mutation: Added check for zero balance\n    }",
    "type": "Boundary Condition",
    "description": "Added check for zero balance."
  },
  {
    "id": "4",
    "source_path": "src/main/java/com/example/BankAccount.java",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/examples/java_maven/logs/_latest/mutants/4_BankAccount.java",
    "status": "SURVIVED",
    "error_msg": "",
    "mutant_code": "public List<String> getTransactionHistory() {\n        return new ArrayList<>(transactionHistory); // Mutation: Return a copy of the transaction history instead of the original list\n    }",
    "type": "Return Value Modification",
    "description": "Return a copy of the transaction history instead of the original list."
  },
  {
    "id": "5",
    "source_path": "src/main/java/com/example/BankAccount.java",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/examples/java_maven/logs/_latest/mutants/5_BankAccount.java",
    "status": "SURVIVED",
    "error_msg": "",
    "mutant_code": "public List<String> getTransactionHistory() {\n        if (transactionHistory == null) { return new ArrayList<>(); } return transactionHistory; // Mutation: Added null check for transactionHistory before returning\n    }",
    "type": "Null Check Addition",
    "description": "Added null check for transactionHistory before returning."
  },
  {
    "id": "7",
    "source_path": "src/main/java/com/example/BankAccount.java",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/examples/java_maven/logs/_latest/mutants/7_BankAccount.java",
    "status": "SURVIVED",
    "error_msg": "",
    "mutant_code": "public void deposit(double amount) {\n        if (amount < 0) { // Mutation: Changed the condition to allow zero deposit\n            throw new IllegalArgumentException(\"Deposit amount must be positive\");\n        }\n        balance += amount;\n        transactionHistory.add(\"Deposited: \" + amount);\n    }",
    "type": "Boundary Condition",
    "description": "Changed the condition to allow zero deposit."
  },
  {
    "id": "10",
    "source_path": "src/main/java/com/example/BankAccount.java",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/examples/java_maven/logs/_latest/mutants/10_BankAccount.java",
    "status": "SURVIVED",
    "error_msg": "",
    "mutant_code": "public void withdraw(double amount) {\n        if (amount < 0) { // Mutation: Changed condition to allow zero withdrawal\n            throw new IllegalArgumentException(\"Withdrawal amount must be positive\");\n        }\n        if (amount > balance + overdraftLimit) {\n            throw new IllegalArgumentException(\"Insufficient funds, including overdraft limit\");\n        }\n        balance -= amount;\n        transactionHistory.add(\"Withdrew: \" + amount);\n    }",
    "type": "Boundary Condition",
    "description": "Changed condition to allow zero withdrawal."
  },
  {
    "id": "16",
    "source_path": "src/main/java/com/example/BankAccount.java",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/examples/java_maven/logs/_latest/mutants/16_BankAccount.java",
    "status": "SURVIVED",
    "error_msg": "",
    "mutant_code": "public void executeBatchTransactions(double[] deposits, double[] withdrawals) {\n        if (deposits == null) { throw new IllegalArgumentException(\"Deposits array must not be null\"); } for (double deposit : deposits) { // Mutation: Added check for null deposits array\n            deposit(deposit);\n        }\n        for (double withdrawal : withdrawals) {\n            withdraw(withdrawal);\n        }\n        transactionHistory.add(\"Batch transactions executed\");\n    }",
    "type": "Boundary Condition",
    "description": "Added check for null deposits array."
  },
  {
    "id": "17",
    "source_path": "src/main/java/com/example/BankAccount.java",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/examples/java_maven/logs/_latest/mutants/17_BankAccount.java",
    "status": "SURVIVED",
    "error_msg": "",
    "mutant_code": "public void executeBatchTransactions(double[] deposits, double[] withdrawals) {\n        for (double deposit : deposits) {\n            deposit(deposit);\n        }\n        if (withdrawals == null) { throw new IllegalArgumentException(\"Withdrawals array must not be null\"); } for (double withdrawal : withdrawals) { // Mutation: Added check for null withdrawals array\n            withdraw(withdrawal);\n        }\n        transactionHistory.add(\"Batch transactions executed\");\n    }",
    "type": "Boundary Condition",
    "description": "Added check for null withdrawals array."
  },
  {
    "id": "18",
    "source_path": "src/main/java/com/example/BankAccount.java",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/examples/java_maven/logs/_latest/mutants/18_BankAccount.java",
    "status": "SURVIVED",
    "error_msg": "",
    "mutant_code": "public void executeBatchTransactions(double[] deposits, double[] withdrawals) {\n        for (double deposit : deposits) {\n            deposit(deposit);\n        }\n        for (double withdrawal : withdrawals) {\n            withdraw(withdrawal);\n        }\n        if (deposits.length == 0 && withdrawals.length == 0) { throw new IllegalArgumentException(\"At least one transaction must be executed\"); } transactionHistory.add(\"Batch transactions executed\"); // Mutation: Added check to ensure at least one transaction is executed\n    }",
    "type": "Logical Branch",
    "description": "Added check to ensure at least one transaction is executed."
  },
  {
    "id": "19",
    "source_path": "src/main/java/com/example/BankAccount.java",
    "mutant_path": "/Users/taikorind/Documents/personal/codeintegrity/mutahunter/examples/java_maven/logs/_latest/mutants/19_BankAccount.java",
    "status": "SURVIVED",
    "error_msg": "",
    "mutant_code": "public void scheduleTransaction(String type, double amount, int daysFromNow) {\n        if (daysFromNow < 0) {\n            if (daysFromNow < -1) { throw new IllegalArgumentException(\"Days from now must be non-negative\"); } // Mutation: Changed condition to allow scheduling transactions for today\n        }\n        // This is a simplification; in a real system, you would have a scheduler.\n        // We'll just log the scheduled transaction for demonstration purposes.\n        transactionHistory.add(\"Scheduled \" + type + \" of \" + amount + \" in \" + daysFromNow + \" days\");\n    }",
    "type": "Boundary Condition",
    "description": "Changed condition to allow scheduling transactions for today."
  }
]```
