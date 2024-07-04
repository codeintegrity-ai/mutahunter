import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import com.example.Calculator;

public class CalculatorTest {

    private Calculator calculator;

    @BeforeEach
    public void setUp() {
        calculator = new Calculator();
    }

    @Test
    public void testAdd() {
        assertEquals(15.0, calculator.add(10, 5));
        assertEquals(0.0, calculator.add(-5, 5));
        assertEquals(-15.0, calculator.add(-10, -5));
    }

    @Test
    public void testSubtract() {
        assertEquals(5.0, calculator.subtract(10, 5));
        assertEquals(-10.0, calculator.subtract(-5, 5));
        assertEquals(-5.0, calculator.subtract(-10, -5));
    }

    @Test
    public void testMultiply() {
        assertEquals(50.0, calculator.multiply(10, 5));
        assertEquals(-25.0, calculator.multiply(-5, 5));
        assertEquals(50.0, calculator.multiply(-10, -5));
    }

    @Test
    public void testDivide() {
        assertEquals(2.0, calculator.divide(10, 5));
        assertEquals(-1.0, calculator.divide(-5, 5));
        assertEquals(2.0, calculator.divide(-10, -5));
    }
}