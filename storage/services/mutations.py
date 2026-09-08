from storage.dto import StorageItem
from storage.exceptions import (
    InvalidPathError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
)
from storage.services.base import BaseS3Service
from storage.services.decorators import handle_s3_errors
from storage.utils import build_s3_key, get_relative_path, make_parent_dir
from storage.validators import is_valid_path

class S3MutationService(BaseS3Service):

    def _move_file(
        self, source_key: str, target_key: str, user_id: int
    ) -> StorageItem:
        if not self._file_exists(source_key):
            raise ResourceNotFoundError

        if self._file_exists(target_key):
            raise ResourceAlreadyExistsError

        head = self.client.head_object(Bucket=self.bucket, Key=source_key)

        self.client.copy_object(
            Bucket=self.bucket,
            CopySource={"Bucket": self.bucket, "Key": source_key},
            Key=target_key,
        )
        self.client.delete_object(Bucket=self.bucket, Key=source_key)

        relative_path = get_relative_path(target_key, user_id)
        parent_dir, file_name = make_parent_dir(relative_path)
        return StorageItem(
            path=parent_dir,
            name=file_name,
            size=head.get("ContentLength"),
            type="FILE",
        )

    def _move_directory(
        self, source_key: str, target_key: str, user_id: int
    ) -> StorageItem:
        if not source_key.endswith("/"):
            source_key = f"{source_key}/"
        if not target_key.endswith("/"):
            target_key = f"{target_key}/"

        source_files = []
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=source_key):
            source_files.extend(page.get("Contents", []))

        if not source_files:
            raise ResourceNotFoundError

        if self._folder_exists(target_key):
            raise ResourceAlreadyExistsError

        for file in source_files:
            old_key = file.get("Key")
            new_key = f"{target_key}{old_key.removeprefix(source_key)}"
            self.client.copy_object(
                Bucket=self.bucket,
                CopySource={"Bucket": self.bucket, "Key": old_key},
                Key=new_key,
            )

        self._delete_objects_batch(source_files)

        relative_path = get_relative_path(target_key, user_id)
        parent_dir, file_name = make_parent_dir(relative_path)
        return StorageItem(
            path=parent_dir,
            name=file_name,
            size=None,
            type="DIRECTORY",
        )

    @handle_s3_errors
    def delete_resource(self, user_id: int, path: str):
        is_dir = path.endswith("/")
        normal_path = build_s3_key(user_id, path, is_dir=is_dir)

        if is_dir:
            files = []
            paginator = self.client.get_paginator("list_objects_v2")
            for page in paginator.paginate(
                    Bucket=self.bucket, Prefix=normal_path
            ):
                files.extend(page.get("Contents", []))
            if not files:
                raise ResourceNotFoundError
            self._delete_objects_batch(files)
        else:
            if not self._file_exists(normal_path):
                raise ResourceNotFoundError
            self.client.delete_object(Bucket=self.bucket, Key=normal_path)

    @handle_s3_errors
    def move_resource(
            self, user_id: int, source_key: str, target_key: str
    ) -> StorageItem:
        if not (is_valid_path(source_key) and is_valid_path(target_key)):
            raise InvalidPathError

        ready_source_key = build_s3_key(user_id, source_key)
        ready_target_key = build_s3_key(user_id, target_key)

        is_dir = source_key.endswith("/") or target_key.endswith("/")
        if is_dir:
            return self._move_directory(
                ready_source_key, ready_target_key, user_id
            )
        return self._move_file(ready_source_key, ready_target_key, user_id)
