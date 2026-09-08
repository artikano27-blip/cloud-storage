import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status

from users.services import create_user

@pytest.mark.django_db
def test_register_successful_returns_201(api_client,user_credentials):
    response1 = api_client.post(reverse("sign-up"), user_credentials, format="json")

    user = User.objects.get(username=user_credentials["username"])

    assert response1.data == {"username": user.username}
    assert "sessionid"  in api_client.cookies
    assert response1.status_code == status.HTTP_201_CREATED

@pytest.mark.django_db
def test_register_duplicate_username_returns_409(api_client,user_credentials):
    # 1. Первый запрос на регистрацию (успешный)
    response1 = api_client.post(reverse("sign-up"), user_credentials, format="json")
    assert response1.status_code == status.HTTP_201_CREATED

    # 2. Второй запрос с теми же данными
    response2 = api_client.post(reverse("sign-up"), user_credentials, format="json")
    assert response2.status_code == status.HTTP_409_CONFLICT
    assert response2.data["message"] == "Пользователь с таким логином уже существует."

@pytest.mark.django_db
def test_login_successful_returns_200(api_client,created_user,user_credentials):
    response1 = api_client.post(reverse("sign-in"), user_credentials, format="json")
    assert response1.data == {"username": created_user.username}
    assert "sessionid" in api_client.cookies
    assert api_client.session["_auth_user_id"] == str(created_user.id)
    assert response1.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_login_wrong_password_returns_401(api_client,created_user):
    payload = {"username": created_user.username,"password": "test_pass123"}
    response1 = api_client.post(reverse("sign-in"), payload, format="json")
    assert response1.status_code == status.HTTP_401_UNAUTHORIZED
    assert "sessionid" not in api_client.cookies
    assert response1.data["message"] == "Неверные данные (такого пользователя нет, или пароль неправильный)"

@pytest.mark.django_db
def test_logout_not_authenticate_returns_401(api_client):
    response1 = api_client.post(reverse("logout"), format="json")
    assert response1.status_code == status.HTTP_401_UNAUTHORIZED
    assert response1.data["message"] == "Authentication credentials were not provided."

@pytest.mark.django_db
def test_successful_logout_returns_204(api_client,created_user):
    api_client.force_login(created_user)
    response1 = api_client.post(reverse("logout"), format = "json")
    assert response1.status_code == status.HTTP_204_NO_CONTENT
    assert "_auth_user_id" not in api_client.session
