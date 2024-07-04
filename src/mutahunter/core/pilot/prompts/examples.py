"""
This module contains example output templates for different 
programming languages supported by MutaHunter.
"""

GO_UDIFF = """
Example Output:
```diff
--- /Users/taikorind/Documents/personal/codeintegrity/mutahunter/example/go/app.go
+++ /Users/taikorind/Documents/personal/codeintegrity/mutahunter/example/go/app.go
@@ ... @@
 func reverse(s string) string {
        runes := []rune(s)
-       for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
+       for i, j := 0, len(runes)-1; i <= j; i, j = i+1, j-1 { // Mutation: Changed the condition from i < j to i <= j to simulate off-by-one error.
                runes[i], runes[j] = runes[j], runes[i]
        }
        return string(runes)
}
```
"""

JAVASCRIPT_UDIFF = """
Example Output:
```diff
--- /Users/taikorind/Documents/personal/codeintegrity/mutahunter/example/javascript/showAlert.js
+++ /Users/taikorind/Documents/personal/codeintegrity/mutahunter/example/javascript/showAlert.js
@@ ... @@
 showAlert(message, className) {
     this.clearAlert();
     const div = document.createElement('div');
     div.className = className;
-    div.appendChild(document.createTextNode(message));
+    div.innerHTML = message;  // Mutation: Using innerHTML instead of createTextNode to simulate XSS vulnerability.
     const container = document.querySelector('.searchContainer');
     const search = document.querySelector('.search');
     container.insertBefore(div, search);

     setTimeout(() => {
       this.clearAlert();
     }, 2000);
 }
```
"""

PYTHON_UDIFF = """
Example Output:
```diff
--- /Users/taikorind/Documents/personal/codeintegrity/mutahunter/example/calculator/simple_calculator.py
+++ /Users/taikorind/Documents/personal/codeintegrity/mutahunter/example/calculator/simple_calculator.py
@@ ... @@
 def add(self, a, b):
         \"\"\"Return the sum of a and b.\"\"\"
-        return a + b
+        return float(a) + float(b) # Mutation: Convert inputs to floats to simulate floating-point precision error.
```
"""

JAVA_UDIFF = """
Example Output:
```diff
--- /Users/taikorind/Documents/personal/codeintegrity/mutahunter/example/calculator/simple_calculator.py
+++ /Users/taikorind/Documents/personal/codeintegrity/mutahunter/example/calculator/simple_calculator.py
@@ ... @@
    public double divide(double a, double b) {
        if (b == 0) {
            throw new IllegalArgumentException("Division by zero is not allowed.");
        }
-        return a / b;        
+        return a * b; // Mutation: Changed division to multiplication using AOR (Arithmetic Operator Replacement)
    }
```
"""
