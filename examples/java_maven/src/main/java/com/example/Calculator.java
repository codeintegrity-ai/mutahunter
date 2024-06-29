package com.example;

public class Calculator {

    // Method to add two numbers
    public double add(double a, double b) {
        return a + b;
    }

    // Method to subtract one number from another
    public double subtract(double a, double b) {
        return a - b;
    }

    // Method to multiply two numbers
    public double multiply(double a, double b) {
        return a * b;
    }

    // Method to divide one number by another
    public double divide(double a, double b) {
        if (b == 0) {
            throw new IllegalArgumentException("Division by zero is not allowed.");
        }
        return a / b;
    }

    public static void main(String[] args) {
        Calculator calculator = new Calculator();

        // Sample usage
        double num1 = 10;
        double num2 = 5;

        System.out.println("Addition: " + calculator.add(num1, num2));
        System.out.println("Subtraction: " + calculator.subtract(num1, num2));
        System.out.println("Multiplication: " + calculator.multiply(num1, num2));
        System.out.println("Division: " + calculator.divide(num1, num2));
    }
}