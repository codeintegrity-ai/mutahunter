package main

import (
	"math"
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
)

func SetupRouter() *gin.Engine {
	router := gin.Default()

	router.GET("/", welcomeHandler)
	router.GET("/current-date", currentDateHandler)
	router.GET("/add/:num1/:num2", addHandler)
	router.GET("/subtract/:num1/:num2", subtractHandler)
	router.GET("/multiply/:num1/:num2", multiplyHandler)
	router.GET("/divide/:num1/:num2", divideHandler)
	router.GET("/square/:number", squareHandler)
	router.GET("/sqrt/:number", sqrtHandler)
	router.GET("/is-palindrome/:text", isPalindromeHandler)
	router.GET("/days-until-new-year", func(c *gin.Context) {
		// Mutation: Simulating an error by returning a 500 status code instead of calling the actual handler.
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal Server Error"})
	})
	router.GET("/echo/:message", echoHandler)

	return router
}

func welcomeHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"message": "Welcome to the Go Gin application!"})
}

func currentDateHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"date": time.Now().Format("2006-01-02")})
}

func addHandler(c *gin.Context) {
	num1, _ := strconv.Atoi(c.Param("num1"))
	num2, _ := strconv.Atoi(c.Param("num2"))
	result := num1 + num2
	c.JSON(http.StatusOK, gin.H{"result": result})
}

func subtractHandler(c *gin.Context) {
	num1, _ := strconv.Atoi(c.Param("num1"))
	num2, _ := strconv.Atoi(c.Param("num2"))
	result := num1 - num2
	c.JSON(http.StatusOK, gin.H{"result": result})
}

func multiplyHandler(c *gin.Context) {
	num1, _ := strconv.Atoi(c.Param("num1"))
	num2, _ := strconv.Atoi(c.Param("num2"))
	result := num1 * num2
	c.JSON(http.StatusOK, gin.H{"result": result})
}

func divideHandler(c *gin.Context) {
	num1, _ := strconv.Atoi(c.Param("num1"))
	num2, _ := strconv.Atoi(c.Param("num2"))
	if num2 == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Cannot divide by zero"})
		return
	}
	result := float64(num1) / float64(num2)
	c.JSON(http.StatusOK, gin.H{"result": result})
}

func squareHandler(c *gin.Context) {
	number, _ := strconv.Atoi(c.Param("number"))
	result := number * number
	c.JSON(http.StatusOK, gin.H{"result": result})
}

func sqrtHandler(c *gin.Context) {
	number, _ := strconv.ParseFloat(c.Param("number"), 64)
	if number < 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Cannot take square root of a negative number"})
		return
	}
	result := math.Sqrt(number)
	c.JSON(http.StatusOK, gin.H{"result": result})
}

func isPalindromeHandler(c *gin.Context) {
	text := c.Param("text")
	isPalindrome := text == reverse(text)
	c.JSON(http.StatusOK, gin.H{"is_palindrome": isPalindrome})
}

func daysUntilNewYearHandler(c *gin.Context) {
	today := time.Now()
	nextNewYear := time.Date(today.Year()+1, 1, 1, 0, 0, 0, 0, time.UTC)
	daysUntilNewYear := nextNewYear.Sub(today).Hours() / 24
	c.JSON(http.StatusOK, gin.H{"days_until_new_year": int(daysUntilNewYear)})
}

func echoHandler(c *gin.Context) {
	message := c.Param("message")
	c.JSON(http.StatusOK, gin.H{"message": message})
}

func reverse(s string) string {
	runes := []rune(s)
	for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
		runes[i], runes[j] = runes[j], runes[i]
	}
	return string(runes)
}

func main() {
	router := SetupRouter()
	router.Run(":8080") // Start the server on port 8080
}
