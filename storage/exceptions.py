
from rest_framework import status
from rest_framework.exceptions import APIException


class ResourceNotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = {"message": "Ресурс не найден"}

class InvalidPathError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {"message": "Невалидный или отсутствующий путь"}

class FileNotExistsError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {"message": "Не удалось найти файл"}

class ValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {"message":"Имя файла не может быть пустым"}


class StorageServiceError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    def __init__(self, message="Ошибка при обращении к сервису хранилища"):
        super().__init__(detail={"message": message})

class ResourceAlreadyExistsError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = {"message": "Ресурс по указанному пути уже существует"}