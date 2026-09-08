import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from users.exceptions import UserAlreadyExistsError
from users.services import create_user, authenticate_user, InvalidCredentialsError

User = get_user_model()


@pytest.mark.django_db
def test_create_user_success():
    username = "testuser"
    password = "secret_password123"

    # 1. Вызов сервиса
    user = create_user(username=username, password=password)

    assert user.pk is not None

    # Читаем пользователя напрямую из PostgreSQL
    db_user = User.objects.get(username=username)
    assert db_user.username == username
    assert db_user.password != password
    assert db_user.check_password(password) is True

@pytest.mark.django_db
def test_create_user_duplicate_username_fails():
    # 1. Создаем первого пользователя
    create_user(username="unique_login", password="password123")

    # 2. Пытаемся создать второго с таким же username
    with pytest.raises(UserAlreadyExistsError):
        create_user(username="unique_login", password="another_password")

@pytest.mark.django_db
def test_login_user_success():
    user = create_user(username="unique_login", password="password123")
    authenticated_user = authenticate_user(username="unique_login", password="password123")

    assert authenticated_user == user

@pytest.mark.django_db
def test_login_user_wrong_data_fails():
    create_user(username="unique_login", password="password123")

    with pytest.raises(InvalidCredentialsError):
        authenticate_user(username="unique_login", password="qwerty123")