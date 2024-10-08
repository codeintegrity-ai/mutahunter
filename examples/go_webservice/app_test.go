package main

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"time"

	"github.com/stretchr/testify/assert"
)

func TestRootEndpoint(t *testing.T) {
	router := SetupRouter() // Use the SetupRouter from app.go

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Body.String(), "Welcome to the Go Gin application!")
}

func TestIsPalindromeEndpoint(t *testing.T) {
	router := SetupRouter()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/is-palindrome/radar", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.JSONEq(t, `{"is_palindrome": true}`, w.Body.String())
}

func TestDivideByZeroEndpoint(t *testing.T) {
	router := SetupRouter()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/divide/4/0", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusBadRequest, w.Code)
	assert.JSONEq(t, `{"error": "Cannot divide by zero"}`, w.Body.String())
}

func TestAddEndpoint(t *testing.T) {
	router := SetupRouter()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/add/3/4", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.JSONEq(t, `{"result": 7}`, w.Body.String())
}

func TestCurrentDateEndpoint(t *testing.T) {
	router := SetupRouter()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/current-date", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Body.String(), time.Now().Format("2006-01-02"))
}

func TestSubtractEndpoint(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/subtract/5/4", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, `{"result": 1}`, w.Body.String())
}

func TestSubtractEndpointWithNegativeResult(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/subtract/3/4", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, `{"result": -1}`, w.Body.String())
}

func TestMultiplyEndpoint(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/multiply/3/4", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, `{"result": 12}`, w.Body.String())
}

func TestMultiplyEndpointWithZero(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/multiply/3/0", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, `{"result": 0}`, w.Body.String())
}

func TestDivideEndpoint(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/divide/4/2", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, `{"result": 2}`, w.Body.String())
}

func TestSquareEndpoint(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/square/4", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, `{"result": 16}`, w.Body.String())
}

func TestSqrtEndpoint(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/sqrt/4", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, `{"result": 2}`, w.Body.String())
}

func TestSqrtEndpointWithNegativeNumber(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/sqrt/-4", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusBadRequest, w.Code)
    assert.JSONEq(t, `{"error": "Cannot take square root of a negative number"}`, w.Body.String())
}

func TestDaysUntilNewYearEndpoint(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/days-until-new-year", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.Contains(t, w.Body.String(), `"days_until_new_year"`)
}

func TestEchoEndpoint(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/echo/Hello, World!", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, `{"message": "Hello, World!"}`, w.Body.String())
}

func TestSubtractEndpointWithZero(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/subtract/5/0", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, `{"result": 5}`, w.Body.String())
}

func TestMultiplyEndpointWithNegativeNumbers(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/multiply/-3/4", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, `{"result": -12}`, w.Body.String())
}

func TestDivideEndpointWithNegativeNumbers(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/divide/-4/2", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, `{"result": -2}`, w.Body.String())
}

func TestSquareEndpointWithNegativeNumber(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/square/-4", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, `{"result": 16}`, w.Body.String())
}

func TestSqrtEndpointWithZero(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/sqrt/0", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, `{"result": 0}`, w.Body.String())
}

func TestSubtractEndpointWithLargeNumbers(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/subtract/2000000000/1000000000", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, `{"result": 1000000000}`, w.Body.String())
}

func TestMultiplyEndpointWithLargeNumbers(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/multiply/1000000/1000000", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, `{"result": 1000000000000}`, w.Body.String())
}

func TestDivideEndpointWithLargeNumbers(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/divide/1000000000/1000", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, `{"result": 1000000}`, w.Body.String())
}

func TestSquareEndpointWithLargeNumber(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/square/1000000", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, `{"result": 1000000000000}`, w.Body.String())
}

func TestSqrtEndpointWithLargeNumber(t *testing.T) {
    router := SetupRouter()

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/sqrt/1000000000000", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.JSONEq(t, `{"result": 1000000}`, w.Body.String())
}
