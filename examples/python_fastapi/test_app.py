import pytest
from app import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_root():
    """
    Test the root endpoint by sending a GET request to "/" and checking the response status code and JSON body.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the FastAPI application!"}


def test_echo():
    response = client.get("/echo/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "hello"}


def test_days_until_new_year():
    response = client.get("/days-until-new-year")
    assert response.status_code == 200
    assert "days_until_new_year" in response.json()


def test_is_palindrome():
    response = client.get("/is-palindrome/radar")
    assert response.status_code == 200
    assert response.json() == {"is_palindrome": True}


def test_sqrt_negative():
    response = client.get("/sqrt/-1")
    assert response.status_code == 400
    assert response.json() == {"detail": "Cannot take square root of a negative number"}


def test_square():
    response = client.get("/square/5")
    assert response.status_code == 200
    assert response.json() == {"result": 25}


def test_divide_by_zero():
    response = client.get("/divide/8/0")
    assert response.status_code == 400
    assert response.json() == {"detail": "Cannot divide by zero"}


def test_divide():
    response = client.get("/divide/8/2")
    assert response.status_code == 200
    assert response.json() == {"result": 4.0}


def test_multiply():
    response = client.get("/multiply/3/4")
    assert response.status_code == 200
    assert response.json() == {"result": 12}


def test_subtract():
    response = client.get("/subtract/10/4")
    assert response.status_code == 200
    assert response.json() == {"result": 6}


def test_add():
    response = client.get("/add/3/4")
    assert response.status_code == 200
    assert response.json() == {"result": 7}


def test_current_date():
    response = client.get("/current-date")
    assert response.status_code == 200
    assert "date" in response.json()
