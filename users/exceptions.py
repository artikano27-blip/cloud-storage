from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.permissions import BasePermission
from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # Логика преобразования структуры ответа
        if "detail" in response.data:
            msg = response.data.get("detail")
            response.data = {"message":msg}

    return response

class IsAuthenticatedCustom(BasePermission):
    # DRF автоматически использует это поле при формировании ответа об ошибке
    message = {"message": "Запрос исполняется неавторизованным юзером"}

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

class InvalidCredentialsError(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = {"message": "Неверные данные (такого пользователя нет, или пароль неправильный)"}

class AuthServiceError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    def __init__(self, message="Ошибка при обращении к сервису авторизации"):
        super().__init__(detail={"message": message})

class UserAlreadyExistsError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = {"message": "Пользователь с таким логином уже существует."}