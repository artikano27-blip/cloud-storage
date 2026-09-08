from botocore.exceptions import ClientError

from storage.dto import StorageItem
from storage.exceptions import ResourceNotFoundError
from storage.services.base import BaseS3Service
from storage.services.decorators import handle_s3_errors
from storage.utils import build_s3_key, get_relative_path, make_parent_dir


class S3DirectoryService(BaseS3Service):

    @handle_s3_errors
    def get_resource_info(self, user_id: int, path: str):
        is_dir = not path or path.endswith("/")
        normal_path = build_s3_key(user_id, path, is_dir=is_dir)

        if is_dir:
            if path and not self._folder_exists(normal_path):
                raise ResourceNotFoundError
            relative_path = get_relative_path(normal_path, user_id)
            parent_dir, file_name = make_parent_dir(relative_path)
            return StorageItem(
                path=parent_dir,
                name=file_name,
                size=None,
                type="DIRECTORY",
            )

        try:
            response = self.client.head_object(
                Bucket=self.bucket, Key=normal_path
            )
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
                raise ResourceNotFoundError
            raise e

        relative_path = get_relative_path(normal_path, user_id)
        parent_dir, file_name = make_parent_dir(relative_path)
        return StorageItem(
            path=parent_dir,
            name=file_name,
            size=response.get("ContentLength"),
            type="FILE",
        )


    @handle_s3_errors
    def get_folder_resources(self, user_id: int, path: str):
        normal_path = build_s3_key(user_id, path, is_dir=True)
        response = self.client.list_objects_v2(
            Bucket=self.bucket, Prefix=normal_path, Delimiter="/"
        )

        if response.get("KeyCount", 0) == 0 and path:
            raise ResourceNotFoundError

        storage = []
        for file in response.get("Contents", []):
            if file["Key"] == normal_path or file["Key"].endswith("/"):
                continue
            rel_path = get_relative_path(file["Key"], user_id)
            p_dir, f_name = make_parent_dir(rel_path)
            storage.append(
                StorageItem(
                    path=p_dir,
                    name=f_name,
                    size=file.get("Size"),
                    type="FILE",
                )
            )

        for prefix in response.get("CommonPrefixes", []):
            rel_path = get_relative_path(prefix["Prefix"], user_id)
            p_dir, f_name = make_parent_dir(rel_path)
            storage.append(
                StorageItem(
                    path=p_dir,
                    name=f_name,
                    size=None,
                    type="DIRECTORY",
                )
            )

        return storage