from datetime import date
from datetime import date
import pytest
from fastapi.testclient import TestClient

from ..app import app

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


def test_current_date():
    response = client.get("/current-date")
    assert response.status_code == 200
    assert response.json() == {"date": date.today().isoformat()}


def test_add():
    num1, num2 = 3, 5
    response = client.get(f"/add/{num1}/{num2}")
    assert response.status_code == 200
    assert response.json() == {"result": num1 + num2}


def test_subtract():
    num1, num2 = 10, 4
    response = client.get(f"/subtract/{num1}/{num2}")
    assert response.status_code == 200
    assert response.json() == {"result": num1 - num2}


def test_multiply():
    num1, num2 = 6, 7
    response = client.get(f"/multiply/{num1}/{num2}")
    assert response.status_code == 200
    assert response.json() == {"result": num1 * num2}


def test_divide():
    num1, num2 = 8, 2
    response = client.get(f"/divide/{num1}/{num2}")
    assert response.status_code == 200
    assert response.json() == {"result": num1 / num2}


def test_divide_by_zero():
    num1, num2 = 8, 0
    response = client.get(f"/divide/{num1}/{num2}")
    assert response.status_code == 400
    assert response.json() == {"detail": "Cannot divide by zero"}


def test_square():
    number = 4
    response = client.get(f"/square/{number}")
    assert response.status_code == 200
    assert response.json() == {"result": number**2}


def test_sqrt_negative():
    number = -4.0
    response = client.get(f"/sqrt/{number}")
    assert response.status_code == 400
    assert response.json() == {"detail": "Cannot take square root of a negative number"}


def test_is_palindrome():
    text = "madam"
    response = client.get(f"/is-palindrome/{text}")
    assert response.status_code == 200
    assert response.json() == {"is_palindrome": True}


def test_is_not_palindrome():
    text = "hello"
    response = client.get(f"/is-palindrome/{text}")
    assert response.status_code == 200
    assert response.json() == {"is_palindrome": False}


def test_days_until_new_year():
    today = date.today()
    next_new_year = date(today.year + 1, 1, 1)
    delta = next_new_year - today
    response = client.get("/days-until-new-year")
    assert response.status_code == 200
    assert response.json() == {"days_until_new_year": delta.days}
