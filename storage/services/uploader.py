from botocore.exceptions import ClientError
from django.core.files.uploadedfile import UploadedFile

from storage.dto import StorageItem
from storage.exceptions import (
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
)
from storage.services.base import BaseS3Service
from storage.services.decorators import handle_s3_errors
from storage.utils import (
    _get_s3_key,
    build_s3_key,
    get_relative_path,
    make_parent_dir,
)



class S3UploadService(BaseS3Service):

    def _upload_single_file(
        self, user_id: int, path: str, file: UploadedFile
    ) -> StorageItem:
        # Передаем file.name, а не весь объект
        s3_key = _get_s3_key(user_id, path, file.name)
        file.seek(0)

        try:
            # Атомарная запись с блокировкой гонки
            self.client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=file.read(),
                ContentType=file.content_type
                or "application/octet-stream",
                IfNoneMatch="*",
            )
        except ClientError as e:
            if self._is_precondition_failed(e):
                raise ResourceAlreadyExistsError(
                    detail={
                        "message": "Файл/папка с таким именем уже существует в целевой папке!"
                    }
                )
            raise e

        relative_path = get_relative_path(s3_key, user_id)
        parent_dir, file_name = make_parent_dir(relative_path)
        return StorageItem(
            path=parent_dir,
            name=file_name,
            size=file.size,
            type="FILE",
        )

    @handle_s3_errors
    def upload_resource(
            self, user_id: int, path: str, files: list[UploadedFile]
    ) -> list[StorageItem]:
        # Валидируем целевую папку перед началом загрузки
        if path:
            parent_folder_key = build_s3_key(user_id, path, is_dir=True)
            if not self._folder_exists(parent_folder_key):
                raise ResourceNotFoundError(
                    detail={"message": "Целевая папка не найдена"}
                )

        upload_data = []
        for file in files:
            # Атомарно загружаем каждый файл
            item = self._upload_single_file(user_id, path, file)
            upload_data.append(item)

        return upload_data

    @handle_s3_errors
    def create_null_folder(self, user_id: int, path: str) -> StorageItem:
        normal_path = build_s3_key(user_id, path, is_dir=True)
        relative_path = get_relative_path(normal_path, user_id)
        parent_dir, file_name = make_parent_dir(relative_path)

        if parent_dir:
            parent_s3_key = build_s3_key(user_id, parent_dir, is_dir=True)
            if not self._folder_exists(parent_s3_key):
                raise ResourceNotFoundError(
                    detail={"message": "Родительская папка не найдена"}
                )

        if self._folder_exists(normal_path):
            raise ResourceAlreadyExistsError(
                detail={"message": "Ресурс по указанному пути уже существует"}
            )

        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=normal_path,
                Body=b"",
                IfNoneMatch="*",
            )
        except ClientError as e:
            if self._is_precondition_failed(e):
                raise ResourceAlreadyExistsError(
                    detail={
                        "message": "Ресурс по указанному пути уже существует"
                    }
                )
            raise e

        return StorageItem(
            path=parent_dir,
            name=file_name,
            size=None,
            type="DIRECTORY",
        )