from django.contrib.auth import get_user_model, authenticate
from django.db import IntegrityError

from users.exceptions import InvalidCredentialsError, AuthServiceError, UserAlreadyExistsError

User = get_user_model()

def create_user(username: str, password: str):
    try:
        return User.objects.create_user(username=username, password=password)
    except IntegrityError:
        raise UserAlreadyExistsError()
    except Exception as e:
        raise AuthServiceError() from e

def authenticate_user(username, password):
   try:
        user = authenticate(username=username, password=password)

   except Exception:
       raise AuthServiceError()

   if user is None:
       raise InvalidCredentialsError()
   return user



