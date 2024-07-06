import org.junit.jupiter.api.Test;

import com.example.BankAccount;

import static org.junit.jupiter.api.Assertions.*;

class BankAccountTest {

        @Test
        void testInitialBalance() {
                BankAccount account = new BankAccount(1000, 500);
                assertEquals(1000, account.getBalance());
        }

        @Test
        void testInitialBalanceNegative() {
                Exception exception = assertThrows(IllegalArgumentException.class, () -> {
                        new BankAccount(-1000, 500);
                });
                assertEquals("Initial balance must be non-negative", exception.getMessage());
        }

        @Test
        void testDeposit() {
                BankAccount account = new BankAccount(1000, 500);
                account.deposit(500);
                assertEquals(1500, account.getBalance());
        }

        @Test
        void testWithdraw() {
                BankAccount account = new BankAccount(1000, 500);
                account.withdraw(500);
                assertEquals(500, account.getBalance());
        }

        @Test
        void testApplyAnnualInterest() {
                BankAccount account = new BankAccount(1000, 500);
                account.applyAnnualInterest(5);
                assertEquals(1050, account.getBalance());
        }

        @Test
        void testExecuteBatchTransactions() {
                BankAccount account = new BankAccount(1000, 500);
                double[] deposits = { 100, 200 };
                double[] withdrawals = { 50, 150 };
                account.executeBatchTransactions(deposits, withdrawals);
                assertEquals(1100, account.getBalance());
        }

        @Test
        void testScheduleTransaction() {
                BankAccount account = new BankAccount(1000, 500);
                account.scheduleTransaction("Deposit", 500, 5);
                assertTrue(account.getTransactionHistory().contains("Scheduled Deposit of 500.0 in 5 days"));
        }

        @Test
        void testScheduleTransactionNegativeDays() {
                BankAccount account = new BankAccount(1000, 500);
                Exception exception = assertThrows(IllegalArgumentException.class, () -> {
                        account.scheduleTransaction("Deposit", 500, -5);
                });
                assertEquals("Days from now must be non-negative", exception.getMessage());
        }

        @Test
        void testDepositNegativeAmount() {
                BankAccount account = new BankAccount(1000, 500);
                Exception exception = assertThrows(IllegalArgumentException.class, () -> {
                        account.deposit(-500);
                });
                assertEquals("Deposit amount must be positive", exception.getMessage());
        }

        @Test
        void testWithdrawNegativeAmount() {
                BankAccount account = new BankAccount(1000, 500);
                Exception exception = assertThrows(IllegalArgumentException.class, () -> {
                        account.withdraw(-500);
                });
                assertEquals("Withdrawal amount must be positive", exception.getMessage());
        }

        @Test
        void testWithdrawExceedingBalance() {
                BankAccount account = new BankAccount(1000, 500);
                Exception exception = assertThrows(IllegalArgumentException.class, () -> {
                        account.withdraw(1600);
                });
                assertEquals("Insufficient funds, including overdraft limit", exception.getMessage());
        }

        @Test
        void testApplyZeroInterestRate() {
                BankAccount account = new BankAccount(1000, 500);
                Exception exception = assertThrows(IllegalArgumentException.class, () -> {
                        account.applyAnnualInterest(0);
                });
                assertEquals("Interest rate must be positive", exception.getMessage());
        }

}
