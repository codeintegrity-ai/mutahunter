package com.example;

import java.util.ArrayList;
import java.util.List;

public class BankAccount {

    private double balance;
    private double overdraftLimit;
    private List<String> transactionHistory;

    public BankAccount(double initialBalance, double overdraftLimit) {
        if (initialBalance < 0) {
            throw new IllegalArgumentException("Initial balance must be non-negative");
        }
        this.balance = initialBalance;
        this.overdraftLimit = overdraftLimit;
        this.transactionHistory = new ArrayList<>();
        transactionHistory.add("Account created with balance: " + initialBalance);
    }

    public double getBalance() {
        return balance;
    }

    public List<String> getTransactionHistory() {
        return transactionHistory;
    }

    public void deposit(double amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("Deposit amount must be positive");
        }
        balance += amount;
        transactionHistory.add("Deposited: " + amount);
    }

    public void withdraw(double amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("Withdrawal amount must be positive");
        }
        if (amount > balance + overdraftLimit) {
            throw new IllegalArgumentException("Insufficient funds, including overdraft limit");
        }
        balance -= amount;
        transactionHistory.add("Withdrew: " + amount);
    }

    public void applyAnnualInterest(double interestRate) {
        if (interestRate <= 0) {
            throw new IllegalArgumentException("Interest rate must be positive");
        }
        double interest = balance * (interestRate / 100);
        balance += interest;
        transactionHistory.add("Interest applied: " + interest);
    }

    public void executeBatchTransactions(double[] deposits, double[] withdrawals) {
        for (double deposit : deposits) {
            deposit(deposit);
        }
        for (double withdrawal : withdrawals) {
            withdraw(withdrawal);
        }
        transactionHistory.add("Batch transactions executed");
    }

    public void scheduleTransaction(String type, double amount, int daysFromNow) {
        if (daysFromNow < 0) {
            throw new IllegalArgumentException("Days from now must be non-negative");
        }
        // This is a simplification; in a real system, you would have a scheduler.
        // We'll just log the scheduled transaction for demonstration purposes.
        transactionHistory.add("Scheduled " + type + " of " + amount + " in " + daysFromNow + " days");
    }
}
