GO_UDIFF = """
Example Output:
```diff
--- /Users/taikorind/Documents/personal/codeintegrity/mutahunter/example/go/router.go
+++ /Users/taikorind/Documents/personal/codeintegrity/mutahunter/example/go/router.go
@@ ... @@
 router.GET("/subtract/:num1/:num2", func(c *gin.Context) {
     num1, _ := strconv.Atoi(c.Param("num1"))
     num2, _ := strconv.Atoi(c.Param("num2"))
     result := num1 - num2
-    if num1 > 1000000 || num2 > 1000000 {
-        c.JSON(http.StatusBadRequest, gin.H{"error": "Input value too large"})
-        return
-    }
+    // Mutation: Removing validation for large input values to simulate Integer Overflow vulnerability.
     c.JSON(http.StatusOK, gin.H{"result": result})
 })
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
