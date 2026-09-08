# conftest.py
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from testcontainers.community.postgres import PostgresContainer
from django.conf import settings
from django.db import connections
from rest_framework.test import APIClient
from testcontainers.core.container import DockerContainer

from storage.services.base import get_s3_client
from storage.utils import build_s3_key
from users.services import create_user


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker):
    print("\n--- ЗАПУСК TESTCONTAINERS ---")
    with PostgresContainer("postgres:16-alpine") as postgres:
        # 1. Обновляем существующий словарь in-place
        settings.DATABASES["default"].update({
            "ENGINE": "django.db.backends.postgresql",
            "NAME": postgres.dbname,
            "USER": postgres.username,
            "PASSWORD": postgres.password,
            "HOST": postgres.get_container_host_ip(),
            "PORT": postgres.get_exposed_port(5432),
        })

        # 2. Сбрасываем кэш активных соединений
        connections.close_all()

        # 3. Применяем миграции к базе внутри контейнера
        with django_db_blocker.unblock():
            from django.core.management import call_command
            call_command("migrate")
            yield

@pytest.fixture(scope="session", autouse=True)
def s3_setup():
    print("\n--- ЗАПУСК TESTCONTAINERS ---")
    with (DockerContainer("minio/minio:latest")
            .with_env("MINIO_ROOT_USER", "minioadmin")
            .with_env("MINIO_ROOT_PASSWORD", "minioadmin")
            .with_exposed_ports(9000)
            .with_command("server /data")
    ) as minio:

        host = minio.get_container_host_ip()
        port = minio.get_exposed_port(9000)

        settings.AWS_S3_ENDPOINT_URL = f"http://{host}:{port}"
        settings.AWS_ACCESS_KEY_ID = "minioadmin"
        settings.AWS_SECRET_ACCESS_KEY = "minioadmin"
        settings.AWS_STORAGE_BUCKET_NAME = "user-files"

        s3 = get_s3_client()
        s3.create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        yield


@pytest.fixture(autouse=True)
def clean_s3_bucket(s3_client):
    # До теста ничего делать не нужно
    yield

    # После завершения теста получаем список всех объектов в бакете 📦
    response = s3_client.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME)

    if "Contents" in response:
        # Формируем список ключей для массового удаления
        objects_to_delete = [{"Key": obj["Key"]} for obj in response["Contents"]]

        # Удаляем все найденные объекты за один вызов ⚡
        s3_client.delete_objects(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Delete={"Objects": objects_to_delete},
        )

# conftest.py или прямо в файле тестов
@pytest.fixture
def user_credentials():
    return {"username": "testuser", "password": "secure_password123"}

@pytest.fixture
def created_user(user_credentials):
    return create_user( **user_credentials)

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_s3_file(created_user,s3_client):
    def _create(filename: str = "123.png", content: bytes = b"test content"):
        normal_path = build_s3_key(created_user.id, filename)
        s3_client.put_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=normal_path,
            Body=content,
        )
        return filename, normal_path

    return _create

@pytest.fixture
def create_uploaded_file():
    def _factory(name: str, content: bytes = b"default_content", content_type: str = "text/plain"):
        return SimpleUploadedFile(name=name, content=content, content_type=content_type)
    return _factory

@pytest.fixture
def s3_client():
    return get_s3_client()

@pytest.fixture
def authenticated_client(api_client, created_user):
    api_client.force_authenticate(user=created_user)
    return api_client

@pytest.fixture
def bucket_name():
    return settings.AWS_STORAGE_BUCKET_NAME